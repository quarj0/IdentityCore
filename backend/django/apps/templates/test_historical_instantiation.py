from rest_framework.test import APITestCase

from apps.templates import tests as fixtures
from apps.templates.models import TemplateStatus
from apps.workflows.models import Workflow


class HistoricalTemplateInstantiationTests(APITestCase):
    setUp = fixtures.WorkflowTemplateAPITests.setUp

    def instantiate(self, *, name="Original name", key="original"):
        return self.client.post(
            f"/api/v1/projects/{self.project.public_id}/workflows:instantiate",
            {
                "template_id": self.template.public_id,
                "template_version": "1.0",
                "name": name,
            },
            format="json",
            HTTP_IDEMPOTENCY_KEY=key,
        )

    def test_name_collision_returns_validation_error(self):
        self.assertEqual(self.instantiate().status_code, 201)
        self.assertEqual(self.instantiate(key="different").status_code, 400)

    def test_exact_replay_survives_workflow_rename(self):
        first = self.instantiate()
        Workflow.objects.filter(public_id=first.data["data"]["id"]).update(
            name="Renamed workflow"
        )
        replay = self.instantiate()
        self.assertEqual(replay.status_code, 200)
        self.assertEqual(replay.data["data"]["id"], first.data["data"]["id"])
        self.assertEqual(replay.data["data"]["name"], "Renamed workflow")

    def test_exact_replay_survives_source_archive(self):
        first = self.instantiate()
        self.template.status = TemplateStatus.ARCHIVED
        self.template.save()
        replay = self.instantiate()
        self.assertEqual(replay.status_code, 200)
        self.assertEqual(replay.data["data"]["id"], first.data["data"]["id"])

    def test_omitted_name_replay_survives_source_rename(self):
        first = self.instantiate(name="")
        self.template.name = "Renamed source"
        self.template.save()
        replay = self.instantiate(name="")
        self.assertEqual(replay.status_code, 200)
        self.assertEqual(replay.data["data"]["id"], first.data["data"]["id"])

    def test_repeated_instantiation_counts_one_adopting_organization(self):
        self.assertEqual(self.instantiate().status_code, 201)
        self.assertEqual(
            self.instantiate(name="Another workflow", key="another").status_code, 201
        )
        self.template.refresh_from_db()
        self.assertEqual(self.template.usage_count, 2)
        self.assertEqual(self.template.cloned_by_organizations, 1)

    def test_catalog_omits_internal_identity_and_operational_fields(self):
        private = {
            "created_by_id",
            "created_by_email",
            "owner_team",
            "risk_level",
            "usage_count",
            "cloned_by_organizations",
        }
        listing = self.client.get("/api/v1/workflow-templates/").data["data"][
            "results"
        ][0]
        detail = self.client.get(
            f"/api/v1/workflow-templates/{self.template.public_id}"
        ).data["data"]
        for payload in (listing, detail):
            self.assertFalse(private.intersection(payload))
            self.assertEqual(payload["steps"], self.template.steps_json)

    def test_legacy_key_without_original_request_evidence_returns_conflict(self):
        first = self.instantiate()
        Workflow.objects.filter(public_id=first.data["data"]["id"]).update(
            instantiation_request_hash=""
        )
        replay = self.instantiate()
        self.assertEqual(replay.status_code, 409)
        self.assertEqual(Workflow.objects.count(), 1)

    def test_renamed_workflow_does_not_authorize_different_request(self):
        first = self.instantiate()
        Workflow.objects.filter(public_id=first.data["data"]["id"]).update(
            name="Changed request"
        )
        self.assertEqual(self.instantiate(name="Changed request").status_code, 409)

    def test_distinct_organizations_count_separately(self):
        from apps.accounts.models import PlatformUser
        from apps.tenants.models import Tenant
        from apps.projects.models import Project
        from apps.organizations.models import Organization

        self.assertEqual(self.instantiate().status_code, 201)
        tenant = Tenant.objects.create(
            organization=Organization.objects.create(
                name="Second adopter", slug="second-adopter", status="active"
            ),
            name="Second tenant",
            slug="second-adopter",
            status="active",
        )
        user = PlatformUser.objects.create_user(
            email="second-adopter@example.com",
            password="StrongPassword123!",
            status="active",
            tenant=tenant,
        )
        project = Project.objects.create(
            tenant=tenant, created_by=user, name="Second sandbox", slug="second-sandbox"
        )
        self.client.force_authenticate(user)
        self.project = project
        self.assertEqual(self.instantiate().status_code, 201)
        self.template.refresh_from_db()
        self.assertEqual(self.template.usage_count, 2)
        self.assertEqual(self.template.cloned_by_organizations, 2)

    def test_migration_reconciles_existing_inflated_adoption(self):
        from importlib import import_module
        from types import SimpleNamespace
        from django.apps import apps
        from django.db import connection

        self.instantiate()
        self.instantiate(name="Second", key="second")
        type(self.template).objects.filter(pk=self.template.pk).update(
            cloned_by_organizations=97
        )
        migration = import_module(
            "apps.templates.migrations.0003_reconcile_organization_adoption"
        )
        migration.reconcile_organization_adoption(
            apps, SimpleNamespace(connection=connection)
        )
        self.template.refresh_from_db()
        self.assertEqual(self.template.cloned_by_organizations, 1)
        self.assertEqual(self.template.usage_count, 2)
