from datetime import timedelta
from unittest.mock import Mock

from django.test import TestCase
from django.utils import timezone

from apps.providers import tests as fixtures
from apps.providers.models import (
    ProviderCheck,
    ProviderCheckStatus,
    ProviderCheckType,
    ProviderCircuitState,
    ProviderCircuitStatus,
    ProviderExecutionAttempt,
)
from apps.providers.services import (
    create_provider_check,
    execute_provider_route,
    invoke_provider_check,
    redact_provider_metadata,
)
from apps.verifications.models import ProcessingJob
from apps.verifications.processing_jobs import ProcessingJobOwnershipLost
from apps.verifications.result_contract import _serialize_check_provenance


class HistoricalProviderAuditTests(TestCase):
    def setUp(self):
        self.fixture = fixtures.ProviderRouteTests()
        self.fixture.setUp()
        self.verification = self.fixture.create_processing_verification()
        self.route = self.fixture.create_route(
            route_key="historical-audit", providers=[self.fixture.providers[0]]
        )

    def test_credential_aliases_and_evidence_locations_are_not_telemetry(self):
        for key in (
            "client_secret",
            "shared_token",
            "signing_key",
            "storage_key",
            "privateKey",
            "aws_secret_access_key",
        ):
            with self.subTest(key=key):
                self.assertEqual(
                    redact_provider_metadata({"nested": [{key: "private-value"}]}),
                    {"nested": [{key: "[REDACTED]"}]},
                )
        self.assertEqual(
            redact_provider_metadata(
                {"capture_id": "cap_synthetic", "status": "completed"}
            ),
            {"capture_id": "cap_synthetic", "status": "completed"},
        )

    def test_reusing_bootstrap_check_preserves_distinct_invocation_records(self):
        initial = create_provider_check(
            verification=self.verification,
            check_type=ProviderCheckType.DOCUMENT_OCR,
            status=ProviderCheckStatus.PENDING,
            request_metadata={"document_type": "passport"},
        )
        first = execute_provider_route(
            verification=self.verification,
            check_type=ProviderCheckType.DOCUMENT_OCR,
            initial_provider_check=initial,
            operation=lambda *_: {"status": "completed", "confidence_score": 0.91},
        )
        # Reuse the same Python object, including any cached absent reverse relation.
        second = execute_provider_route(
            verification=self.verification,
            check_type=ProviderCheckType.DOCUMENT_OCR,
            initial_provider_check=initial,
            operation=lambda *_: {"status": "completed", "confidence_score": 0.82},
        )
        self.assertNotEqual(first.provider_check.pk, second.provider_check.pk)
        self.assertEqual(
            ProviderExecutionAttempt.objects.filter(
                provider_check__verification=self.verification
            ).count(),
            2,
        )
        first.provider_check.refresh_from_db()
        self.assertEqual(
            first.provider_check.normalized_result_json["confidence_score"], 0.91
        )
        self.assertEqual(
            first.provider_check.request_metadata_json["document_type"], "passport"
        )

    def test_retry_clears_terminal_fields_before_calling_provider(self):
        check = create_provider_check(
            verification=self.verification,
            check_type=ProviderCheckType.DOCUMENT_OCR,
            status=ProviderCheckStatus.PENDING,
        )
        check.status = ProviderCheckStatus.FAILED
        check.completed_at = timezone.now()
        check.duration_ms = 99
        check.error_code = "provider_timeout"
        check.error_message = "safe timeout"
        check.response_metadata_json = {"outcome": "failed"}
        check.normalized_result_json = {"status": "failed"}
        check.save()

        def operation():
            current = ProviderCheck.objects.get(pk=check.pk)
            self.assertEqual(current.status, ProviderCheckStatus.PROCESSING)
            self.assertIsNone(current.completed_at)
            self.assertIsNone(current.duration_ms)
            self.assertEqual(current.error_code, "")
            self.assertEqual(current.error_message, "")
            self.assertEqual(current.response_metadata_json, {})
            self.assertEqual(current.normalized_result_json, {})
            return {"status": "completed", "confidence_score": 0.91}

        invoke_provider_check(
            provider_check=check, operation=operation, operation_kwargs={}
        )

    def test_stale_owner_cannot_reserve_half_open_probe(self):
        step = self.route.steps.get()
        before = timezone.now() - timedelta(seconds=1)
        circuit = ProviderCircuitState.objects.create(
            route_step=step, status=ProviderCircuitStatus.OPEN, retry_after=before
        )
        job = ProcessingJob.objects.create(
            tenant=self.verification.tenant,
            verification=self.verification,
            job_type="identity_document",
            resource_public_id="doc_synthetic",
            status="processing",
            attempt_count=1,
            lease_expires_at=timezone.now() + timedelta(minutes=5),
        )
        ProcessingJob.objects.filter(pk=job.pk).update(attempt_count=2)
        operation = Mock(return_value={"status": "completed", "confidence_score": 0.91})
        with self.assertRaises(ProcessingJobOwnershipLost):
            execute_provider_route(
                verification=self.verification,
                check_type=ProviderCheckType.DOCUMENT_OCR,
                operation=operation,
                processing_job=job,
            )
        circuit.refresh_from_db()
        self.assertEqual(circuit.status, ProviderCircuitStatus.OPEN)
        self.assertEqual(circuit.retry_after, before)
        operation.assert_not_called()
        self.assertFalse(ProviderExecutionAttempt.objects.exists())

    def test_invalid_liveness_evidence_is_failed_inside_provider_boundary(self):
        from apps.providers.adapters import ProviderContractError
        from apps.providers.services import get_or_create_system_provider

        provider = get_or_create_system_provider(ProviderCheckType.LIVENESS)
        check = ProviderCheck.objects.create(
            tenant=self.verification.tenant,
            verification=self.verification,
            provider=provider,
            check_type=ProviderCheckType.LIVENESS,
            status=ProviderCheckStatus.PENDING,
            started_at=timezone.now(),
        )
        with self.assertRaises(ProviderContractError):
            invoke_provider_check(
                provider_check=check,
                operation=lambda: {"status": "completed", "passed": True},
                operation_kwargs={},
            )
        check.refresh_from_db()
        self.assertEqual(check.status, ProviderCheckStatus.FAILED)
        self.assertEqual(check.response_metadata_json["outcome"], "failed")
        self.assertEqual(check.normalized_result_json["status"], "failed")
        self.assertFalse(check.normalized_result_json["error"]["retryable"])

    def test_public_provenance_prefers_nested_workflow_outcome(self):
        check = create_provider_check(
            verification=self.verification,
            check_type=ProviderCheckType.DOCUMENT_OCR,
            status=ProviderCheckStatus.COMPLETED,
            normalized_result={
                "contract_version": "1",
                "status": "completed",
                "workflow_result": {"status": "validated"},
            },
        )
        self.assertEqual(_serialize_check_provenance(check)["status"], "validated")
        check.normalized_result_json["workflow_result"] = {
            "status": "private-unknown-status"
        }
        self.assertEqual(_serialize_check_provenance(check)["status"], "completed")
