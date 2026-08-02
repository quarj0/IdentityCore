from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import PlatformUser, PlatformUserStatus
from apps.api_clients.models import APIClient
from apps.audit.models import AuditEvent
from apps.notifications.models import Notification
from apps.organizations.models import (
    Organization,
    OrganizationStatus,
    OrganizationSupportingDocument,
)
from apps.projects.models import Project
from apps.tenants.models import Tenant
from apps.verification_subjects.models import VerificationSubject
from apps.webhooks.models import WebhookEndpoint
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
        foreign = getattr(self.client, method)(foreign_path, data or {}, format="json")
        missing = getattr(self.client, method)(missing_path, data or {}, format="json")
        self.assertEqual(foreign.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(foreign.status_code, missing.status_code)
        self.assertEqual(foreign.data["error"]["code"], "resource_not_found")
        self.assertEqual(foreign.data["error"]["code"], missing.data["error"]["code"])

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
