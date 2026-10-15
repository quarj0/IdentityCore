from django.db import transaction
from django.test import RequestFactory
from rest_framework.test import APITestCase
from apps.accounts.models import PlatformUser
from apps.audit.models import AuditEvent
from apps.templates.models import Template
from config.graphql_schema import schema


class HistoricalTemplateLifecycleTests(APITestCase):
    def setUp(self):
        self.admin = PlatformUser.objects.create_superuser(
            email="template-audit@example.test",
            password="StrongPassword123!",
            status="active",
        )
        self.template = Template.objects.create(
            name="Customer KYC",
            slug="customer-kyc",
            description="Synthetic template",
            category="banking_kyc",
            status="draft",
            version="1.0",
            steps_json=["consent", "document", "decision"],
            required_checks_json=["document"],
            created_by=self.admin,
        )

    def graphql(self, query, variables):
        request = RequestFactory().post("/api/graphql")
        request.user = self.admin
        with transaction.atomic():
            result = schema.execute_sync(
                query, variable_values=variables, context_value={"request": request}
            )
            if result.errors:
                transaction.set_rollback(True)
        return result

    def test_slug_collision_returns_validation_without_database_error(self):
        for query in [
            'mutation{createPlatformTemplate(name:"Customer-KYC",description:"Synthetic",category:"banking_kyc"){id}}',
            'mutation($id:String!){clonePlatformTemplate(templateId:$id,name:"Customer-KYC"){id}}',
        ]:
            with self.subTest(query=query):
                result = self.graphql(query, {"id": self.template.public_id})
                self.assertIsNotNone(result.errors)
                self.assertIn("slug", result.errors[0].message.lower())
                self.assertNotIn("UNIQUE constraint", result.errors[0].message)
                self.assertEqual(Template.objects.count(), 1)

    def test_publish_rejects_invalid_policy_settings(self):
        for settings in [
            {"media_retention_days": "thirty"},
            {"face_match_threshold": 1.2},
            {"manual_review_threshold": 0.95, "face_match_threshold": 0.85},
            {"consent_template_id": "tenant-private-template"},
        ]:
            with self.subTest(settings=settings):
                Template.objects.filter(pk=self.template.pk).update(
                    settings_json=settings, status="draft"
                )
                result = self.graphql(
                    "mutation($id:String!){publishPlatformTemplate(templateId:$id){id status}}",
                    {"id": self.template.public_id},
                )
                self.assertIsNotNone(result.errors)
                self.template.refresh_from_db()
                self.assertEqual(self.template.status, "draft")
                self.assertFalse(
                    AuditEvent.objects.filter(action="template.published").exists()
                )

    def test_new_version_preserves_identity_and_published_source(self):
        self.template.status = "published"
        self.template.save(update_fields=["status"])
        result = self.graphql(
            'mutation($id:String!){createPlatformTemplateVersion(templateId:$id,version:"1.1"){id slug version status}}',
            {"id": self.template.public_id},
        )
        self.assertIsNone(result.errors, result.errors)
        node = result.data["createPlatformTemplateVersion"]
        self.assertEqual(
            (node["slug"], node["version"], node["status"]),
            ("customer-kyc", "1.1", "draft"),
        )
        clone = Template.objects.get(public_id=node["id"])
        self.assertEqual(clone.steps_json, self.template.steps_json)
        self.template.refresh_from_db()
        self.assertEqual(
            (self.template.version, self.template.status), ("1.0", "published")
        )
        self.assertTrue(
            AuditEvent.objects.filter(
                action="template.version_created", target_id=clone.public_id
            ).exists()
        )

    def test_archived_template_cannot_be_edited_or_republished(self):
        self.template.status = "archived"
        self.template.save(update_fields=["status"])
        for query in [
            'mutation($id:String!){updatePlatformTemplate(templateId:$id,name:"Changed"){id}}',
            "mutation($id:String!){publishPlatformTemplate(templateId:$id){id}}",
        ]:
            with self.subTest(query=query):
                result = self.graphql(query, {"id": self.template.public_id})
                self.assertIsNotNone(result.errors)
        self.template.refresh_from_db()
        self.assertEqual(self.template.status, "archived")
        self.assertEqual(self.template.name, "Customer KYC")

    def test_valid_publication_normalizes_settings_and_preserves_controls(self):
        self.template.settings_json = {
            "face_match_threshold": 0.94,
            "maker_checker_required": True,
            "media_retention_days": 14,
        }
        self.template.save(update_fields=["settings_json"])
        result = self.graphql(
            "mutation($id:String!){publishPlatformTemplate(templateId:$id){id status}}",
            {"id": self.template.public_id},
        )
        self.assertIsNone(result.errors, result.errors)
        self.template.refresh_from_db()
        self.assertEqual(self.template.status, "published")
        self.assertEqual(self.template.settings_json["face_match_threshold"], 0.94)
        self.assertTrue(self.template.settings_json["maker_checker_required"])
        self.assertEqual(self.template.settings_json["media_retention_days"], 14)
        self.assertTrue(
            AuditEvent.objects.filter(
                action="template.published", target_id=self.template.public_id
            ).exists()
        )

    def test_new_version_rejects_duplicate_backward_and_invalid_versions(self):
        self.template.status = "published"
        self.template.save(update_fields=["status"])
        for version in ["1.0", "1.0.0", "0.9", "not-a-version", "1.1.2.3"]:
            with self.subTest(version=version):
                result = self.graphql(
                    "mutation($id:String!,$version:String!){createPlatformTemplateVersion(templateId:$id,version:$version){id}}",
                    {"id": self.template.public_id, "version": version},
                )
                self.assertIsNotNone(result.errors)
                self.assertEqual(Template.objects.count(), 1)
        self.assertFalse(
            AuditEvent.objects.filter(action="template.version_created").exists()
        )

    def test_stale_inactive_platform_actor_cannot_publish(self):
        PlatformUser.objects.filter(pk=self.admin.pk).update(status="inactive")
        result = self.graphql(
            "mutation($id:String!){publishPlatformTemplate(templateId:$id){id}}",
            {"id": self.template.public_id},
        )
        self.assertIsNotNone(result.errors)
        self.template.refresh_from_db()
        self.assertEqual(self.template.status, "draft")
        self.assertFalse(
            AuditEvent.objects.filter(action="template.published").exists()
        )

    def test_tenant_bound_platform_actor_retains_valid_publication_audit(self):
        from apps.organizations.models import Organization
        from apps.tenants.models import Tenant
        from apps.audit.services import verify_audit_chain

        organization = Organization.objects.create(
            name="Template admin", slug="template-admin", status="active"
        )
        tenant = Tenant.objects.create(
            organization=organization,
            name="Template admin",
            slug="template-admin",
            status="active",
        )
        self.admin.tenant = tenant
        self.admin.save(update_fields=["tenant"])
        result = self.graphql(
            "mutation($id:String!){publishPlatformTemplate(templateId:$id){id status}}",
            {"id": self.template.public_id},
        )
        self.assertIsNone(result.errors, result.errors)
        event = AuditEvent.objects.get(action="template.published")
        self.assertEqual(event.tenant_id, tenant.pk)
        self.assertEqual(verify_audit_chain(tenant_id=tenant.pk), (True, ""))
