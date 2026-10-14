from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest import skipUnless

from django.db import close_old_connections, connection
from rest_framework.test import APITransactionTestCase

from apps.workflows import tests as workflow_fixtures
from apps.workflows.models import Workflow, WorkflowVersion
from apps.workflows.serializers import publish_workflow


@skipUnless(connection.vendor == "postgresql", "Requires real PostgreSQL row locks")
class WorkflowPublishingRaceTests(APITransactionTestCase):
    setUp = workflow_fixtures.WorkflowAPITests.setUp

    def test_concurrent_publish_allocates_distinct_versions(self):
        for attempt in range(3):
            workflow = Workflow.objects.create(
                tenant=self.tenant,
                project=self.project,
                created_by=self.user,
                name=f"Concurrent publication {attempt}",
                steps_json=["consent", "decision"],
            )
            start = Barrier(2)

            def publish():
                close_old_connections()
                try:
                    with connection.cursor() as cursor:
                        cursor.execute("SET lock_timeout = '10s'")
                        cursor.execute("SET statement_timeout = '15s'")
                    stale = Workflow.objects.get(pk=workflow.pk)
                    start.wait(timeout=10)
                    return publish_workflow(stale, self.user).version
                finally:
                    connection.close()

            with ThreadPoolExecutor(max_workers=2) as pool:
                first, second = pool.submit(publish), pool.submit(publish)
                versions = sorted([first.result(timeout=25), second.result(timeout=25)])
            self.assertEqual(versions, [1, 2])
            workflow.refresh_from_db()
            self.assertEqual(workflow.current_version, 2)
            self.assertEqual(
                list(
                    WorkflowVersion.objects.filter(workflow=workflow)
                    .order_by("version")
                    .values_list("policy__version", flat=True)
                ),
                [1, 2],
            )
