from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest import skipUnless

from django.db import close_old_connections, connection
from django.test import TransactionTestCase
from rest_framework.test import APIClient

from apps.audit.models import AuditEvent
from apps.templates import tests as fixtures
from apps.templates.models import Template
from apps.workflows.models import Workflow


@skipUnless(connection.vendor == "postgresql", "Requires real PostgreSQL locks")
class TemplateInstantiationRaceTests(TransactionTestCase):
    def setUp(self):
        self.client = APIClient()
        fixtures.WorkflowTemplateAPITests.setUp(self)

    def new_template(self, suffix):
        self.template = Template.objects.create(
            name=f"Race {suffix}",
            slug=f"race-{suffix}",
            category=self.template.category,
            status="published",
            version="1.0",
            steps_json=self.template.steps_json,
            settings_json=self.template.settings_json,
            created_by=self.user,
        )

    def race(self, inputs):
        start = Barrier(2)
        template_id = self.template.public_id

        def worker(user, project, name, key):
            close_old_connections()
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SET lock_timeout = '10s'")
                    cursor.execute("SET statement_timeout = '15s'")
                client = APIClient()
                client.force_authenticate(user)
                start.wait(timeout=10)
                response = client.post(
                    f"/api/v1/projects/{project.public_id}/workflows:instantiate",
                    {
                        "template_id": template_id,
                        "template_version": "1.0",
                        "name": name,
                    },
                    format="json",
                    HTTP_IDEMPOTENCY_KEY=key,
                )
                return response.status_code
            finally:
                connection.close()

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(worker, *values) for values in inputs]
            return sorted(f.result(timeout=25) for f in futures)

    def test_overlapping_keys_and_names_are_classified(self):
        for round_number in range(3):
            for variant, first, second, expected in (
                ("replay", ("Same", "same"), ("Same", "same"), [200, 201]),
                ("key-conflict", ("First", "same"), ("Second", "same"), [201, 409]),
                ("name-conflict", ("Same", "first"), ("Same", "second"), [201, 400]),
            ):
                with self.subTest(round=round_number, variant=variant):
                    self.new_template(f"{variant}-{round_number}")
                    # Keys are tenant-wide, so each race gets fresh key material.
                    suffix = f"-{variant}-{round_number}"
                    result = self.race(
                        [
                            (
                                self.user,
                                self.project,
                                first[0] + suffix,
                                first[1] + suffix,
                            ),
                            (
                                self.user,
                                self.project,
                                second[0] + suffix,
                                second[1] + suffix,
                            ),
                        ]
                    )
                    self.assertEqual(result, expected)
                    workflows = Workflow.objects.filter(source_template=self.template)
                    self.assertEqual(workflows.count(), 1)
                    workflow = workflows.get()
                    self.assertEqual(len(workflow.instantiation_request_hash), 64)
                    self.template.refresh_from_db()
                    self.assertEqual(self.template.usage_count, 1)
                    self.assertEqual(self.template.cloned_by_organizations, 1)
                    self.assertEqual(
                        AuditEvent.objects.filter(
                            action="workflow.template_instantiated",
                            target_id=workflow.public_id,
                        ).count(),
                        1,
                    )

    def test_concurrent_tenants_count_distinct_organizations(self):
        from apps.accounts.models import PlatformUser
        from apps.organizations.models import Organization
        from apps.projects.models import Project
        from apps.tenants.models import Tenant

        other_org = Organization.objects.create(
            name="Other adopter", slug="other-adopter", status="active"
        )
        for shared_org in (True, False):
            organization = self.tenant.organization if shared_org else other_org
            suffix = "shared" if shared_org else "different"
            if shared_org:
                user, project = self.user, self.project
            else:
                tenant = Tenant.objects.create(
                    organization=organization, name=suffix, slug=suffix, status="active"
                )
                user = PlatformUser.objects.create_user(
                    email=f"{suffix}@example.com",
                    password="StrongPassword123!",
                    status="active",
                    tenant=tenant,
                )
                project = Project.objects.create(
                    tenant=tenant, created_by=user, name=suffix, slug=suffix
                )
            for round_number in range(3):
                with self.subTest(shared_org=shared_org, round=round_number):
                    self.new_template(f"adoption-{suffix}-{round_number}")
                    key = f"adoption-{suffix}-{round_number}"
                    self.assertEqual(
                        self.race(
                            [
                                (
                                    self.user,
                                    self.project,
                                    key + "-first",
                                    key + "-first",
                                ),
                                (user, project, key + "-second", key + "-second"),
                            ]
                        ),
                        [201, 201],
                    )
                    self.template.refresh_from_db()
                    self.assertEqual(self.template.usage_count, 2)
                    self.assertEqual(
                        self.template.cloned_by_organizations, 1 if shared_org else 2
                    )
