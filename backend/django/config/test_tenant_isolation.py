from datetime import timedelta
from uuid import uuid4

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import (
    DashboardSession,
    PlatformUser,
    PlatformUserStatus,
    TeamInvitation,
)
from apps.access_control.models import Permission, Role, RolePermission, UserRole
from apps.api_clients.models import APIClient
from apps.audit.models import AuditEvent
from apps.notifications.models import Notification
from apps.organizations.models import (
    Organization,
    OrganizationStatus,
    OrganizationSupportingDocument,
)
from apps.projects.models import Project
from apps.tenants.models import Tenant, TenantKMSBinding
from apps.billing.models import (
    BillingPlan,
    BillingSubscription,
    BillingInvoice,
    BillingPayment,
)
from apps.consent.test_helpers import accept_test_consent
from apps.verification_subjects.models import VerificationSubject
from apps.webhooks.models import WebhookEndpoint, WebhookEvent
from apps.verification_policies.models import VerificationPolicy
from apps.verifications.models import Verification, ReviewQueue, ReviewQualityAssignment
from apps.providers.models import Provider, ProviderEnvironmentConfiguration
from apps.workflows.models import Workflow


class TenantIsolationMatrixTests(APITestCase):
    """Regression matrix for tenant-owned dashboard REST resources.

    Detail operations deliberately compare a foreign identifier with an unknown
    identifier.  Both must produce the same non-disclosing response, and write
    attempts must leave the foreign object unchanged.
    """

    password = "StrongPassword123!"

    def setUp(self):
        self.user, self.tenant = self._create_workspace("acme")
        self.other_user, self.other_tenant = self._create_workspace("beta")
        role = Role.objects.create(
            tenant=self.tenant, name="Matrix administrator", scope="tenant"
        )
        for code in (
            "manage_team",
            "manage_webhooks",
            "manage_subject_privacy",
            "review_verification",
            "manage_providers",
            "manage_billing",
            "manage_consent",
            "manage_encryption",
        ):
            permission, _ = Permission.objects.get_or_create(
                code=code, defaults={"name": code}
            )
            RolePermission.objects.create(role=role, permission=permission)
        UserRole.objects.create(user=self.user, role=role, tenant=self.tenant)
        login = self.client.post(
            reverse("auth-login"),
            {"email": self.user.email, "password": self.password},
            format="json",
        )
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login.data['data']['tokens']['access']}"
        )

        self.other_project = Project.objects.create(
            tenant=self.other_tenant,
            created_by=self.other_user,
            name="Foreign project",
            slug="foreign-project",
        )
        self.other_workflow = Workflow.objects.create(
            tenant=self.other_tenant,
            project=self.other_project,
            created_by=self.other_user,
            name="Foreign workflow",
        )
        self.other_subject = VerificationSubject.objects.create(
            tenant=self.other_tenant, full_name="Foreign subject"
        )
        self.other_client = APIClient(
            tenant=self.other_tenant,
            created_by=self.other_user,
            name="Foreign client",
        )
        self.other_client.set_client_secret("not-returned")
        self.other_client.save()
        self.other_webhook = WebhookEndpoint.objects.create(
            tenant=self.other_tenant,
            created_by=self.other_user,
            url="https://foreign.example.test/hook",
            secret_hash="not-returned",
        )
        self.other_audit_event = AuditEvent.objects.create(
            tenant=self.other_tenant,
            actor_type="platform_user",
            actor_id=self.other_user.public_id,
            action="foreign.action",
            target_type="project",
            target_id=self.other_project.public_id,
        )
        self.other_notification = Notification.objects.create(
            tenant=self.other_tenant,
            recipient_type="platform_user",
            recipient=self.other_user.email,
            channel="in_app",
            subject="Foreign notification",
        )
        self.other_document = OrganizationSupportingDocument.objects.create(
            organization=self.other_tenant.organization,
            tenant=self.other_tenant,
            uploaded_by=self.other_user,
            filename="foreign.pdf",
            file_size_bytes=128,
            storage_key="organizations/beta/foreign.pdf",
            status="uploaded",
        )

        self.other_policy = VerificationPolicy.objects.create(
            tenant=self.other_tenant, name="Foreign policy"
        )
        self.other_verification = Verification.objects.create(
            tenant=self.other_tenant,
            organization=self.other_tenant.organization,
            verification_subject=self.other_subject,
            purpose="Foreign verification",
            expires_at=timezone.now() + timedelta(hours=1),
        )
        self.other_event = WebhookEvent.objects.create(
            tenant=self.other_tenant,
            webhook_endpoint=self.other_webhook,
            event_type="verification.completed",
            status="failed",
        )
        foreign_role = Role.objects.create(
            tenant=self.other_tenant, name="Foreign role", scope="tenant"
        )
        self.other_invitation = TeamInvitation.objects.create(
            tenant=self.other_tenant,
            role=foreign_role,
            invited_by=self.other_user,
            email="invitee@beta.example.test",
            token_hash="foreign-matrix-invitation",
            expires_at=timezone.now() + timedelta(days=1),
        )
        self.other_session = DashboardSession.objects.create(
            user=self.other_user,
            last_seen_at=timezone.now(),
            expires_at=timezone.now() + timedelta(days=1),
        )
        self.other_queue = ReviewQueue.objects.create(
            tenant=self.other_tenant, name="Foreign queue", environment="sandbox"
        )
        self.other_quality = ReviewQualityAssignment.objects.create(
            tenant=self.other_tenant,
            verification=self.other_verification,
            queue=self.other_queue,
            decision_revision=1,
            sampling_percent=100,
            original_outcome="verified",
            maker=self.other_user,
        )
        self.other_provider = Provider.objects.create(
            tenant=self.other_tenant,
            name="Foreign provider",
            code="matrix-foreign",
            provider_type="document",
        )
        self.other_configuration = ProviderEnvironmentConfiguration.objects.create(
            provider=self.other_provider,
            environment="sandbox",
            version=1,
            public_configuration_json={
                "endpoint_url": "https://foreign.example.test/invoke"
            },
            credentials_json={"api_key": "matrix-only-credential"},
            manifest_snapshot_json={"version": 1},
            requested_by=self.other_user,
        )

        self.other_consent = accept_test_consent(self.other_verification)
        self.other_kms = TenantKMSBinding.objects.create(
            tenant=self.other_tenant,
            environment="sandbox",
            key_arn="arn:aws:kms:us-east-1:111122223333:key/matrix-only",
        )
        plan = BillingPlan.objects.create(code="matrix", name="Matrix plan")
        subscription = BillingSubscription.objects.create(
            tenant=self.other_tenant, plan=plan, started_at=timezone.now()
        )
        self.other_invoice = BillingInvoice.objects.create(
            tenant=self.other_tenant,
            subscription=subscription,
            plan_code=plan.code,
            plan_version=1,
            currency="GHS",
            period_start=timezone.now().date(),
            period_end=(timezone.now() + timedelta(days=30)).date(),
            status="issued",
        )
        self.other_payment = BillingPayment.objects.create(
            invoice=self.other_invoice,
            reference="matrix-only",
            amount_minor=100,
            currency="GHS",
        )

    def _create_workspace(self, slug):
        organization = Organization.objects.create(
            name=slug.title(), slug=slug, status=OrganizationStatus.ACTIVE
        )
        tenant = Tenant.objects.create(
            organization=organization,
            name=f"{slug.title()} tenant",
            slug=f"{slug}-tenant",
            status="active",
        )
        user = PlatformUser.objects.create_user(
            email=f"owner@{slug}.example.test",
            password=self.password,
            status=PlatformUserStatus.ACTIVE,
            tenant=tenant,
        )
        return user, tenant

    def assert_non_disclosing_not_found(
        self, method, foreign_path, missing_path, data=None
    ):
        foreign = getattr(self.client, method)(
            foreign_path, data or {}, format="json", HTTP_IDEMPOTENCY_KEY=uuid4().hex
        )
        missing = getattr(self.client, method)(
            missing_path, data or {}, format="json", HTTP_IDEMPOTENCY_KEY=uuid4().hex
        )
        self.assertEqual(foreign.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(foreign.status_code, missing.status_code)
        self.assertEqual(foreign.data["error"]["code"], "resource_not_found")
        self.assertEqual(
            {key: value for key, value in foreign.data.items() if key != "request_id"},
            {key: value for key, value in missing.data.items() if key != "request_id"},
        )

    def test_cross_tenant_detail_read_matrix_is_non_disclosing(self):
        cases = (
            (
                f"/api/v1/projects/{self.other_project.public_id}",
                "/api/v1/projects/prj_missing",
            ),
            (
                f"/api/v1/workflows/{self.other_workflow.public_id}",
                "/api/v1/workflows/wfl_missing",
            ),
            (
                f"/api/v1/subjects/{self.other_subject.public_id}",
                "/api/v1/subjects/sub_missing",
            ),
            (
                f"/api/v1/api-clients/{self.other_client.public_id}",
                "/api/v1/api-clients/api_missing",
            ),
            (
                f"/api/v1/webhook-endpoints/{self.other_webhook.public_id}",
                "/api/v1/webhook-endpoints/whk_missing",
            ),
            (
                f"/api/v1/audit-events/{self.other_audit_event.public_id}",
                "/api/v1/audit-events/aud_missing",
            ),
            (
                f"/api/v1/notifications/{self.other_notification.public_id}",
                "/api/v1/notifications/ntf_missing",
            ),
        )
        for foreign_path, missing_path in cases:
            with self.subTest(path=foreign_path):
                self.assert_non_disclosing_not_found("get", foreign_path, missing_path)

    def test_cross_tenant_write_matrix_cannot_mutate_resources(self):
        cases = (
            (
                f"/api/v1/projects/{self.other_project.public_id}",
                "/api/v1/projects/prj_missing",
                {"name": "Compromised"},
                self.other_project,
            ),
            (
                f"/api/v1/workflows/{self.other_workflow.public_id}",
                "/api/v1/workflows/wfl_missing",
                {"name": "Compromised"},
                self.other_workflow,
            ),
            (
                f"/api/v1/api-clients/{self.other_client.public_id}",
                "/api/v1/api-clients/api_missing",
                {"name": "Compromised"},
                self.other_client,
            ),
            (
                f"/api/v1/webhook-endpoints/{self.other_webhook.public_id}",
                "/api/v1/webhook-endpoints/whk_missing",
                {"description": "Compromised"},
                self.other_webhook,
            ),
        )
        for foreign_path, missing_path, payload, instance in cases:
            with self.subTest(path=foreign_path):
                self.assert_non_disclosing_not_found(
                    "patch", foreign_path, missing_path, payload
                )
                instance.refresh_from_db()
                self.assertNotEqual(
                    getattr(instance, next(iter(payload))), "Compromised"
                )

    def test_cross_tenant_list_matrix_hides_foreign_resources(self):
        cases = (
            ("/api/v1/projects/", self.other_project.public_id),
            ("/api/v1/workflows/", self.other_workflow.public_id),
            ("/api/v1/subjects/", self.other_subject.public_id),
            ("/api/v1/api-clients/", self.other_client.public_id),
            ("/api/v1/webhook-endpoints/", self.other_webhook.public_id),
            ("/api/v1/audit-events/", self.other_audit_event.public_id),
            ("/api/v1/notifications/", self.other_notification.public_id),
        )
        for path, foreign_id in cases:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertNotIn(foreign_id, str(response.data))

    def test_cross_tenant_delete_is_non_disclosing_and_preserves_resource(self):
        self.assert_non_disclosing_not_found(
            "delete",
            f"/api/v1/organization/me/verification-documents/{self.other_document.public_id}/",
            "/api/v1/organization/me/verification-documents/doc_missing/",
        )
        self.other_document.refresh_from_db()
        self.assertIsNone(self.other_document.deleted_at)

    def test_cross_tenant_action_matrix_preserves_foreign_rows(self):
        """Exercise authorized actors, complete error envelopes and persisted state."""
        cases = []

        def add(method, resource, instance, suffix="", data=None):
            cases.append(
                (
                    method,
                    f"/api/v1/{resource}/{instance.public_id}{suffix}",
                    f"/api/v1/{resource}/{instance.public_id_prefix}_missing{suffix}",
                    data or {},
                )
            )

        for action in ("activate", "reactivate", "suspend", "workflows:instantiate"):
            add("post", "projects", self.other_project, f"/{action}")
        for action in ("clone", "publish", "archive"):
            add("post", "workflows", self.other_workflow, f"/{action}")
        for action in ("rotate", "revoke", "reactivate"):
            add("post", "api-clients", self.other_client, f"/{action}")
        for action in ("test", "rotate", "disable", "reactivate"):
            add("post", "webhook-endpoints", self.other_webhook, f"/{action}")
        add("post", "webhook-endpoints/events", self.other_event, "/replay")
        add("patch", "policies", self.other_policy, data={"name": "Compromised"})
        for action in ("clone", "activate", "archive"):
            add("post", "policies", self.other_policy, f"/{action}")
        for action in ("export", "delete"):
            add(
                "post",
                "subjects",
                self.other_subject,
                data={"action": action, "confirm": True},
            )
        for action in ("cancel", "resend-link", "simulate"):
            add(
                "post",
                "verifications",
                self.other_verification,
                f"/{action}",
                {"scenario": "approved"},
            )
        for action in ("decision", "approval"):
            add(
                "post",
                "verifications/manual-reviews",
                self.other_verification,
                f"/{action}",
            )
        for action in ("resend", "revoke"):
            add("post", "auth/team/invitations", self.other_invitation, f"/{action}")
        add("post", "auth/sessions", self.other_session, "/revoke")
        add(
            "patch",
            "verifications/review-queues",
            self.other_queue,
            data={"name": "Compromised"},
        )
        add(
            "put",
            "verifications/review-queues",
            self.other_queue,
            "/members",
            {"user_id": self.user.public_id},
        )
        add("post", "verifications/review-queues", self.other_queue, "/cases")
        add("post", "verifications/review-quality", self.other_quality)
        add("post", "verifications/review-quality", self.other_quality, "/allocate")
        add("post", "providers", self.other_provider, "/configurations/")
        for action in ("test", "activate", "assign"):
            add(
                "post",
                "providers/configurations",
                self.other_configuration,
                f"/{action}/",
            )
        add("post", "consent/records", self.other_consent, "/withdraw")
        for action in ("activate", "disable"):
            add("post", "tenant/kms-bindings", self.other_kms, f"/{action}")
        add("post", "billing/invoices", self.other_invoice, "/checkout")
        add("post", "billing/payments", self.other_payment)
        self.other_document.status = "initiated"
        self.other_document.save(update_fields=["status"])
        for method, suffix in (
            ("post", "/complete/"),
            ("put", "/content/"),
            ("delete", "/"),
        ):
            add(
                method,
                "organization/me/verification-documents",
                self.other_document,
                suffix,
            )

        instances = (
            self.other_project,
            self.other_workflow,
            self.other_client,
            self.other_webhook,
            self.other_event,
            self.other_policy,
            self.other_subject,
            self.other_verification,
            self.other_invitation,
            self.other_session,
            self.other_queue,
            self.other_quality,
            self.other_provider,
            self.other_configuration,
            self.other_document,
            self.other_consent,
            self.other_kms,
            self.other_invoice,
            self.other_payment,
        )
        # Compare every persisted field, including secrets, status and timestamps.
        before = {
            type(obj): list(type(obj).objects.filter(pk=obj.pk).values())
            for obj in instances
        }
        counts = {type(obj): type(obj).objects.count() for obj in instances}
        for method, foreign, missing, data in cases:
            with self.subTest(method=method, path=foreign):
                self.assert_non_disclosing_not_found(method, foreign, missing, data)
                for obj in instances:
                    self.assertEqual(type(obj).objects.count(), counts[type(obj)])
                    self.assertEqual(
                        list(type(obj).objects.filter(pk=obj.pk).values()),
                        before[type(obj)],
                    )
        self.assertEqual(self.other_queue.members.count(), 0)
        self.assertEqual(self.other_subject.exports.count(), 0)
