from datetime import timedelta
from importlib import import_module
from types import SimpleNamespace

from django.apps import apps
from django.db import connection
from django.db.migrations.recorder import MigrationRecorder
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APITestCase
from django.utils import timezone

from apps.accounts.models import PlatformUser
from apps.verification_policies.models import VerificationPolicy
from apps.verifications.models import Verification
from apps.verification_subjects.models import VerificationSubject
from apps.workflows import tests as fixtures
from apps.workflows.models import Workflow, WorkflowVersion


class LegacyWorkflowLineageTests(APITestCase):
    setUp = fixtures.WorkflowAPITests.setUp

    def version(
        self,
        *,
        policy_name="Original published name",
        name="Later draft name",
        settings=None,
        actor=None,
    ):
        workflow = Workflow.objects.create(
            tenant=self.tenant, project=self.project, created_by=self.user, name=name
        )
        policy = VerificationPolicy.objects.create(
            tenant=self.tenant,
            project=self.project,
            created_by=self.user,
            name=policy_name,
            version=1,
            status="active",
        )
        return WorkflowVersion.objects.create(
            workflow=workflow,
            workflow_name=name,
            version=1,
            policy=policy,
            published_by=actor or self.user,
            steps_json=["consent", "decision"],
            settings_json=settings if settings is not None else {},
        )

    def case(self, version, snapshot=None):
        return Verification.objects.create(
            tenant=self.tenant,
            organization=self.tenant.organization,
            verification_subject=VerificationSubject.objects.create(
                tenant=self.tenant, full_name="Synthetic subject"
            ),
            policy_public_id=version.policy.public_id,
            workflow_snapshot_json=snapshot or {},
            purpose="Legacy lineage coverage",
            expires_at=timezone.now() + timedelta(hours=1),
        )

    def test_original_backfill_recovers_published_policy_name_after_parent_rename(self):
        version = self.version()
        import_module(
            "apps.workflows.migrations.0004_workflowversion_workflow_name"
        ).backfill_workflow_names(apps, None)
        version.refresh_from_db()
        self.assertEqual(version.workflow_name, "Original published name")
        self.assertEqual(version.workflow.name, "Later draft name")

    def test_platform_policy_suffix_and_truncated_name_are_handled_honestly(self):
        actor = PlatformUser.objects.create_superuser(
            email="legacy-platform@example.test", password="unused", status="active"
        )
        version = self.version(
            policy_name="Original admin name workflow policy", actor=actor
        )
        backfill = import_module(
            "apps.workflows.migrations.0004_workflowversion_workflow_name"
        ).backfill_workflow_names
        backfill(apps, None)
        version.refresh_from_db()
        self.assertEqual(version.workflow_name, "Original admin name")
        version.policy.name = (
            f"{'x' * 180} [{version.workflow.public_id}] workflow policy"
        )
        version.policy.save()
        backfill(apps, None)
        version.refresh_from_db()
        self.assertEqual(version.workflow_name, "")

    def test_snapshot_and_backfill_preserve_legacy_scalar_and_list_settings(self):
        for index, settings in enumerate(([1, "legacy"], 42, "legacy", False)):
            with self.subTest(settings=settings):
                version = self.version(
                    name=f"Legacy {index}",
                    policy_name=f"Legacy policy {index}",
                    settings=settings,
                )
                case = self.case(version)
                import_module(
                    "apps.verifications.migrations.0017_backfill_workflow_snapshots"
                ).backfill_workflow_snapshots(apps, None)
                case.refresh_from_db()
                self.assertEqual(case.workflow_snapshot_json["settings"], settings)
                self.assertEqual(version.snapshot()["settings"], settings)

    def test_forward_repair_corrects_legacy_assertion_and_preserves_new_publications(
        self,
    ):
        cutoff = timezone.now() - timedelta(hours=1)
        MigrationRecorder.Migration.objects.filter(
            app="workflows", name="0004_workflowversion_workflow_name"
        ).update(applied=cutoff)
        legacy = self.version()
        WorkflowVersion.objects.filter(pk=legacy.pk).update(
            published_at=cutoff - timedelta(minutes=1)
        )
        case = self.case(legacy, legacy.snapshot())
        current = self.version(
            name="Trustworthy current name",
            policy_name="Do not infer this current name",
        )
        current_case = self.case(current, current.snapshot())
        editor = SimpleNamespace(connection=connection)
        import_module(
            "apps.workflows.migrations.0006_repair_legacy_workflow_names"
        ).repair(apps, editor)
        repair = import_module(
            "apps.verifications.migrations.0025_repair_legacy_workflow_name_snapshots"
        ).repair
        repair(apps, editor)
        repair(apps, editor)
        case.refresh_from_db()
        current.refresh_from_db()
        current_case.refresh_from_db()
        self.assertEqual(
            case.workflow_snapshot_json["workflow_name"], "Original published name"
        )
        self.assertEqual(
            case.workflow_snapshot_json["workflow_name_backfill_correction"][
                "previous_assertion"
            ],
            "Later draft name",
        )
        self.assertEqual(current.workflow_name, "Trustworthy current name")
        self.assertNotIn(
            "workflow_name_backfill_correction", current_case.workflow_snapshot_json
        )

    def test_rest_clone_clears_template_instantiation_replay_identity(self):
        source = self.version().workflow
        source.instantiation_key = "synthetic-original-request"
        source.instantiation_request_hash = "a" * 64
        source.save()
        response = self.client.post(
            f"/api/v1/workflows/{source.public_id}/clone", {}, format="json"
        )
        self.assertEqual(response.status_code, 200, response.data)
        clone = Workflow.objects.get(public_id=response.data["data"]["id"])
        self.assertEqual(clone.instantiation_key, "")
        self.assertEqual(clone.instantiation_request_hash, "")
        source.refresh_from_db()
        self.assertEqual(source.instantiation_key, "synthetic-original-request")

    def test_workflow_list_eager_loads_lineage_without_per_row_queries(self):
        from apps.templates.models import Template

        template = Template.objects.create(
            name="Synthetic template",
            category="banking_kyc",
            status="published",
            version="1.0",
            created_by=self.user,
        )
        Workflow.objects.create(
            tenant=self.tenant,
            project=self.project,
            created_by=self.user,
            name="Workflow 0",
            source_template=template,
        )
        with CaptureQueriesContext(connection) as one:
            response = self.client.get("/api/v1/workflows/")
        self.assertEqual(response.status_code, 200)
        for index in range(1, 6):
            Workflow.objects.create(
                tenant=self.tenant,
                project=self.project,
                created_by=self.user,
                name=f"Workflow {index}",
                source_template=template,
            )
        with CaptureQueriesContext(connection) as many:
            response = self.client.get("/api/v1/workflows/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["data"]["results"]), 6)
        self.assertEqual(len(many), len(one))
        deleted = Workflow.objects.get(name="Workflow 0")
        deleted.soft_delete()
        self.assertEqual(
            len(self.client.get("/api/v1/workflows/").data["data"]["results"]), 5
        )
        self.assertEqual(
            self.client.get(f"/api/v1/workflows/{deleted.public_id}/").status_code, 404
        )
