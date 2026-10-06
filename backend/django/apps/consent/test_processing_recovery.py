from unittest.mock import patch

from django.test import TestCase

from apps.biometrics import test_finalization_recovery as biometric_fixtures
from apps.consent.services import active_consent
from apps.verifications import test_processing_jobs as document_fixtures
from apps.verifications.models import ProcessingJobStatus, ProcessingJobType
from apps.verifications.processing_jobs import acquire_processing_job, enqueue_processing_job
from common.fields import decrypt_tenant_json


class ConsentKeyRecoveryAssertions:
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
    def setUp(self):
        biometric_fixtures.BiometricFinalizationRecoveryTests.setUp(self)
        self.job_type = ProcessingJobType.BIOMETRICS
        self.resource = self.liveness_check
