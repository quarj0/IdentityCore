from django.test import SimpleTestCase, Client
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from shared import observability as telemetry
from unittest.mock import patch
from common.responses import get_request_id
from types import SimpleNamespace


class ObservabilityTests(SimpleTestCase):
    def setUp(self):
        self.exporter = InMemorySpanExporter()
        self.provider = TracerProvider()
        self.provider.add_span_processor(SimpleSpanProcessor(self.exporter))
        self.tracer_patch = patch.object(
            telemetry.trace, "get_tracer", return_value=self.provider.get_tracer("test")
        )
        self.tracer_patch.start()
        self.token = telemetry.ENVIRONMENT.set("production")
        self.addCleanup(telemetry.ENVIRONMENT.reset, self.token)
        self.addCleanup(self.tracer_patch.stop)
        self.addCleanup(self.provider.shutdown)

    def test_api_worker_provider_ai_storage_share_trace_without_payloads(self):
        with telemetry.operation("api", "request"):
            headers = {}
            telemetry.inject(headers)
        headers["tracestate"] = "vendor=private-applicant"
        headers["baggage"] = "applicant=private"
        with telemetry.operation("worker", "task", context=telemetry.extract(headers)):
            with telemetry.operation("provider", "invoke"):
                outgoing = {}
                telemetry.inject(outgoing)
                with telemetry.operation(
                    "ai", "request", context=telemetry.extract(outgoing)
                ):
                    with telemetry.operation("storage", "read"):
                        pass
        spans = self.exporter.get_finished_spans()
        self.assertEqual(len(spans), 5)
        self.assertEqual(len({s.context.trace_id for s in spans}), 1)
        self.assertEqual(set(outgoing), {"traceparent"})
        for span in spans:
            self.assertEqual(
                set(span.attributes), {"component", "operation", "environment"}
            )
            self.assertFalse(span.events)
        worker = next(s for s in spans if s.name == "worker.task")
        api = next(s for s in spans if s.name == "api.request")
        self.assertEqual(worker.parent.span_id, api.context.span_id)

    def test_exceptions_export_no_message_or_stack(self):
        with self.assertRaises(ValueError):
            with telemetry.operation("provider", "invoke"):
                raise ValueError("private-document-secret")
        span = self.exporter.get_finished_spans()[0]
        self.assertEqual(span.status.status_code.name, "ERROR")
        self.assertIsNone(span.status.description)
        self.assertFalse(span.events)
        self.assertNotIn("private-document-secret", str(span))

    def test_unknown_environment_and_malformed_context_are_safe(self):
        self.assertEqual(telemetry.environment("tenant-secret"), "unknown")
        with telemetry.operation(
            "api",
            "request",
            context=telemetry.extract(
                {
                    "traceparent": "broken",
                    "baggage": "pii=value",
                    "tracestate": "vendor=private-applicant",
                }
            ),
        ):
            outgoing = {}
            telemetry.inject(outgoing)
        self.assertNotIn("baggage", outgoing)
        self.assertNotIn("tracestate", outgoing)

    def test_request_id_cannot_echo_pii_or_unbounded_values(self):
        for value in ["applicant@example.org", "x" * 65, "a\nb"]:
            request = SimpleNamespace(headers={"X-Request-Id": value})
            self.assertTrue(get_request_id(request).startswith("req_"))
        self.assertEqual(
            get_request_id(SimpleNamespace(headers={"X-Request-Id": "req_safe-123"})),
            "req_safe-123",
        )

    def test_disabled_tracer_omits_trace_header_and_preserves_request_id(self):
        with patch.object(
            telemetry.trace, "get_tracer", return_value=telemetry.trace.NoOpTracer()
        ):
            response = Client().get("/api/v1/health", HTTP_X_REQUEST_ID="req_support")
        self.assertNotIn("X-Trace-Id", response)
        self.assertEqual(response["X-Request-Id"], "req_support")
        self.assertEqual(response.json()["request_id"], "req_support")

    def test_http_boundary_returns_trace_and_request_ids(self):
        response = Client().get("/api/v1/health", HTTP_X_REQUEST_ID="req_safe")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["X-Request-Id"], "req_safe")
        self.assertRegex(response["X-Trace-Id"], r"^[0-9a-f]{32}$")
        self.assertNotEqual(response["X-Trace-Id"], "0" * 32)


from django.test import TestCase
from apps.core.management.commands.collect_operational_metrics import backlog_samples
from apps.organizations.models import Organization
from apps.tenants.models import Tenant
from apps.projects.models import Project
from apps.accounts.models import PlatformUser
from apps.verification_subjects.models import VerificationSubject
from apps.verifications.models import Verification, ProcessingJob
from django.utils import timezone
from datetime import timedelta


class DurableMetricsTests(TestCase):
    def test_queue_age_remains_visible_without_workers_and_environments_are_separate(
        self,
    ):
        organization = Organization.objects.create(
            name="Synthetic", slug="synthetic-metrics"
        )
        tenant = Tenant.objects.create(
            organization=organization, name="Synthetic", slug="synthetic-metrics"
        )
        subject = VerificationSubject.objects.create(tenant=tenant)
        user = PlatformUser.objects.create_user(
            email="synthetic@example.invalid",
            password="SyntheticTest123!",
            tenant=tenant,
        )
        project = Project.objects.create(
            created_by=user,
            tenant=tenant,
            name="Production",
            slug="production",
            environment="production",
        )
        production = Verification.objects.create(
            expires_at=timezone.now() + timedelta(hours=1),
            tenant=tenant,
            organization=organization,
            verification_subject=subject,
            project=project,
        )
        sandbox = Verification.objects.create(
            expires_at=timezone.now() + timedelta(hours=1),
            tenant=tenant,
            organization=organization,
            verification_subject=subject,
        )
        for verification, age in [(production, 600), (sandbox, 1200)]:
            job = ProcessingJob.objects.create(
                lease_expires_at=timezone.now(),
                tenant=tenant,
                verification=verification,
                job_type="biometrics",
                resource_public_id=verification.public_id,
            )
            ProcessingJob.objects.filter(pk=job.pk).update(
                created_at=timezone.now() - timedelta(seconds=age)
            )
        samples = {(queue, env): age for queue, env, age in backlog_samples()}
        self.assertAlmostEqual(samples[("processing", "production")], 600, delta=2)
        self.assertAlmostEqual(samples[("processing", "sandbox")], 1200, delta=2)
        self.assertEqual(samples[("webhooks", "production")], 0)
