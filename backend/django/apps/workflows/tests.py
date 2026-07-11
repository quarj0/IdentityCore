from rest_framework.test import APITestCase
from apps.accounts.models import PlatformUser, PlatformUserStatus
from apps.organizations.models import Organization
from apps.projects.models import Project
from apps.tenants.models import Tenant
from apps.workflows.models import WorkflowVersion


class WorkflowAPITests(APITestCase):
    def setUp(self):
        organization = Organization.objects.create(
            name="Flow", slug="flow-org", status="active"
        )
        self.tenant = Tenant.objects.create(
            organization=organization, name="Flow", slug="flow-tenant", status="active"
        )
        self.user = PlatformUser.objects.create_user(
            email="flow@example.com",
            password="StrongPassword123!",
            status=PlatformUserStatus.ACTIVE,
            tenant=self.tenant,
        )
        self.project = Project.objects.create(
            tenant=self.tenant,
            created_by=self.user,
            name="Sandbox",
            slug="sandbox",
            is_default=True,
        )
        self.client.force_authenticate(self.user)

    def test_publish_creates_immutable_policy_version(self):
        created = self.client.post(
            "/api/v1/workflows/",
            {
                "project_id": self.project.public_id,
                "name": "KYC",
                "steps": ["consent", "document", "decision"],
                "settings": {},
            },
            format="json",
        )
        self.assertEqual(created.status_code, 201)
        workflow_id = created.data["data"]["id"]
        published = self.client.post(
            f"/api/v1/workflows/{workflow_id}/publish", {}, format="json"
        )
        self.assertEqual(published.status_code, 200)
        version = WorkflowVersion.objects.get(workflow__public_id=workflow_id)
        self.assertEqual(version.version, 1)
        self.assertEqual(version.policy.project, self.project)

    def test_rejects_unsupported_steps(self):
        response = self.client.post(
            "/api/v1/workflows/",
            {
                "project_id": self.project.public_id,
                "name": "Bad",
                "steps": ["consent", "magic", "decision"],
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
