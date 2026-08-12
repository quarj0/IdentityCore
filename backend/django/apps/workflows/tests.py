from rest_framework.test import APITestCase
from django.apps import apps as django_apps
from importlib import import_module
from apps.accounts.models import PlatformUser, PlatformUserStatus
from apps.organizations.models import Organization
from apps.projects.models import Project
from apps.tenants.models import Tenant
from apps.workflows.models import Workflow, WorkflowVersion


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
        self.assertEqual(version.workflow_name, "KYC")

        workflow = version.workflow
        workflow.name = "Renamed draft"
        workflow.save(update_fields=["name", "updated_at"])
        version.refresh_from_db()
        self.assertEqual(version.snapshot()["workflow_name"], "KYC")

        versions = self.client.get(f"/api/v1/workflows/{workflow_id}/versions")
        self.assertEqual(versions.status_code, 200)
        self.assertEqual(versions.data["data"]["results"][0]["workflow_name"], "KYC")

    def test_workflow_name_migration_backfills_existing_versions(self):
        workflow = Workflow.objects.create(
            tenant=self.tenant,
            project=self.project,
            created_by=self.user,
            name="Published name",
            steps_json=["consent", "decision"],
        )
        created = self.client.post(
            f"/api/v1/workflows/{workflow.public_id}/publish", {}, format="json"
        )
        self.assertEqual(created.status_code, 200)
        version = WorkflowVersion.objects.get(workflow=workflow)
        WorkflowVersion.objects.filter(pk=version.pk).update(workflow_name="")

        migration = import_module(
            "apps.workflows.migrations.0004_workflowversion_workflow_name"
        )
        migration.backfill_workflow_names(django_apps, None)

        version.refresh_from_db()
        self.assertEqual(version.workflow_name, "Published name")

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
