from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import connection
from django.test import override_settings

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import PlatformUser, PlatformUserStatus
from apps.api_clients.models import APIClient
from apps.audit.models import AuditEvent
from apps.audit.services import verify_audit_chain
from apps.organizations.models import Organization
from apps.tenants.models import Tenant
from apps.verification_policies.models import VerificationPolicy
from apps.verifications.models import Verification, VerificationStatus
from apps.verification_subjects.models import VerificationSubject


class AuditEventTests(APITestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name="Acme", slug="acme")
        self.tenant = Tenant.objects.create(
            organization=self.organization,
            name="Acme Tenant",
            slug="acme-tenant",
            status="active",
        )
        self.user = PlatformUser.objects.create_user(
            email="owner@example.com",
            password="StrongPassword123!",
            status=PlatformUserStatus.ACTIVE,
            tenant=self.tenant,
        )
        self.api_client_obj = APIClient(
            tenant=self.tenant,
            created_by=self.user,
            name="Backend",
            scopes_json=["verifications:create", "verifications:read"],
        )
        self.raw_secret = "client-secret"
        self.api_client_obj.set_client_secret(self.raw_secret)
        self.api_client_obj.save()
        self.policy = VerificationPolicy.objects.create(
            tenant=self.tenant,
            name="Default Verification",
            version=1,
            status="active",
            required_document_types_json=["national_id"],
            required_liveness_level="passive",
            face_match_threshold="0.8500",
            manual_review_threshold="0.6500",
            verification_expiry_minutes=1440,
            media_retention_days=30,
            metadata_retention_days=365,
            created_by=self.user,
        )

    def api_client_headers(self):
        return {
            "HTTP_X_CLIENT_ID": self.api_client_obj.client_id,
            "HTTP_IDEMPOTENCY_KEY": "audit-verification-created",
            "HTTP_AUTHORIZATION": f"Bearer {self.raw_secret}",
        }

    def test_login_creates_audit_event(self):
        response = self.client.post(
            reverse("auth-login"),
            {"email": self.user.email, "password": "StrongPassword123!"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            AuditEvent.objects.filter(
                tenant=self.tenant,
                action="user.login",
                target_type="platform_user",
                target_id=self.user.public_id,
            ).exists()
        )

    def test_verification_created_creates_audit_event(self):
        response = self.client.post(
            reverse("verification-list-create"),
            {
                "external_reference": "customer_12345",
                "purpose": "Customer onboarding verification",
                "policy_id": self.policy.public_id,
                "verification_subject": {"full_name": "Kwame Mensah"},
            },
            format="json",
            **self.api_client_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        verification_id = response.data["data"]["id"]
        self.assertTrue(
            AuditEvent.objects.filter(
                tenant=self.tenant,
                action="verification.created",
                target_type="verification",
                target_id=verification_id,
            ).exists()
        )

    def test_manual_decision_creates_audit_event(self):
        from apps.access_control.test_helpers import grant_review_permission

        grant_review_permission(self.user)
        verification = Verification.objects.create(
            tenant=self.tenant,
            organization=self.organization,
            verification_subject=VerificationSubject.objects.create(
                tenant=self.tenant,
                full_name="Reviewer Case",
            ),
            purpose="Manual review case",
            expires_at=timezone.now() + timedelta(hours=1),
            status=VerificationStatus.MANUAL_REVIEW_REQUIRED,
        )
        self.client.force_authenticate(self.user)

        response = self.client.post(
            reverse(
                "manual-review-decision",
                kwargs={"verification_id": verification.public_id},
            ),
            {
                "decision": "verified",
                "reason_code": "evidence_confirmed",
                "reason_detail": "Document and selfie match after manual review.",
            },
            format="json",
            HTTP_IDEMPOTENCY_KEY="audit-manual-decision",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            AuditEvent.objects.filter(
                tenant=self.tenant,
                action="verification.verified",
                target_type="verification",
                target_id=verification.public_id,
            ).exists()
        )

    def test_audit_event_list_is_tenant_scoped(self):
        AuditEvent.objects.create(
            tenant=self.tenant,
            actor_type="platform_user",
            actor_id=self.user.public_id,
            action="user.login",
            target_type="platform_user",
            target_id=self.user.public_id,
        )
        other_org = Organization.objects.create(name="Beta", slug="beta")
        other_tenant = Tenant.objects.create(
            organization=other_org,
            name="Beta Tenant",
            slug="beta-tenant",
            status="active",
        )
        other_user = PlatformUser.objects.create_user(
            email="other@example.com",
            password="StrongPassword123!",
            status=PlatformUserStatus.ACTIVE,
            tenant=other_tenant,
        )
        AuditEvent.objects.create(
            tenant=other_tenant,
            actor_type="platform_user",
            actor_id=other_user.public_id,
            action="user.login",
            target_type="platform_user",
            target_id=other_user.public_id,
        )

        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("audit-event-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["data"]["results"]), 1)

    def test_audit_events_form_a_tamper_evident_chain(self):
        first = AuditEvent.objects.create(
            tenant=self.tenant,
            actor_type="system",
            action="test.first",
            target_type="test",
            target_id="one",
        )
        second = AuditEvent.objects.create(
            tenant=self.tenant,
            actor_type="system",
            action="test.second",
            target_type="test",
            target_id="two",
        )

        self.assertEqual(second.previous_event_hash, first.integrity_hash)
        self.assertEqual(verify_audit_chain(tenant_id=self.tenant.pk), (True, ""))
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE audit_auditevent SET action = %s WHERE id = %s",
                ["tampered", first.pk],
            )
        self.assertEqual(verify_audit_chain(tenant_id=self.tenant.pk)[0], False)

    def test_audit_events_cannot_be_updated_or_deleted(self):
        event = AuditEvent.objects.create(
            tenant=self.tenant,
            actor_type="system",
            action="test.immutable",
            target_type="test",
            target_id="one",
        )
        with self.assertRaises(Exception):
            event.delete()

    def create_event(self, **kwargs):
        return AuditEvent.objects.create(
            tenant=self.tenant,
            actor_type="system",
            action="test.integrity",
            target_type="test",
            target_id="one",
            **kwargs,
        )

    def test_queryset_and_admin_mutations_are_blocked(self):
        from django.contrib.admin.sites import AdminSite
        from apps.audit.admin import AuditEventAdmin

        event = self.create_event()
        for operation in (
            lambda: AuditEvent.objects.filter(pk=event.pk).delete(),
            lambda: AuditEvent.objects.filter(pk=event.pk).update(action="changed"),
            lambda: AuditEvent._base_manager.filter(pk=event.pk).delete(),
            lambda: AuditEvent.objects.bulk_update([event], ["action"]),
            lambda: AuditEvent.objects.bulk_create([AuditEvent(tenant=self.tenant)]),
        ):
            with self.assertRaises(ValidationError):
                operation()
        model_admin = AuditEventAdmin(AuditEvent, AdminSite())
        self.assertFalse(model_admin.has_add_permission(None))
        self.assertFalse(model_admin.has_change_permission(None, event))
        self.assertFalse(model_admin.has_delete_permission(None, event))
        self.assertNotIn(
            "delete_selected",
            model_admin.get_actions(type("Request", (), {"GET": {}})()),
        )

    def test_creation_time_is_assigned_and_ipv6_round_trips(self):
        before = timezone.now()
        event = self.create_event(
            created_at=before - timedelta(days=365),
            ip_address="2001:0db8:0000:0000:0000:0000:0000:0001",
        )
        event.refresh_from_db()
        self.assertGreaterEqual(event.created_at, before)
        self.assertEqual(event.ip_address, "2001:db8::1")
        self.assertEqual(verify_audit_chain(tenant_id=self.tenant.pk), (True, ""))

    def test_public_id_tampering_is_detected(self):
        event = self.create_event()
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE audit_auditevent SET public_id = %s WHERE id = %s",
                ["aud_forged", event.pk],
            )
        self.assertEqual(
            verify_audit_chain(tenant_id=self.tenant.pk), (False, "aud_forged")
        )

    def test_recomputed_unkeyed_hash_and_version_downgrade_fail(self):
        from apps.audit.integrity import event_hash

        event = self.create_event()
        for version in (2, 1):
            event.action = "forged"
            event.integrity_version = version
            forged_hash = event_hash(event)
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE audit_auditevent SET action = %s, integrity_version = %s, integrity_hash = %s WHERE id = %s",
                    [event.action, version, forged_hash, event.pk],
                )
            self.assertEqual(
                verify_audit_chain(tenant_id=self.tenant.pk), (False, event.public_id)
            )

    def test_rotated_keys_verify_retained_history_and_missing_keys_fail_closed(self):
        import base64

        old = "old:" + base64.urlsafe_b64encode(b"a" * 32).decode()
        new = "new:" + base64.urlsafe_b64encode(b"b" * 32).decode()
        with override_settings(
            APPLICATION_ENCRYPTION_KEYRING=old,
            APPLICATION_ENCRYPTION_ACTIVE_KEY_ID="old",
        ):
            first = self.create_event()
        with override_settings(
            APPLICATION_ENCRYPTION_KEYRING=new + "," + old,
            APPLICATION_ENCRYPTION_ACTIVE_KEY_ID="new",
        ):
            second = self.create_event()
            self.assertEqual(second.previous_event_hash, first.integrity_hash)
            self.assertEqual(verify_audit_chain(tenant_id=self.tenant.pk), (True, ""))
        with override_settings(
            APPLICATION_ENCRYPTION_KEYRING=new,
            APPLICATION_ENCRYPTION_ACTIVE_KEY_ID="new",
        ):
            self.assertEqual(
                verify_audit_chain(tenant_id=self.tenant.pk), (False, first.public_id)
            )

    def test_legacy_backfill_preserves_hashes_and_authenticates_public_id(self):
        import importlib
        from types import SimpleNamespace
        from apps.audit.integrity import event_hash

        event = self.create_event()
        event.integrity_version = 1
        legacy_hash = event_hash(event)
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE audit_auditevent SET integrity_version = 1, integrity_hash = %s, authentication_tag = '', integrity_key_id = '' WHERE id = %s",
                [legacy_hash, event.pk],
            )

        class HistoricalQuerySet(type(AuditEvent.objects.all())):
            def update(self, **kwargs):
                from django.db.models import QuerySet

                return QuerySet.update(self, **kwargs)

        historical = SimpleNamespace(
            objects=HistoricalQuerySet(model=AuditEvent, using=connection.alias)
        )
        migration = importlib.import_module(
            "apps.audit.migrations.0004_alter_auditevent_options_and_more"
        )
        migration.authenticate_existing_events(
            SimpleNamespace(get_model=lambda *args: historical),
            SimpleNamespace(connection=connection),
        )
        event.refresh_from_db()
        self.assertEqual(event.integrity_hash, legacy_hash)
        self.assertEqual(verify_audit_chain(tenant_id=self.tenant.pk), (True, ""))
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE audit_auditevent SET public_id = %s WHERE id = %s",
                ["aud_legacy_forged", event.pk],
            )
        self.assertEqual(
            verify_audit_chain(tenant_id=self.tenant.pk), (False, "aud_legacy_forged")
        )

    def test_legacy_authentication_refuses_corrupted_history(self):
        import importlib
        from types import SimpleNamespace

        event = self.create_event()
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE audit_auditevent SET action = %s WHERE id = %s",
                ["tampered", event.pk],
            )
        migration = importlib.import_module(
            "apps.audit.migrations.0004_alter_auditevent_options_and_more"
        )
        with self.assertRaisesRegex(RuntimeError, "Audit chain preflight failed"):
            migration.authenticate_existing_events(
                SimpleNamespace(get_model=lambda *args: AuditEvent),
                SimpleNamespace(connection=connection),
            )

    def test_non_ascii_hashes_and_tags_fail_verification_without_crashing(self):
        event = self.create_event()
        for field in ("integrity_hash", "authentication_tag"):
            with self.subTest(field=field):
                original = getattr(event, field)
                with connection.cursor() as cursor:
                    cursor.execute(
                        f"UPDATE audit_auditevent SET {field} = %s WHERE id = %s",
                        ["é" * 64, event.pk],
                    )
                self.assertEqual(
                    verify_audit_chain(tenant_id=self.tenant.pk),
                    (False, event.public_id),
                )
                with connection.cursor() as cursor:
                    cursor.execute(
                        f"UPDATE audit_auditevent SET {field} = %s WHERE id = %s",
                        [original, event.pk],
                    )
