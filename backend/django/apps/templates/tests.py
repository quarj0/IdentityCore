from rest_framework.test import APITestCase

from apps.accounts.models import PlatformUser, PlatformUserStatus
from apps.audit.models import AuditEvent
from apps.organizations.models import Organization
from apps.projects.models import Project
from apps.templates.models import Template, TemplateCategory, TemplateStatus
from apps.tenants.models import Tenant
from apps.workflows.models import Workflow


class WorkflowTemplateAPITests(APITestCase):
    def setUp(self):
        organization = Organization.objects.create(
            name="Template Org", slug="template-org", status="active"
        )
        self.tenant = Tenant.objects.create(
            organization=organization,
            name="Template Tenant",
            slug="template-tenant",
            status="active",
        )
        self.user = PlatformUser.objects.create_user(
            email="templates@example.com",
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
        self.template = Template.objects.create(
            name="Customer onboarding",
            slug="customer-onboarding",
            description="Verify a customer.",
            category=TemplateCategory.BANKING_KYC,
            status=TemplateStatus.PUBLISHED,
            version="1.0",
            countries_json=["GH"],
            required_checks_json=["document", "liveness", "face_match"],
            steps_json=[
                "consent",
                "document",
                "selfie",
                "liveness",
                "face_match",
                "decision",
            ],
            settings_json={"required_liveness_level": "active"},
            provider_requirements_json=["document_ocr", "liveness", "face_match"],
            output_claims_json=["verification_status"],
            created_by=self.user,
        )
        self.client.force_authenticate(self.user)

    def test_catalog_returns_only_published_templates(self):
        Template.objects.create(
            name="Draft",
            slug="draft",
            category=TemplateCategory.BANKING_KYC,
            status=TemplateStatus.DRAFT,
            version="1.0",
            created_by=self.user,
        )

        response = self.client.get("/api/v1/workflow-templates/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["data"]["results"]), 1)
        self.assertEqual(
            response.data["data"]["results"][0]["steps"], self.template.steps_json
        )

    def test_instantiates_template_with_lineage_and_audit(self):
        response = self.client.post(
            f"/api/v1/projects/{self.project.public_id}/workflows:instantiate",
            {
                "template_id": self.template.public_id,
                "template_version": "1.0",
                "name": "Primary customer onboarding",
            },
            format="json",
            HTTP_IDEMPOTENCY_KEY="first-workflow",
        )

        self.assertEqual(response.status_code, 201)
        workflow = Workflow.objects.get(public_id=response.data["data"]["id"])
        self.assertEqual(workflow.source_template, self.template)
        self.assertEqual(workflow.source_template_version, "1.0")
        self.assertEqual(workflow.steps_json, self.template.steps_json)
        self.assertEqual(workflow.settings_json["required_liveness_level"], "active")
        self.assertTrue(
            AuditEvent.objects.filter(
                action="workflow.template_instantiated", target_id=workflow.public_id
            ).exists()
        )

    def test_same_idempotency_key_replays_created_workflow(self):
        url = f"/api/v1/projects/{self.project.public_id}/workflows:instantiate"
        payload = {
            "template_id": self.template.public_id,
            "template_version": "1.0",
            "name": "Primary customer onboarding",
        }
        first = self.client.post(
            url, payload, format="json", HTTP_IDEMPOTENCY_KEY="same-request"
        )
        replay = self.client.post(
            url, payload, format="json", HTTP_IDEMPOTENCY_KEY="same-request"
        )

        self.assertEqual(first.status_code, 201)
        self.assertEqual(replay.status_code, 200)
        self.assertEqual(first.data["data"]["id"], replay.data["data"]["id"])
        self.assertFalse(replay.data["data"]["created"])
        self.assertEqual(Workflow.objects.count(), 1)

    def test_idempotency_key_rejects_different_request(self):
        url = f"/api/v1/projects/{self.project.public_id}/workflows:instantiate"
        payload = {
            "template_id": self.template.public_id,
            "template_version": "1.0",
            "name": "First name",
        }
        self.client.post(url, payload, format="json", HTTP_IDEMPOTENCY_KEY="conflict")
        payload["name"] = "Different name"

        response = self.client.post(
            url, payload, format="json", HTTP_IDEMPOTENCY_KEY="conflict"
        )

        self.assertEqual(response.status_code, 409)

    def test_requires_current_template_version(self):
        url = f"/api/v1/projects/{self.project.public_id}/workflows:instantiate"
        response = self.client.post(
            url,
            {
                "template_id": self.template.public_id,
                "template_version": "2.0",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_requires_idempotency_key(self):
        response = self.client.post(
            f"/api/v1/projects/{self.project.public_id}/workflows:instantiate",
            {
                "template_id": self.template.public_id,
                "template_version": "1.0",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    def test_cannot_instantiate_into_another_tenants_project(self):
        other_organization = Organization.objects.create(
            name="Other", slug="other-org", status="active"
        )
        other_tenant = Tenant.objects.create(
            organization=other_organization,
            name="Other",
            slug="other-tenant",
            status="active",
        )
        other_user = PlatformUser.objects.create_user(
            email="other@example.com",
            password="StrongPassword123!",
            status=PlatformUserStatus.ACTIVE,
            tenant=other_tenant,
        )
        other_project = Project.objects.create(
            tenant=other_tenant,
            created_by=other_user,
            name="Other sandbox",
            slug="other-sandbox",
        )

        response = self.client.post(
            f"/api/v1/projects/{other_project.public_id}/workflows:instantiate",
            {
                "template_id": self.template.public_id,
                "template_version": "1.0",
            },
            format="json",
            HTTP_IDEMPOTENCY_KEY="cross-tenant",
        )

        self.assertEqual(response.status_code, 404)
