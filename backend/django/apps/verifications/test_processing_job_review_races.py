from datetime import timedelta

from django.db import transaction
from django.test import TestCase, override_settings
from django.utils import timezone

from apps.biometrics.models import LivenessCheck, LivenessCheckStatus, SelfieCapture
from apps.organizations.models import Organization
from apps.providers.models import (
    ProviderAttemptOutcome,
    ProviderCheck,
    ProviderCheckStatus,
    ProviderCheckType,
    ProviderExecutionAttempt,
)
from apps.providers.services import create_provider_check, get_or_create_system_provider
from apps.tenants.models import Tenant
from apps.verification_subjects.models import VerificationSubject
from apps.verifications.models import (
    ProcessingJob,
    ProcessingJobStatus,
    ProcessingJobType,
    Verification,
    VerificationDecision,
    VerificationDecisionType,
    VerificationStatus,
)
from apps.verifications.processing_jobs import (
    COMMITTED_PROVIDER_RESULT_RECOVERY,
    ProcessingJobOwnershipLost,
    acquire_processing_job,
    complete_processing_job,
    recover_stale_processing_jobs,
)


@override_settings(PROCESSING_JOB_LEASE_SECONDS=300, PROCESSING_JOB_MAX_ATTEMPTS=3)
class ProcessingJobReviewRaceTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            name="Processing Race Review", slug="processing-race-review"
        )
        self.tenant = Tenant.objects.create(
            organization=self.organization,
            name="Processing Race Tenant",
            slug="processing-race-tenant",
            status="active",
        )
        self.subject = VerificationSubject.objects.create(
            tenant=self.tenant,
            full_name="Processing Race Subject",
        )

    def _verification(self, *, status=VerificationStatus.PROCESSING):
        return Verification.objects.create(
            tenant=self.tenant,
            organization=self.organization,
            verification_subject=self.subject,
            purpose="Processing race regression",
            status=status,
            expires_at=timezone.now() + timedelta(hours=1),
        )

    def _liveness(self, verification, suffix):
        selfie = SelfieCapture.objects.create(
            tenant=self.tenant,
            verification=verification,
            verification_subject=self.subject,
            storage_key=f"uploads/selfies/{suffix}",
            capture_type="image",
            captured_at=timezone.now(),
        )
        return LivenessCheck.objects.create(
            tenant=self.tenant,
            verification=verification,
            selfie_capture=selfie,
            liveness_type="passive",
            status=LivenessCheckStatus.INCONCLUSIVE,
            checked_at=timezone.now(),
        )

    def _job(self, verification, liveness, *, status, attempt_count=1):
        return ProcessingJob.objects.create(
            tenant=self.tenant,
            verification=verification,
            job_type=ProcessingJobType.BIOMETRICS,
            resource_public_id=liveness.public_id,
            status=status,
            attempt_count=attempt_count,
            max_attempts=3,
            heartbeat_at=timezone.now() - timedelta(minutes=10),
            lease_expires_at=timezone.now() - timedelta(minutes=5),
        )

    def test_exhausted_job_aborts_surrounding_finalization_transaction(self):
        verification = self._verification()
        liveness = self._liveness(verification, "ownership-lost")
        job = self._job(
            verification,
            liveness,
            status=ProcessingJobStatus.EXHAUSTED,
            attempt_count=3,
        )
        job.error_code = "processing_retries_exhausted"
        job.save(update_fields=["error_code", "updated_at"])

        with self.assertRaises(ProcessingJobOwnershipLost):
            with transaction.atomic():
                verification.status = VerificationStatus.VERIFIED
                verification.save(update_fields=["status", "updated_at"])
                complete_processing_job(job)

        verification.refresh_from_db()
        job.refresh_from_db()
        self.assertEqual(verification.status, VerificationStatus.PROCESSING)
        self.assertEqual(job.status, ProcessingJobStatus.EXHAUSTED)
        self.assertEqual(job.error_code, "processing_retries_exhausted")

    def test_route_exhaustion_repairs_only_the_originating_biometric_job(self):
        verification = self._verification(
            status=VerificationStatus.MANUAL_REVIEW_REQUIRED
        )
        origin = self._liveness(verification, "route-origin")
        unrelated = self._liveness(verification, "route-unrelated")
        origin_job = self._job(
            verification, origin, status=ProcessingJobStatus.PROCESSING
        )
        unrelated_job = self._job(
            verification, unrelated, status=ProcessingJobStatus.PROCESSING
        )

        now = timezone.now()
        provider = get_or_create_system_provider(ProviderCheckType.LIVENESS)
        provider_check = ProviderCheck.objects.create(
            tenant=self.tenant,
            verification=verification,
            provider=provider,
            check_type=ProviderCheckType.LIVENESS,
            status=ProviderCheckStatus.FAILED,
            request_metadata_json={"liveness_check_id": origin.public_id},
            error_code="provider_timeout",
            error_message="timeout",
            started_at=now - timedelta(seconds=2),
            completed_at=now - timedelta(seconds=1),
        )
        ProviderExecutionAttempt.objects.create(
            execution_id="pex_route_origin",
            provider_check=provider_check,
            sequence=1,
            provider_attempt=1,
            outcome=ProviderAttemptOutcome.FAILED,
            error_code="provider_timeout",
            retryable=False,
            fallback_reason="route_exhausted",
            timeout_seconds=30,
            started_at=now - timedelta(seconds=2),
            completed_at=now - timedelta(seconds=1),
        )
        VerificationDecision.objects.create(
            tenant=self.tenant,
            verification=verification,
            decision=VerificationStatus.MANUAL_REVIEW_REQUIRED,
            decision_type=VerificationDecisionType.SYSTEM,
            reason_code="provider_route_exhausted",
            reason_detail="Provider route exhausted.",
            evidence_summary_json={
                "capability": ProviderCheckType.LIVENESS,
                "provider_route_id": "",
                "attempt_count": 1,
                "error_codes": ["provider_timeout"],
            },
            decided_at=now,
        )

        complete_processing_job(unrelated_job)
        unrelated.refresh_from_db()
        self.assertEqual(unrelated.status, LivenessCheckStatus.INCONCLUSIVE)

        complete_processing_job(origin_job)
        origin.refresh_from_db()
        self.assertEqual(origin.status, LivenessCheckStatus.ERROR)
        self.assertEqual(origin.failure_reason, "provider_route_exhausted")

    def test_max_attempt_sweep_grants_one_resume_for_committed_provider_result(self):
        verification = self._verification()
        liveness = self._liveness(verification, "committed-provider-result")
        completed_check = create_provider_check(
            verification=verification,
            check_type=ProviderCheckType.LIVENESS,
            status=ProviderCheckStatus.COMPLETED,
            request_metadata={"liveness_check_id": liveness.public_id},
            normalized_result={
                "passed": True,
                "score": 0.99,
                "metrics": {"face_count": 1, "avg_detection_confidence": 0.99},
                "model_name": "test-liveness",
                "model_version": "1",
            },
        )
        job = self._job(
            verification,
            liveness,
            status=ProcessingJobStatus.PROCESSING,
            attempt_count=3,
        )

        from unittest.mock import patch

        with patch(
            "apps.verifications.processing_jobs.dispatch_processing_job",
            return_value=True,
        ) as dispatch:
            recovered, exhausted = recover_stale_processing_jobs(limit=10)

        liveness.refresh_from_db()
        job.refresh_from_db()
        self.assertEqual((recovered, exhausted), (1, 0))
        self.assertEqual(liveness.provider_check_id, completed_check.public_id)
        self.assertEqual(job.status, ProcessingJobStatus.QUEUED)
        self.assertEqual(job.attempt_count, 3)
        self.assertEqual(job.error_code, COMMITTED_PROVIDER_RESULT_RECOVERY)
        dispatch.assert_called_once_with(job.public_id)

        acquired = acquire_processing_job(
            job_type=ProcessingJobType.BIOMETRICS,
            resource=liveness,
        )
        self.assertIsNotNone(acquired)
        acquired.refresh_from_db()
        self.assertEqual(acquired.status, ProcessingJobStatus.PROCESSING)
        self.assertEqual(acquired.attempt_count, 3)
        self.assertEqual(acquired.error_code, COMMITTED_PROVIDER_RESULT_RECOVERY)
