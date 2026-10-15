from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest import skipUnless
from django.db import close_old_connections, connection
from django.test import RequestFactory
from rest_framework.test import APITransactionTestCase
from apps.accounts.models import PlatformUser
from apps.audit.models import AuditEvent
from apps.audit.services import verify_audit_chain
from apps.templates.models import Template
from config.graphql_schema import schema


@skipUnless(
    connection.vendor == "postgresql", "Requires real PostgreSQL transaction locks"
)
class TemplateLifecycleRaceTests(APITransactionTestCase):
    def test_concurrent_same_version_returns_one_draft_and_one_validation_error(self):
        admin = PlatformUser.objects.create_superuser(
            email="template-race@example.test",
            password="StrongPassword123!",
            status="active",
        )
        for attempt in range(3):
            source = Template.objects.create(
                name=f"Template {attempt}",
                slug=f"template-race-{attempt}",
                category="banking_kyc",
                status="published",
                version="1.0",
                steps_json=["consent", "decision"],
                required_checks_json=["document"],
                created_by=admin,
            )
            start = Barrier(2)

            def create_version():
                close_old_connections()
                try:
                    with connection.cursor() as cursor:
                        cursor.execute("SET lock_timeout = '10s'")
                        cursor.execute("SET statement_timeout = '15s'")
                    request = RequestFactory().post("/api/graphql")
                    request.user = PlatformUser.objects.get(pk=admin.pk)
                    start.wait(timeout=10)
                    result = schema.execute_sync(
                        'mutation($id:String!){createPlatformTemplateVersion(templateId:$id,version:"1.1"){id}}',
                        variable_values={"id": source.public_id},
                        context_value={"request": request},
                    )
                    return [error.message for error in result.errors or []]
                finally:
                    connection.close()

            with ThreadPoolExecutor(max_workers=2) as pool:
                first, second = pool.submit(create_version), pool.submit(create_version)
                results = [first.result(timeout=25), second.result(timeout=25)]
            self.assertEqual(sorted(len(errors) for errors in results), [0, 1])
            self.assertIn(
                "slug and version already exists",
                next(errors[0] for errors in results if errors),
            )
            self.assertEqual(
                Template.objects.filter(
                    slug=source.slug, version="1.1", status="draft"
                ).count(),
                1,
            )
            self.assertEqual(
                AuditEvent.objects.filter(action="template.version_created").count(),
                attempt + 1,
            )
            self.assertEqual(verify_audit_chain(tenant_id=None), (True, ""))
