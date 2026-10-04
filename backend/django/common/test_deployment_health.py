import io
import tempfile
from pathlib import Path
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase, override_settings

from common.deployment_health import is_draining


class DrainReadinessTests(SimpleTestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.marker = Path(self.directory.name) / "draining"
        self.settings_override = override_settings(
            DEPLOYMENT_DRAIN_FILE=str(self.marker)
        )
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)

    def test_readiness_rejects_drain_and_dependency_failure_without_details(self):
        with patch("common.deployment_health.dependencies_ready", return_value=True):
            self.assertEqual(self.client.get("/api/v1/ready").status_code, 200)
            self.marker.touch()
            response = self.client.get("/api/v1/ready")
            self.assertEqual(response.status_code, 503)
            self.assertEqual(response["Cache-Control"], "no-store")
            self.assertEqual(response.json()["data"], {"status": "unavailable"})
        self.marker.unlink()
        with patch("common.deployment_health.dependencies_ready", return_value=False):
            self.assertEqual(self.client.get("/api/v1/ready").status_code, 503)
        self.assertEqual(self.client.post("/api/v1/ready").status_code, 405)

    @patch("apps.verifications.management.commands.deployment_drain.app")
    def test_drain_targets_only_named_worker_and_does_not_print_task_payloads(
        self, app
    ):
        worker = "worker@instance"
        inspect = app.control.inspect.return_value
        inspect.ping.return_value = {worker: {"ok": "pong"}}
        inspect.active_queues.return_value = {worker: [{"name": "ai_processing"}]}
        inspect.active.return_value = {worker: []}
        inspect.reserved.return_value = {worker: []}
        inspect.scheduled.return_value = {worker: []}
        app.control.cancel_consumer.return_value = [{worker: {"ok": "cancelled"}}]
        output = io.StringIO()
        call_command("deployment_drain", worker=worker, timeout=1, stdout=output)
        self.assertTrue(is_draining())
        app.control.inspect.assert_called_once_with(destination=[worker], timeout=2)
        app.control.cancel_consumer.assert_called_once_with(
            "ai_processing", destination=[worker], reply=True, timeout=2
        )
        self.assertIn("Instance drained.", output.getvalue())

    @patch("apps.verifications.management.commands.deployment_drain.app")
    def test_task_transition_between_inspections_resets_empty_confirmation(self, app):
        worker = "worker@instance"
        inspect = app.control.inspect.return_value
        inspect.ping.return_value = {worker: {"ok": "pong"}}
        inspect.active_queues.return_value = {worker: []}
        inspect.active.side_effect = [
            {worker: []},
            {worker: [{"args": "private-synthetic-evidence"}]},
            {worker: []},
            {worker: []},
        ]
        inspect.reserved.return_value = {worker: []}
        inspect.scheduled.return_value = {worker: []}
        output = io.StringIO()
        with patch(
            "apps.verifications.management.commands.deployment_drain.time.sleep"
        ):
            call_command("deployment_drain", worker=worker, timeout=1, stdout=output)
        self.assertEqual(inspect.active.call_count, 4)
        self.assertNotIn("private-synthetic-evidence", output.getvalue())

    @patch("apps.verifications.management.commands.deployment_drain.app")
    def test_unacknowledged_worker_retains_marker(self, app):
        app.control.inspect.return_value.ping.return_value = None
        with self.assertRaises(CommandError):
            call_command("deployment_drain", worker="worker@instance", timeout=1)
        self.assertTrue(is_draining())
        app.control.cancel_consumer.assert_not_called()

    @patch("apps.verifications.management.commands.deployment_drain.app")
    def test_timeout_preserves_inflight_work_without_exposing_arguments(self, app):
        worker = "worker@instance"
        inspect = app.control.inspect.return_value
        inspect.ping.return_value = {worker: {"ok": "pong"}}
        inspect.active_queues.return_value = {worker: []}
        inspect.active.return_value = {worker: [{"args": "private-synthetic-evidence"}]}
        inspect.reserved.return_value = {worker: []}
        inspect.scheduled.return_value = {worker: []}
        with patch(
            "apps.verifications.management.commands.deployment_drain.time.monotonic",
            side_effect=[0, 0, 2],
        ), patch("apps.verifications.management.commands.deployment_drain.time.sleep"):
            with self.assertRaises(CommandError) as error:
                call_command("deployment_drain", worker=worker, timeout=1)
        self.assertTrue(is_draining())
        self.assertNotIn("private-synthetic-evidence", str(error.exception))
        app.control.revoke.assert_not_called()

    def test_resume_requires_healthy_dependencies(self):
        self.marker.touch()
        with patch(
            "apps.verifications.management.commands.deployment_drain.dependencies_ready",
            return_value=False,
        ):
            with self.assertRaises(CommandError):
                call_command("deployment_drain", resume=True)
        self.assertTrue(is_draining())
        with patch(
            "apps.verifications.management.commands.deployment_drain.dependencies_ready",
            return_value=True,
        ):
            call_command("deployment_drain", resume=True, stdout=io.StringIO())
        self.assertFalse(is_draining())
