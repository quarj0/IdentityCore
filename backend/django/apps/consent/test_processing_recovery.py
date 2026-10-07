from unittest.mock import patch

from django.test import TestCase
from django.db import transaction

from apps.biometrics import test_finalization_recovery as biometric_fixtures
from apps.consent.services import active_consent, ConsentProofUnavailable
from apps.verifications import test_processing_jobs as document_fixtures
from apps.verifications.models import ProcessingJobStatus, ProcessingJobType
from apps.verifications.processing_jobs import (
    ProcessingJobOwnershipLost, acquire_processing_job, enqueue_processing_job,
    defer_on_consent_proof_unavailable, lock_processing_job_for_finalization,
    heartbeat_processing_job, COMMITTED_PROVIDER_RESULT_RECOVERY,
)
from common.fields import decrypt_tenant_json


class ConsentKeyRecoveryAssertions:
    def test_finalization_outage_refunds_final_attempt_and_fences_old_worker(self):
        queued = enqueue_processing_job(job_type=self.job_type, resource=self.resource)
        queued.attempt_count = queued.max_attempts - 1
        queued.save(update_fields=["attempt_count"])
        old_job = acquire_processing_job(job_type=self.job_type, resource=self.resource)

        def unavailable_proof(value, **kwargs):
            if kwargs.get("purpose") == "consent.proof":
                raise ValueError("synthetic key-provider outage")
            return decrypt_tenant_json(value, **kwargs)

        @defer_on_consent_proof_unavailable
        def finalize():
            with transaction.atomic():
                lock_processing_job_for_finalization(old_job)
                self.fail("No state write may follow unavailable proof")

        with patch("common.fields.decrypt_tenant_json", side_effect=unavailable_proof):
            finalize()
        queued.refresh_from_db()
        self.assertEqual(queued.status, ProcessingJobStatus.QUEUED)
        self.assertEqual(queued.attempt_count, queued.max_attempts - 1)
        self.assertEqual(queued.lease_generation, old_job.lease_generation)
        self.assertEqual(queued.error_code, "consent_key_unavailable")
        self.assertIsNone(queued.completed_at)
        recovered = acquire_processing_job(job_type=self.job_type, resource=self.resource)
        self.assertEqual(recovered.attempt_count, old_job.attempt_count)
        self.assertGreater(recovered.lease_generation, old_job.lease_generation)
        with self.assertRaises(ProcessingJobOwnershipLost):
            heartbeat_processing_job(old_job)
        with transaction.atomic(), self.assertRaises(ProcessingJobOwnershipLost):
            lock_processing_job_for_finalization(old_job)
        heartbeat_processing_job(recovered)
        from apps.providers.models import ProviderCheckStatus, ProviderCheckType
        from apps.providers.services import create_provider_check, execute_provider_route
        check_type = ProviderCheckType.DOCUMENT_QUALITY if self.job_type == ProcessingJobType.IDENTITY_DOCUMENT else ProviderCheckType.LIVENESS
        metadata = {"resource_id": self.resource.public_id}
        check = create_provider_check(verification=self.verification, check_type=check_type,
            status=ProviderCheckStatus.COMPLETED, request_metadata=metadata)
        for status in ("completed", "inconclusive", "failed"):
            with self.subTest(status=status):
                check.normalized_result_json = {"contract_version": "1", "capability": check_type, "status": status, "score": 0.97}
                check.save(update_fields=["normalized_result_json"])
                with patch("apps.providers.services.resolve_provider_chain_for_verification") as route, patch("builtins.print") as operation:
                    result = execute_provider_route(verification=self.verification, check_type=check_type,
                        request_metadata=metadata, operation=operation, processing_job=recovered)
                self.assertEqual(result.provider_check.pk, check.pk)
                self.assertEqual(result.result["status"], status)
                route.assert_not_called()
                operation.assert_not_called()
        for invalid in ({"contract_version": "2", "capability": check_type, "status": "completed"},
                        {"contract_version": "1", "capability": check_type, "status": "unknown"},
                        {"contract_version": "1", "capability": "wrong", "status": "completed"},
                        ["invalid envelope"]):
            with self.subTest(invalid=invalid):
                check.normalized_result_json = invalid
                check.save(update_fields=["normalized_result_json"])
                with patch("apps.providers.services.resolve_provider_chain_for_verification", side_effect=RuntimeError("fresh route required")):
                    with self.assertRaisesRegex(RuntimeError, "fresh route required"):
                        execute_provider_route(verification=self.verification, check_type=check_type,
                            request_metadata=metadata, operation=lambda *args: self.fail("unexpected I/O"), processing_job=recovered)
        with transaction.atomic():
            lock_processing_job_for_finalization(recovered)

    def test_key_outage_keeps_job_retryable_without_consuming_attempts(self):
        job = enqueue_processing_job(job_type=self.job_type, resource=self.resource)
        initial_provider_count = self.verification.provider_checks.count()

        def unavailable_proof(value, **kwargs):
            if kwargs.get("purpose") == "consent.proof":
                raise ValueError("synthetic key-provider outage")
            return decrypt_tenant_json(value, **kwargs)

        with patch("common.fields.decrypt_tenant_json", side_effect=unavailable_proof):
            self.assertIsNone(active_consent(self.verification))
            self.assertIsNone(acquire_processing_job(job_type=self.job_type, resource=self.resource))
        job.refresh_from_db()
        self.assertEqual(job.status, ProcessingJobStatus.QUEUED)
        self.assertEqual(job.attempt_count, 0)
        self.assertIsNone(job.completed_at)
        self.assertEqual(job.error_code, "consent_key_unavailable")
        self.assertEqual(self.verification.provider_checks.count(), initial_provider_count)
        recovered = acquire_processing_job(job_type=self.job_type, resource=self.resource)
        self.assertEqual(recovered.pk, job.pk)
        self.assertEqual(recovered.status, ProcessingJobStatus.PROCESSING)
        self.assertEqual(recovered.attempt_count, 1)
        self.assertEqual(recovered.error_code, "")


class DocumentConsentKeyRecoveryTests(ConsentKeyRecoveryAssertions, TestCase):
    def setUp(self):
        document_fixtures.ProcessingJobRecoveryTests.setUp(self)
        self.job_type = ProcessingJobType.IDENTITY_DOCUMENT
        self.resource = self.identity_document


class BiometricConsentKeyRecoveryTests(ConsentKeyRecoveryAssertions, TestCase):
    def test_acquisition_outage_preserves_queued_provider_recovery_grace(self):
        job = enqueue_processing_job(job_type=self.job_type, resource=self.resource)
        job.attempt_count = job.max_attempts
        job.error_code = COMMITTED_PROVIDER_RESULT_RECOVERY
        job.save(update_fields=["attempt_count", "error_code"])
        with patch("apps.consent.services.active_consent", side_effect=ConsentProofUnavailable):
            self.assertIsNone(acquire_processing_job(job_type=self.job_type, resource=self.resource))
        job.refresh_from_db()
        self.assertEqual(job.error_code, COMMITTED_PROVIDER_RESULT_RECOVERY)
        self.assertEqual(job.attempt_count, job.max_attempts)


    def setUp(self):
        biometric_fixtures.BiometricFinalizationRecoveryTests.setUp(self)
        self.job_type = ProcessingJobType.BIOMETRICS
        self.resource = self.liveness_check
