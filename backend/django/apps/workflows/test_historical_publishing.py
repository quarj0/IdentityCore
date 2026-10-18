from django.db import transaction
from django.test import RequestFactory
from rest_framework.test import APITestCase

from apps.accounts.models import PlatformUser
from apps.projects.models import Project
from apps.workflows.models import Workflow, WorkflowVersion
from apps.workflows import tests as workflow_fixtures
from config.graphql_schema import schema


class HistoricalWorkflowPublishingTests(APITestCase):
    def setUp(self):
        workflow_fixtures.WorkflowAPITests.setUp(self)
        self.admin = PlatformUser.objects.create_superuser(
            email="workflow-audit-admin@example.test",
            password="StrongPassword123!",
            status="active",
        )

    def workflow(self, name="Historical publishing", **kwargs):
        return Workflow.objects.create(
            tenant=self.tenant,
            project=kwargs.pop("project", self.project),
            created_by=self.user,
            name=name,
            steps_json=["consent", "document", "decision"],
            **kwargs,
        )

    def graphql(self, query, variables):
        request = RequestFactory().post("/api/graphql")
        request.user = self.admin
        with transaction.atomic():
            result = schema.execute_sync(
                query,
                variable_values=variables,
                context_value={"request": request},
            )
            if result.errors:
                transaction.set_rollback(True)
        return result

    def publish(self, workflow):
        return self.graphql(
            "mutation($id:String!){publishPlatformWorkflow(workflowId:$id){id version policyId}}",
            {"id": workflow.public_id},
        )

    def test_platform_create_with_steps_can_publish_and_edit_without_mutating_version(
        self,
    ):
        result = self.graphql(
            'mutation($tenant:String!,$project:String!){createPlatformWorkflow(tenantId:$tenant,projectId:$project,name:"Authored workflow",steps:["consent","document","decision"]){id steps}}',
            {"tenant": self.tenant.public_id, "project": self.project.public_id},
        )
        self.assertIsNone(result.errors, result.errors)
        workflow = Workflow.objects.get(
            public_id=result.data["createPlatformWorkflow"]["id"]
        )
        self.assertIsNone(self.publish(workflow).errors)
        version = WorkflowVersion.objects.get(workflow=workflow)
        result = self.graphql(
            'mutation($id:String!){updatePlatformWorkflow(workflowId:$id,steps:["consent","selfie","liveness","decision"]){id status steps}}',
            {"id": workflow.public_id},
        )
        self.assertIsNone(result.errors, result.errors)
        self.assertEqual(result.data["updatePlatformWorkflow"]["status"], "draft")
        version.refresh_from_db()
        self.assertEqual(version.steps_json, ["consent", "document", "decision"])
        self.assertIsNone(self.publish(workflow).errors)
        self.assertEqual(WorkflowVersion.objects.filter(workflow=workflow).count(), 2)

    def test_platform_create_rejects_missing_empty_unknown_or_duplicate_steps(self):
        query = 'mutation($tenant:String!,$project:String!,$steps:[JSON!]){createPlatformWorkflow(tenantId:$tenant,projectId:$project,name:"Invalid draft",steps:$steps){id}}'
        count = Workflow.objects.count()
        from apps.audit.models import AuditEvent

        audit_count = AuditEvent.objects.count()
        for steps in (
            None,
            [],
            ["consent"],
            ["consent", "magic", "decision"],
            ["consent", "decision", "decision"],
            [{"type": "consent"}, "decision"],
        ):
            with self.subTest(steps=steps):
                result = self.graphql(
                    query,
                    {
                        "tenant": self.tenant.public_id,
                        "project": self.project.public_id,
                        "steps": steps,
                    },
                )
                self.assertTrue(result.errors)
        self.assertEqual(Workflow.objects.count(), count)
        self.assertEqual(AuditEvent.objects.count(), audit_count)

    def test_platform_publication_copies_execution_settings(self):
        workflow = self.workflow(
            settings_json={
                "required_document_types": ["passport"],
                "required_liveness_level": "active",
                "face_match_threshold": 0.94,
                "manual_review_threshold": 0.75,
                "verification_expiry_minutes": 90,
                "media_retention_days": 14,
                "metadata_retention_days": 180,
            }
        )
        result = self.publish(workflow)
        self.assertIsNone(result.errors, result.errors)
        policy = WorkflowVersion.objects.get(workflow=workflow).policy
        self.assertEqual(policy.required_document_types_json, ["passport"])
        self.assertEqual(policy.required_liveness_level, "active")
        self.assertEqual(float(policy.face_match_threshold), 0.94)
        self.assertEqual(float(policy.manual_review_threshold), 0.75)
        self.assertEqual(policy.verification_expiry_minutes, 90)
        self.assertEqual(policy.media_retention_days, 14)
        self.assertEqual(policy.metadata_retention_days, 180)

    def test_editing_published_workflow_returns_it_to_draft(self):
        workflow = self.workflow(status="published", current_version=1)
        result = self.graphql(
            'mutation($id:String!){updatePlatformWorkflow(workflowId:$id,steps:["consent","selfie","decision"]){id status}}',
            {"id": workflow.public_id},
        )
        self.assertIsNone(result.errors, result.errors)
        workflow.refresh_from_db()
        self.assertEqual(workflow.status, "draft")
        self.assertEqual(workflow.current_version, 1)

    def test_publish_rejects_unsupported_or_incomplete_steps(self):
        for steps in [
            ["consent", "unknown", "decision"],
            ["document", "decision"],
            ["consent", "consent", "decision"],
        ]:
            with self.subTest(steps=steps):
                workflow = self.workflow(name="Invalid " + str(steps))
                workflow.steps_json = steps
                workflow.save(update_fields=["steps_json", "updated_at"])
                result = self.publish(workflow)
                self.assertIsNotNone(result.errors)
                self.assertFalse(workflow.versions.exists())

    def test_publish_rejects_unapproved_organizations(self):
        for state in ["pending_review", "suspended"]:
            with self.subTest(state=state):
                self.tenant.organization.status = state
                self.tenant.organization.save(update_fields=["status", "updated_at"])
                workflow = self.workflow(name="Organization " + state)
                result = self.publish(workflow)
                self.assertIsNotNone(result.errors)
                self.assertFalse(workflow.versions.exists())

    def test_archived_workflow_cannot_be_republished(self):
        workflow = self.workflow(status="archived")
        result = self.publish(workflow)
        self.assertIsNotNone(result.errors)
        self.assertFalse(workflow.versions.exists())
        workflow.refresh_from_db()
        self.assertEqual(workflow.status, "archived")

    def test_platform_actor_does_not_become_cross_tenant_policy_creator(self):
        workflow = self.workflow()
        result = self.publish(workflow)
        self.assertIsNone(result.errors, result.errors)
        policy = WorkflowVersion.objects.get(workflow=workflow).policy
        self.assertIn(policy.created_by_id, {None, self.user.pk})
        policy.full_clean()

    def test_platform_created_workflow_retains_publisher_without_fabricating_tenant_creator(
        self,
    ):
        workflow = self.workflow()
        workflow.created_by = self.admin
        workflow.save(update_fields=["created_by", "updated_at"])
        result = self.publish(workflow)
        self.assertIsNone(result.errors, result.errors)
        version = workflow.versions.get()
        self.assertIsNone(version.policy.created_by_id)
        self.assertEqual(version.published_by_id, self.admin.pk)
        version.policy.full_clean()

    def test_partial_settings_edit_preserves_execution_controls(self):
        workflow = self.workflow(
            settings_json={"face_match_threshold": 0.94, "maker_checker_required": True}
        )
        result = self.graphql(
            "mutation($id:String!,$settings:JSON!){updatePlatformWorkflow(workflowId:$id,settings:$settings){id}}",
            {"id": workflow.public_id, "settings": {"media_retention_days": 7}},
        )
        self.assertIsNone(result.errors, result.errors)
        workflow.refresh_from_db()
        self.assertEqual(workflow.settings_json["media_retention_days"], 7)
        self.assertEqual(workflow.settings_json["face_match_threshold"], 0.94)
        self.assertTrue(workflow.settings_json["maker_checker_required"])

    def test_legacy_invalid_settings_can_be_replaced(self):
        workflow = self.workflow(settings_json=[])
        result = self.graphql(
            "mutation($id:String!,$settings:JSON!){updatePlatformWorkflow(workflowId:$id,settings:$settings){id}}",
            {
                "id": workflow.public_id,
                "settings": {"required_document_types": ["passport"]},
            },
        )
        self.assertIsNone(result.errors, result.errors)
        workflow.refresh_from_db()
        self.assertEqual(
            workflow.settings_json["required_document_types"], ["passport"]
        )
        self.assertIsNone(self.publish(workflow).errors)

    def test_http_workflow_edit_uses_real_schema_root(self):
        workflow = self.workflow(status="published", current_version=1)
        self.client.force_authenticate(user=None)
        self.client.force_login(self.admin)
        response = self.client.post(
            "/api/graphql",
            {
                "query": 'mutation($id:String!){updatePlatformWorkflow(workflowId:$id,steps:["consent","selfie","decision"]){id status}}',
                "variables": {"id": workflow.public_id},
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertNotIn("errors", payload)
        self.assertEqual(payload["data"]["updatePlatformWorkflow"]["status"], "draft")

    def test_http_template_creation_uses_real_schema_root_and_platform_audit(self):
        from apps.audit.models import AuditEvent
        from apps.templates.models import TemplateCategory

        self.client.force_authenticate(user=None)
        self.client.force_login(self.admin)
        response = self.client.post(
            "/api/graphql",
            {
                "query": 'mutation($category:String!){createPlatformTemplate(name:"Root regression",description:"Synthetic template",category:$category){id status}}',
                "variables": {"category": TemplateCategory.values[0]},
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertNotIn("errors", payload)
        event = AuditEvent.objects.get(
            action="template.created",
            target_id=payload["data"]["createPlatformTemplate"]["id"],
        )
        self.assertIsNone(event.tenant_id)
        self.assertEqual(event.actor_id, self.admin.public_id)

    def test_stale_edit_cannot_reset_the_published_version_counter(self):
        from apps.workflows.serializers import WorkflowSerializer

        workflow = self.workflow()
        stale = Workflow.objects.get(pk=workflow.pk)
        self.assertIsNone(self.publish(workflow).errors)
        request = RequestFactory().patch("/api/v1/workflows/")
        request.user = self.user
        serializer = WorkflowSerializer(
            stale,
            data={"description": "Edited after publication"},
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        workflow.refresh_from_db()
        self.assertEqual(workflow.current_version, 1)
        self.assertEqual(stale.current_version, 1)
        self.assertEqual(workflow.status, "draft")

    def test_stale_partial_settings_edit_preserves_concurrent_changes(self):
        from apps.workflows.serializers import WorkflowSerializer

        workflow = self.workflow(settings_json={"face_match_threshold": 0.85})
        stale = Workflow.objects.get(pk=workflow.pk)
        workflow.settings_json = {"face_match_threshold": 0.94}
        workflow.save(update_fields=["settings_json", "updated_at"])
        request = RequestFactory().patch("/api/v1/workflows/")
        request.user = self.user
        serializer = WorkflowSerializer(
            stale,
            data={"settings": {"media_retention_days": 7}},
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        workflow.refresh_from_db()
        self.assertEqual(workflow.settings_json["face_match_threshold"], 0.94)
        self.assertEqual(workflow.settings_json["media_retention_days"], 7)

    def test_publication_refreshes_the_callers_current_configuration(self):
        from apps.workflows.serializers import publish_workflow

        workflow = self.workflow()
        stale = Workflow.objects.get(pk=workflow.pk)
        workflow.name = "Updated configuration"
        workflow.settings_json = {"face_match_threshold": 0.94}
        workflow.save(update_fields=["name", "settings_json", "updated_at"])
        version = publish_workflow(stale, self.user)
        self.assertEqual(version.workflow_name, "Updated configuration")
        self.assertEqual(stale.name, "Updated configuration")
        self.assertEqual(stale.settings_json["face_match_threshold"], 0.94)

    def test_noop_updates_preserve_publication_and_emit_no_update_audit(self):
        from apps.audit.models import AuditEvent

        queries = [
            (
                "mutation($id:String!){updatePlatformWorkflow(workflowId:$id){id status}}",
                {},
                True,
            ),
            (
                "mutation($id:String!,$settings:JSON!){updatePlatformWorkflow(workflowId:$id,settings:$settings){id status}}",
                {"settings": {}},
                False,
            ),
            (
                'mutation($id:String!){updatePlatformWorkflow(workflowId:$id,steps:["consent","document","decision"]){id status}}',
                {},
                False,
            ),
        ]
        for index, (query, variables, should_error) in enumerate(queries):
            with self.subTest(index=index):
                workflow = self.workflow(
                    name=f"No-op {index}", status="published", current_version=1
                )
                result = self.graphql(query, {"id": workflow.public_id, **variables})
                if should_error:
                    self.assertIsNotNone(result.errors)
                else:
                    self.assertIsNone(result.errors, result.errors)
                workflow.refresh_from_db()
                self.assertEqual(workflow.status, "published")
                self.assertEqual(workflow.current_version, 1)
                self.assertFalse(
                    AuditEvent.objects.filter(
                        action="workflow.updated", target_id=workflow.public_id
                    ).exists()
                )

    def test_invalid_settings_cannot_be_published(self):
        for settings in [
            {"media_retention_days": "thirty"},
            {"face_match_threshold": 2},
            {"required_liveness_level": "unknown"},
        ]:
            with self.subTest(settings=settings):
                workflow = self.workflow(
                    name="Invalid settings " + str(settings), settings_json=settings
                )
                result = self.publish(workflow)
                self.assertIsNotNone(result.errors)
                self.assertFalse(workflow.versions.exists())

    def test_optional_policy_execution_controls_survive_publication(self):
        workflow = self.workflow(
            settings_json={
                "document_authenticity_required": True,
                "document_authenticity_min_confidence": 0.92,
                "external_risk_enabled": True,
                "external_risk_failure_action": "manual_review",
                "external_risk_review_threshold": 80,
            }
        )
        result = self.publish(workflow)
        self.assertIsNone(result.errors, result.errors)
        policy = workflow.versions.get().policy
        self.assertTrue(policy.document_authenticity_required)
        self.assertEqual(float(policy.document_authenticity_min_confidence), 0.92)
        self.assertTrue(policy.external_risk_enabled)
        self.assertEqual(float(policy.external_risk_review_threshold), 80)
        self.assertEqual(policy.external_risk_failure_action, "manual_review")

    def test_policy_approval_setting_survives_publication(self):
        workflow = self.workflow(settings_json={"maker_checker_required": True})
        result = self.publish(workflow)
        self.assertIsNone(result.errors, result.errors)
        self.assertTrue(workflow.versions.get().policy.maker_checker_required)

    def test_same_workflow_name_can_publish_in_distinct_projects(self):
        other_project = Project.objects.create(
            tenant=self.tenant, created_by=self.user, name="Other", slug="other"
        )
        first = self.workflow(name="Shared name")
        second = self.workflow(name="Shared name", project=other_project)
        for workflow in [first, second]:
            result = self.publish(workflow)
            self.assertIsNone(result.errors, result.errors)
        policies = [
            WorkflowVersion.objects.get(workflow=workflow).policy
            for workflow in [first, second]
        ]
        self.assertNotEqual(policies[0].name, policies[1].name)
        self.assertEqual([p.version for p in policies], [1, 1])
