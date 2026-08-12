from django.utils import timezone
from rest_framework.test import APITestCase

from apps.accounts.models import PlatformUser, PlatformUserStatus
from apps.organizations.models import Organization
from apps.projects.models import Project
from apps.tenants.models import Tenant
from apps.verifications.models import Verification


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
        self.assertEqual(response.data["data"]["pagination"]["page"], 1)

    def test_list_filters_and_paginates_supported_fields(self):
        Project.objects.create(
            tenant=self.tenant,
            name="Production project",
            slug="production-project",
            environment="production",
            created_by=self.user,
        )
        Project.objects.create(
            tenant=self.tenant,
            name="Sandbox project",
            slug="sandbox-project",
            environment="sandbox",
            created_by=self.user,
        )

        response = self.client.get(
            "/api/v1/projects/",
            {"environment": "sandbox", "status": "active", "page_size": 1},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["data"]["results"]), 1)
        self.assertEqual(response.data["data"]["results"][0]["environment"], "sandbox")
        self.assertEqual(response.data["data"]["pagination"]["page_size"], 1)

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

        unsupported = self.client.post(
            f"/api/v1/projects/{project_id}/disable", {}, format="json"
        )
        self.assertEqual(unsupported.status_code, 400)

    def test_environment_cannot_change_after_verification_activity(self):
        project = Project.objects.create(
            tenant=self.tenant,
            name="Immutable Environment",
            slug="immutable-environment",
            environment="sandbox",
            created_by=self.user,
        )
        subject = self.tenant.verification_subjects.create(full_name="Project Subject")
        Verification.objects.create(
            tenant=self.tenant,
            project=project,
            organization=self.organization,
            verification_subject=subject,
            purpose="Environment snapshot",
            expires_at=timezone.now(),
        )

        response = self.client.patch(
            f"/api/v1/projects/{project.public_id}",
            {"environment": "production"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        project.refresh_from_db()
        self.assertEqual(project.environment, "sandbox")
