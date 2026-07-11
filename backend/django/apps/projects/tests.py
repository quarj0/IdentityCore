from rest_framework.test import APITestCase
from apps.accounts.models import PlatformUser, PlatformUserStatus
from apps.organizations.models import Organization
from apps.tenants.models import Tenant


class ProjectAPITests(APITestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            name="Acme", slug="projects-acme", status="active"
        )
        self.tenant = Tenant.objects.create(
            organization=self.organization,
            name="Acme",
            slug="projects-acme",
            status="active",
        )
        self.user = PlatformUser.objects.create_user(
            email="projects@example.com",
            password="StrongPassword123!",
            status=PlatformUserStatus.ACTIVE,
            tenant=self.tenant,
        )
        self.client.force_authenticate(self.user)

    def test_list_creates_default_sandbox(self):
        response = self.client.get("/api/v1/projects/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["results"][0]["environment"], "sandbox")

    def test_create_and_suspend_project(self):
        response = self.client.post(
            "/api/v1/projects/",
            {"name": "Mobile", "environment": "sandbox", "allowed_origins": []},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        project_id = response.data["data"]["id"]
        suspended = self.client.post(
            f"/api/v1/projects/{project_id}/suspend", {}, format="json"
        )
        self.assertEqual(suspended.data["data"]["status"], "suspended")
