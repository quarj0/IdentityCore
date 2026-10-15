from datetime import timedelta
from unittest.mock import patch

from django.db import transaction
from django.test import TestCase
from django.utils import timezone

from apps.biometrics.models import FaceMatch, FaceMatchStatus, LivenessCheckStatus
from apps.identity_documents.models import IdentityDocument
from apps.providers.models import ProviderCheckStatus, ProviderCheckType
from apps.providers.services import create_provider_check
from apps.verifications import test_processing_job_review_races as fixtures
from apps.verifications.models import (
    ProcessingJob,
    ProcessingJobStatus,
    ProcessingJobType,
    VerificationDecision,
    VerificationStatus,
)
from apps.verifications.processing_jobs import (
    COMMITTED_PROVIDER_RESULT_RECOVERY,
    COMMITTED_PROVIDER_RESULT_RECOVERY_CONSUMED,
    ProcessingJobOwnershipLost,
    _repair_biometric_provider_check_links,
    acquire_processing_job,
    complete_processing_job,
    defer_processing_job,
    exhaust_processing_job,
    heartbeat_processing_job,
    recover_stale_processing_jobs,
)


class HistoricalProcessingInvariantTests(TestCase):
    setUp = fixtures.ProcessingJobReviewRaceTests.setUp
    _verification = fixtures.ProcessingJobReviewRaceTests._verification
    _liveness = fixtures.ProcessingJobReviewRaceTests._liveness
    _job = fixtures.ProcessingJobReviewRaceTests._job

    def committed_liveness(self, resource, **overrides):
        fields = dict(
            verification=resource.verification,
            check_type=ProviderCheckType.LIVENESS,
            status=ProviderCheckStatus.COMPLETED,
            request_metadata={"liveness_check_id": resource.public_id},
            normalized_result={
                "capability": ProviderCheckType.LIVENESS,
                "passed": True,
                "score": 0.99,
            },
        )
        fields.update(overrides)
        return create_provider_check(**fields)

    def test_liveness_result_without_final_decision_is_redispatched(self):
        verification = self._verification()
        resource = self._liveness(verification, "unfinished-decision")
        resource.status = LivenessCheckStatus.PASSED
        resource.save(update_fields=["status", "updated_at"])
        job = self._job(verification, resource, status=ProcessingJobStatus.PROCESSING)
        with patch(
            "apps.biometrics.tasks.process_verification_biometrics_task.delay"
        ) as publish:
            self.assertEqual(recover_stale_processing_jobs(), (1, 0))
        job.refresh_from_db()
        self.assertEqual(job.status, ProcessingJobStatus.QUEUED)
        publish.assert_called_once_with(resource.public_id)

    def test_failed_broker_preserves_grace_until_successful_worker_acquisition(self):
        verification = self._verification()
        resource = self._liveness(verification, "broker-grace")
        self.committed_liveness(resource)
        job = self._job(
            verification,
            resource,
            status=ProcessingJobStatus.PROCESSING,
            attempt_count=3,
        )
        with patch(
            "apps.biometrics.tasks.process_verification_biometrics_task.delay",
            side_effect=RuntimeError("synthetic broker outage"),
        ):
            self.assertEqual(recover_stale_processing_jobs(), (0, 0))
        job.refresh_from_db()
        self.assertEqual(job.error_code, COMMITTED_PROVIDER_RESULT_RECOVERY)
        self.assertEqual(job.attempt_count, 3)
        with patch(
            "apps.biometrics.tasks.process_verification_biometrics_task.delay"
        ) as publish:
            self.assertEqual(recover_stale_processing_jobs(), (1, 0))
        publish.assert_called_once_with(resource.public_id)
        job.refresh_from_db()
        self.assertEqual(job.error_code, COMMITTED_PROVIDER_RESULT_RECOVERY)
        owner = acquire_processing_job(
            job_type=ProcessingJobType.BIOMETRICS, resource=resource
        )
        self.assertIsNotNone(owner)
        self.assertEqual(owner.attempt_count, 4)
        self.assertEqual(owner.error_code, COMMITTED_PROVIDER_RESULT_RECOVERY_CONSUMED)

    def test_already_resolved_row_retains_one_finalization_grace(self):
        verification = self._verification()
        resource = self._liveness(verification, "resolved-grace")
        resource.provider_check_id = self.committed_liveness(resource).public_id
        resource.status = LivenessCheckStatus.PASSED
        resource.save(update_fields=["provider_check_id", "status", "updated_at"])
        job = self._job(
            verification,
            resource,
            status=ProcessingJobStatus.PROCESSING,
            attempt_count=3,
        )
        with patch("apps.biometrics.tasks.process_verification_biometrics_task.delay"):
            self.assertEqual(recover_stale_processing_jobs(), (1, 0))
        job.refresh_from_db()
        self.assertEqual(job.error_code, COMMITTED_PROVIDER_RESULT_RECOVERY)
        resource.refresh_from_db()
        self.assertEqual(resource.status, LivenessCheckStatus.PASSED)

    def test_recovery_requires_every_pending_biometric_stage(self):
        verification = self._verification()
        resource = self._liveness(verification, "pending-face")
        resource.provider_check_id = self.committed_liveness(resource).public_id
        resource.save(update_fields=["provider_check_id", "updated_at"])
        document = IdentityDocument.objects.create(
            tenant=self.tenant,
            verification=verification,
            verification_subject=self.subject,
            document_type_id="national_id",
            country_profile_id="GH",
        )
        face = FaceMatch.objects.create(
            tenant=self.tenant,
            verification=verification,
            selfie_capture=resource.selfie_capture,
            identity_document=document,
            status=FaceMatchStatus.INCONCLUSIVE,
            matched_at=timezone.now(),
        )
        self.assertFalse(_repair_biometric_provider_check_links(resource))
        face.provider_check_id = resource.provider_check_id
        face.save(update_fields=["provider_check_id", "updated_at"])
        self.assertFalse(_repair_biometric_provider_check_links(resource))
        face.provider_check_id = create_provider_check(
            verification=verification,
            check_type=ProviderCheckType.FACE_MATCH,
            status=ProviderCheckStatus.COMPLETED,
            request_metadata={"face_match_id": face.public_id},
            normalized_result={
                "capability": ProviderCheckType.FACE_MATCH,
                "matched": True,
            },
        ).public_id
        face.save(update_fields=["provider_check_id", "updated_at"])
        self.assertTrue(_repair_biometric_provider_check_links(resource))

    def test_wrong_capability_or_resource_cannot_grant_grace(self):
        verification = self._verification()
        resource = self._liveness(verification, "wrong-evidence")
        for overrides in (
            {"request_metadata": {"liveness_check_id": "liv_other"}},
            {
                "normalized_result": {
                    "capability": ProviderCheckType.FACE_MATCH,
                    "matched": True,
                }
            },
            {"check_type": ProviderCheckType.FACE_MATCH},
        ):
            with self.subTest(overrides=overrides):
                resource.provider_check_id = self.committed_liveness(
                    resource, **overrides
                ).public_id
                resource.save(update_fields=["provider_check_id", "updated_at"])
                self.assertFalse(_repair_biometric_provider_check_links(resource))

    def test_superseded_generation_cannot_mutate_replacement_or_completed_job(self):
        verification = self._verification()
        resource = self._liveness(verification, "stale-owner")
        stale = self._job(verification, resource, status=ProcessingJobStatus.PROCESSING)
        ProcessingJob.objects.filter(pk=stale.pk).update(
            lease_generation=stale.lease_generation + 1
        )
        replacement = ProcessingJob.objects.get(pk=stale.pk)
        for mutation in (
            heartbeat_processing_job,
            defer_processing_job,
            complete_processing_job,
        ):
            with self.subTest(mutation=mutation.__name__):
                with self.assertRaises(ProcessingJobOwnershipLost):
                    if mutation is defer_processing_job:
                        mutation(stale, error_code="synthetic_failure")
                    else:
                        mutation(stale)
                current = ProcessingJob.objects.get(pk=stale.pk)
                self.assertEqual(current.status, ProcessingJobStatus.PROCESSING)
                self.assertEqual(current.lease_generation, replacement.lease_generation)
        complete_processing_job(replacement)
        with self.assertRaises(ProcessingJobOwnershipLost):
            complete_processing_job(stale)

    def test_route_repair_updates_exact_face_instead_of_newer_unrelated_row(self):
        verification = self._verification(
            status=VerificationStatus.MANUAL_REVIEW_REQUIRED
        )
        resource = self._liveness(verification, "exact-face")
        document = IdentityDocument.objects.create(
            tenant=self.tenant,
            verification=verification,
            verification_subject=self.subject,
            document_type_id="national_id",
            country_profile_id="GH",
        )
        fields = dict(
            tenant=self.tenant,
            verification=verification,
            selfie_capture=resource.selfie_capture,
            identity_document=document,
            status=FaceMatchStatus.INCONCLUSIVE,
        )
        origin = FaceMatch.objects.create(
            **fields, matched_at=timezone.now() - timedelta(seconds=5)
        )
        other = FaceMatch.objects.create(**fields, matched_at=timezone.now())
        VerificationDecision.objects.create(
            tenant=self.tenant,
            verification=verification,
            decision=VerificationStatus.MANUAL_REVIEW_REQUIRED,
            decision_type="system",
            reason_code="provider_route_exhausted",
            decided_at=timezone.now(),
            evidence_summary_json={
                "capability": ProviderCheckType.FACE_MATCH,
                "face_match_id": origin.public_id,
            },
        )
        job = self._job(verification, resource, status=ProcessingJobStatus.PROCESSING)
        complete_processing_job(job)
        origin.refresh_from_db()
        other.refresh_from_db()
        self.assertEqual(origin.status, FaceMatchStatus.ERROR)
        self.assertEqual(other.status, FaceMatchStatus.INCONCLUSIVE)

    def test_exhaustion_preserves_cancelled_decision(self):
        verification = self._verification(status=VerificationStatus.CANCELLED)
        decision = VerificationDecision.objects.create(
            tenant=self.tenant,
            verification=verification,
            decision=VerificationStatus.CANCELLED,
            decision_type="system",
            reason_code="subject_cancelled",
            decided_at=timezone.now(),
        )
        resource = self._liveness(verification, "cancelled-decision")
        job = self._job(
            verification,
            resource,
            status=ProcessingJobStatus.PROCESSING,
            attempt_count=3,
        )
        with patch("apps.webhooks.services.queue_webhook_events") as publish:
            exhaust_processing_job(job)
        verification.refresh_from_db()
        decision.refresh_from_db()
        self.assertEqual(verification.status, VerificationStatus.CANCELLED)
        self.assertEqual(decision.decision, VerificationStatus.CANCELLED)
        self.assertEqual(decision.reason_code, "subject_cancelled")
        publish.assert_not_called()
