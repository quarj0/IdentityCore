from datetime import timedelta
from unittest.mock import patch

from django.core import mail
from django.db import connection
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.accounts.models import PlatformUser, TeamInvitation
from apps.access_control.models import Permission, Role, RolePermission, UserRole
from apps.notifications.models import Notification
from apps.notifications.serializers import serialize_notification
from apps.notifications.services import deliver_notification
from apps.organizations.models import Organization
from apps.tenants.models import Tenant


@override_settings(
    TEAM_INVITATION_BASE_URL="https://dashboard.example.test/accept-invitation",
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
)
class InvitationLifecycleTests(APITestCase):
    password = "StrongPassword123!"
    url = "/api/v1/auth/team/invitations"

    def setUp(self):
        organization = Organization.objects.create(
            name="Invitations", slug="invitation-tests"
        )
        self.tenant = Tenant.objects.create(
            organization=organization,
            name="Invitations",
            slug="invitation-tests",
            status="active",
        )
        self.actor = PlatformUser.objects.create_user(
            email="owner@example.test",
            password=self.password,
            tenant=self.tenant,
            status="active",
        )
        self.admin = Role.objects.create(
            tenant=self.tenant, scope="tenant", name="Invitation manager"
        )
        self.role = Role.objects.create(
            tenant=self.tenant, scope="tenant", name="Member"
        )
        permission, _ = Permission.objects.get_or_create(
            code="manage_team", defaults={"name": "Manage team"}
        )
        RolePermission.objects.create(role=self.admin, permission=permission)
        UserRole.objects.create(user=self.actor, tenant=self.tenant, role=self.admin)
        self.client.force_authenticate(self.actor)

    def create(self, email="new@example.test"):
        response = self.client.post(
            self.url, {"email": email, "role_id": self.role.public_id}, format="json"
        )
        self.assertEqual(response.status_code, 201, response.data)
        invitation = TeamInvitation.objects.get(public_id=response.data["data"]["id"])
        notification = Notification.objects.filter(
            template_code="team.invitation"
        ).latest("created_at")
        return invitation, notification.delivery_json["token"], notification

    def accept(self, token, password=None, **extra):
        self.client.force_authenticate(None)
        return self.client.post(
            self.url + "/accept",
            {"token": token, "password": password or self.password, **extra},
            format="json",
        )

    def test_new_user_acceptance_is_single_use_and_sends_safe_encrypted_delivery(self):
        invitation, token, notification = self.create()
        self.assertNotIn(token, str(serialize_notification(notification)))
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT delivery_json FROM notifications_notification WHERE id=%s",
                [notification.pk],
            )
            self.assertNotIn(token, str(cursor.fetchone()[0]))
        deliver_notification(notification)
        self.assertIn("#token=" + token, mail.outbox[0].body)
        response = self.accept(token)
        self.assertEqual(response.status_code, 200, response.data)
        self.assertNotIn("tokens", response.data["data"])
        user = PlatformUser.objects.get(email=invitation.email)
        self.assertTrue(
            UserRole.objects.filter(
                user=user, role=self.role, tenant=self.tenant
            ).exists()
        )
        self.assertEqual(self.accept(token).status_code, 400)

    def test_resend_rotates_and_cancels_old_delivery_and_revoke_invalidates(self):
        invitation, old_token, old_notification = self.create()
        response = self.client.post(self.url + "/" + invitation.public_id + "/resend")
        self.assertEqual(response.status_code, 200)
        invitation.refresh_from_db()
        new_token = Notification.objects.latest("created_at").delivery_json["token"]
        self.assertNotEqual(old_token, new_token)
        deliver_notification(old_notification)
        old_notification.refresh_from_db()
        self.assertEqual(old_notification.status, "cancelled")
        self.assertEqual(self.accept(old_token).status_code, 400)
        self.client.force_authenticate(self.actor)
        self.assertEqual(
            self.client.post(
                self.url + "/" + invitation.public_id + "/revoke"
            ).status_code,
            200,
        )
        self.assertEqual(self.accept(new_token).status_code, 400)

    def test_expired_pending_invitation_does_not_block_replacement(self):
        invitation, token, _ = self.create()
        TeamInvitation.objects.filter(pk=invitation.pk).update(
            expires_at=timezone.now() - timedelta(seconds=1)
        )
        self.assertEqual(self.accept(token).status_code, 400)
        self.client.force_authenticate(self.actor)
        replacement, _, _ = self.create()
        self.assertNotEqual(replacement.pk, invitation.pk)
        invitation.refresh_from_db()
        self.assertEqual(invitation.status, "expired")

    def test_existing_user_requires_password_and_retains_account_and_credentials(self):
        user = PlatformUser.objects.create_user(
            email="existing@example.test",
            password=self.password,
            tenant=self.tenant,
            status="active",
        )
        invitation, token, _ = self.create(user.email)
        self.assertEqual(self.accept(token, "wrong").status_code, 400)
        self.assertEqual(self.accept(token).status_code, 200)
        self.assertEqual(PlatformUser.objects.filter(email=user.email).count(), 1)
        user.refresh_from_db()
        self.assertTrue(user.check_password(self.password))
        self.assertTrue(
            UserRole.objects.filter(user=user, role=invitation.role).exists()
        )

    def test_existing_mfa_user_must_prove_second_factor(self):
        user = PlatformUser.objects.create_user(
            email="mfa@example.test",
            password=self.password,
            tenant=self.tenant,
            status="active",
            mfa_enabled=True,
        )
        _, token, _ = self.create(user.email)
        with patch("apps.accounts.invitations.verify_challenge", return_value=None):
            self.assertEqual(self.accept(token, mfa_code="invalid").status_code, 400)
        with patch("apps.accounts.invitations.verify_challenge", return_value="totp"):
            self.assertEqual(self.accept(token, mfa_code="valid").status_code, 200)

    def test_permissions_email_and_role_are_validated_before_creation(self):
        self.assertEqual(
            self.client.post(
                self.url,
                {"email": "invalid", "role_id": self.role.public_id},
                format="json",
            ).status_code,
            400,
        )
        permission = Permission.objects.create(code="outside_grant", name="Outside")
        RolePermission.objects.create(role=self.role, permission=permission)
        self.assertEqual(
            self.client.post(
                self.url,
                {"email": "valid@example.test", "role_id": self.role.public_id},
                format="json",
            ).status_code,
            403,
        )
        UserRole.objects.filter(user=self.actor).delete()
        self.assertEqual(
            self.client.post(
                self.url,
                {"email": "valid@example.test", "role_id": self.role.public_id},
                format="json",
            ).status_code,
            403,
        )
        self.assertFalse(TeamInvitation.objects.exists())

    def test_foreign_invitation_matches_unknown_without_mutation(self):
        invitation, _, _ = self.create()
        organization = Organization.objects.create(name="Other", slug="other-invite")
        other = Tenant.objects.create(
            organization=organization,
            name="Other",
            slug="other-invite",
            status="active",
        )
        TeamInvitation.objects.filter(pk=invitation.pk).update(tenant=other)
        foreign = self.client.post(self.url + "/" + invitation.public_id + "/revoke")
        unknown = self.client.post(self.url + "/inv_unknown/revoke")
        self.assertEqual(foreign.status_code, 404)
        self.assertEqual(foreign.data["error"], unknown.data["error"])
        invitation.refresh_from_db()
        self.assertEqual(invitation.status, "pending")

    def test_role_or_inviter_disablement_blocks_acceptance(self):
        _, token, _ = self.create()
        Role.objects.filter(pk=self.role.pk).update(status="inactive")
        self.assertEqual(self.accept(token).status_code, 400)
        self.assertFalse(PlatformUser.objects.filter(email="new@example.test").exists())
