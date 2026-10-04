from datetime import timedelta
from unittest.mock import patch

from botocore.exceptions import EndpointConnectionError
from django.db import OperationalError
from django.test import TestCase
from django.utils import timezone
from kombu.exceptions import OperationalError as BrokerUnavailable

from apps.biometrics import test_finalization_recovery as biometric_tests
from apps.biometrics.tasks import process_verification_biometrics_task
from apps.providers.ai_service import AIServiceUnavailable
from apps.providers.models import ProviderCheck
from apps.verifications import test_processing_jobs as processing_tests
from apps.verifications.models import ProcessingJob, VerificationDecision
from apps.verifications.processing_jobs import (
    queue_identity_document_processing,
    recover_stale_processing_jobs,
)

SENTINEL = "synthetic-private-evidence-do-not-expose"
LIVENESS = {
    "status": "completed",
    "score": 0.97,
    "confidence_level": "high",
    "passed": True,
    "model_name": "synthetic",
    "model_version": "v1",
    "metrics": {"face_count": 1, "avg_detection_confidence": 0.98},
}
FACE = {
    "status": "completed",
    "match_score": 0.96,
    "confidence_level": "high",
    "matched": True,
    "threshold_used": 0.85,
    "model_name": "synthetic",
    "model_version": "v1",
}


class BrokerAndDatabaseOutageTests(TestCase):
    setUp = processing_tests.ProcessingJobRecoveryTests.setUp

    def test_broker_outage_preserves_durable_job_and_recovers_once(self):
        with patch(
            "apps.identity_documents.tasks.process_identity_document_task.delay",
            side_effect=BrokerUnavailable(SENTINEL),
        ):
            with self.assertLogs(
                "apps.verifications.processing_jobs", level="WARNING"
            ) as logs:
                with self.captureOnCommitCallbacks(execute=True):
                    job = queue_identity_document_processing(self.identity_document)
        self.assertNotIn(SENTINEL, str(logs.output))
        job.refresh_from_db()
        self.assertEqual(job.status, "queued")
        self.assertEqual(job.attempt_count, 0)
        self.assertEqual(job.error_code, "dispatch_unavailable")
        self.assertLessEqual(job.lease_expires_at, timezone.now())
        with patch(
            "apps.identity_documents.tasks.process_identity_document_task.delay"
        ) as publish:
            self.assertEqual(recover_stale_processing_jobs(limit=10), (1, 0))
            self.assertEqual(recover_stale_processing_jobs(limit=10), (0, 0))
            publish.assert_called_once_with(self.identity_document.public_id)
        job.refresh_from_db()
        self.assertEqual(job.error_code, "")
        self.assertEqual(ProcessingJob.objects.count(), 1)
        self.assertFalse(VerificationDecision.objects.exists())

    def test_database_failure_rolls_back_job_creation_and_retry_creates_one_job(self):
        with patch.object(
            ProcessingJob, "save", side_effect=OperationalError(SENTINEL)
        ):
            with patch(
                "apps.identity_documents.tasks.process_identity_document_task.delay"
            ) as publish:
                with self.assertRaises(OperationalError):
                    queue_identity_document_processing(self.identity_document)
                publish.assert_not_called()
        self.assertFalse(ProcessingJob.objects.exists())
        with patch(
            "apps.identity_documents.tasks.process_identity_document_task.delay"
        ):
            with self.captureOnCommitCallbacks(execute=True):
                first = queue_identity_document_processing(self.identity_document)
                second = queue_identity_document_processing(self.identity_document)
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(ProcessingJob.objects.count(), 1)
        self.assertFalse(VerificationDecision.objects.exists())


class StorageAndAIOutageTests(TestCase):
    setUp = biometric_tests.BiometricFinalizationRecoveryTests.setUp

    def test_storage_outage_retries_finalization_without_repeating_biometrics(self):
        with patch(
            "apps.biometrics.tasks.run_liveness_check", return_value=LIVENESS
        ) as liveness, patch(
            "apps.biometrics.tasks.run_face_compare", return_value=FACE
        ) as face, patch(
            "apps.biometrics.tasks.promote_upload_to_media_by_storage_key",
            side_effect=EndpointConnectionError(
                endpoint_url="https://storage.example.invalid"
            ),
        ) as promote, patch(
            "apps.biometrics.tasks.queue_webhook_events", return_value=[]
        ), patch(
            "apps.biometrics.tasks.queue_verification_status_notifications"
        ), patch(
            "apps.biometrics.tasks.ensure_verification_evidence_report"
        ):
            with self.assertRaises(EndpointConnectionError):
                process_verification_biometrics_task(self.liveness_check.public_id)
            self.assertFalse(VerificationDecision.objects.exists())
            self.assertEqual(
                self.liveness_check.__class__.objects.get(
                    pk=self.liveness_check.pk
                ).status,
                "passed",
            )
            job = ProcessingJob.objects.get(
                resource_public_id=self.liveness_check.public_id
            )
            ProcessingJob.objects.filter(pk=job.pk).update(
                lease_expires_at=timezone.now() - timedelta(seconds=1)
            )
            promote.side_effect = None
            liveness.reset_mock()
            face.reset_mock()
            self.assertEqual(
                process_verification_biometrics_task(self.liveness_check.public_id),
                "verified",
            )
            liveness.assert_not_called()
            face.assert_not_called()
            self.assertEqual(
                process_verification_biometrics_task(self.liveness_check.public_id),
                "verified",
            )
        self.assertEqual(VerificationDecision.objects.count(), 1)
        job.refresh_from_db()
        self.assertEqual(job.status, "completed")

    def test_ai_outage_routes_to_review_once_with_safe_error_evidence(self):
        with patch(
            "apps.biometrics.tasks.run_liveness_check",
            side_effect=AIServiceUnavailable(SENTINEL),
        ), patch("apps.biometrics.tasks.promote_upload_to_media_by_storage_key"), patch(
            "apps.biometrics.tasks.queue_webhook_events", return_value=[]
        ), patch(
            "apps.biometrics.tasks.queue_verification_status_notifications"
        ), patch(
            "apps.biometrics.tasks.ensure_verification_evidence_report"
        ):
            result = process_verification_biometrics_task(self.liveness_check.public_id)
            self.assertEqual(result, "manual_review_required")
            self.assertEqual(
                process_verification_biometrics_task(self.liveness_check.public_id),
                result,
            )
        self.assertEqual(VerificationDecision.objects.count(), 1)
        decision = VerificationDecision.objects.get()
        self.assertEqual(decision.reason_code, "biometric_provider_unavailable")
        self.assertNotIn(SENTINEL, str(decision.evidence_summary_json))
        self.assertNotIn(
            SENTINEL,
            str(list(ProviderCheck.objects.values_list("error_message", flat=True))),
        )
        self.assertEqual(ProcessingJob.objects.get().status, "completed")


class ExternalProviderOutageTests(TestCase):
    from apps.providers import tests as _provider_tests

    setUp = _provider_tests.ProviderRouteTests.setUp
    create_route = _provider_tests.ProviderRouteTests.create_route
    create_processing_verification = (
        _provider_tests.ProviderRouteTests.create_processing_verification
    )

    def test_provider_outage_falls_back_and_circuit_recovers_without_secret_errors(
        self,
    ):
        from apps.providers.ai_service import AIServiceUnavailable
        from apps.providers.models import ProviderCheckType, ProviderCircuitState
        from apps.providers.services import execute_provider_route

        route = self.create_route(
            route_key="outage-injection",
            providers=self.providers[:2],
            max_attempts_per_provider=2,
            circuit_failure_threshold=1,
            circuit_recovery_seconds=30,
        )
        case = self.create_processing_verification()
        calls = []

        def operation(provider, timeout_seconds):
            calls.append(provider.pk)
            if provider == self.providers[0]:
                raise AIServiceUnavailable(
                    SENTINEL,
                    error_code="provider_timeout",
                    provider_check_status="timeout",
                )
            return {"status": "completed"}

        result = execute_provider_route(
            verification=case,
            check_type=ProviderCheckType.DOCUMENT_OCR,
            operation=operation,
        )
        self.assertEqual(result.provider_check.provider, self.providers[1])
        self.assertGreaterEqual(calls.count(self.providers[0].pk), 1)
        self.assertLessEqual(calls.count(self.providers[0].pk), 2)
        self.assertNotIn(
            SENTINEL,
            str(list(ProviderCheck.objects.values_list("error_message", flat=True))),
        )
        circuit = ProviderCircuitState.objects.get(
            route_step__route=route, route_step__provider=self.providers[0]
        )
        self.assertEqual(circuit.status, "open")
        calls.clear()
        execute_provider_route(
            verification=case,
            check_type=ProviderCheckType.DOCUMENT_OCR,
            operation=operation,
        )
        self.assertNotIn(self.providers[0].pk, calls)
        circuit.retry_after = timezone.now() - timedelta(seconds=1)
        circuit.save(update_fields=["retry_after"])
        recovered = execute_provider_route(
            verification=case,
            check_type=ProviderCheckType.DOCUMENT_OCR,
            operation=lambda provider, timeout: {"status": "completed"},
        )
        self.assertEqual(recovered.provider_check.provider, self.providers[0])
        circuit.refresh_from_db()
        self.assertEqual(circuit.status, "closed")
        self.assertEqual(circuit.consecutive_failures, 0)
        self.assertFalse(VerificationDecision.objects.exists())
