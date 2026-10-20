from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from apps.identity_documents import tests as fixtures
from apps.identity_documents.models import IdentityDocumentStatus
from apps.identity_documents.tasks import process_identity_document_task
from apps.providers.models import ProviderCheckType
from apps.verifications.models import (
    ProcessingJob,
    ProcessingJobType,
    Verification,
    VerificationDecision,
)
from apps.verifications.processing_jobs import (
    acquire_processing_job,
    complete_processing_job,
    recover_stale_processing_jobs,
    document_processing_stop_status,
    ProcessingJobOwnershipLost,
)


class DocumentTerminalRecoveryTests(TestCase):
    setUp = fixtures.IdentityDocumentTaskTests.setUp

    def job(self):
        return acquire_processing_job(
            job_type=ProcessingJobType.IDENTITY_DOCUMENT,
            resource=self.identity_document,
        )

    def route_decision(
        self, *, document_id=None, capability=ProviderCheckType.DOCUMENT_OCR
    ):
        self.verification.status = "manual_review_required"
        self.verification.save(update_fields=["status"])
        return VerificationDecision.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            decision="manual_review_required",
            decision_type="system",
            reason_code="provider_route_exhausted",
            decided_at=timezone.now(),
            evidence_summary_json={
                "identity_document_id": document_id or self.identity_document.public_id,
                "capability": capability,
            },
        )

    @patch("apps.identity_documents.tasks.run_document_quality")
    @patch("apps.identity_documents.tasks.run_document_classification")
    @patch("apps.identity_documents.tasks.run_document_ocr")
    def test_terminal_case_before_acquisition_stops_all_provider_work(
        self, ocr, classification, quality
    ):
        for status in ("cancelled", "expired", "failed", "verified", "rejected"):
            with self.subTest(status=status):
                ProcessingJob.objects.all().delete()
                self.identity_document.status = IdentityDocumentStatus.PROCESSING
                self.identity_document.save(update_fields=["status"])
                self.verification.status = status
                self.verification.save(update_fields=["status"])
                self.assertEqual(
                    process_identity_document_task(self.identity_document.public_id),
                    "failed",
                )
                self.verification.refresh_from_db()
                self.assertEqual(self.verification.status, status)
        ocr.assert_not_called()
        classification.assert_not_called()
        quality.assert_not_called()

    @patch("apps.identity_documents.tasks.process_identity_document_task.delay")
    def test_recovery_at_attempt_limit_repairs_bound_route_without_redispatch(
        self, dispatch
    ):
        job = self.job()
        decision = self.route_decision()
        ProcessingJob.objects.filter(pk=job.pk).update(
            max_attempts=job.attempt_count,
            lease_expires_at=timezone.now() - timedelta(seconds=1),
        )
        self.assertEqual(recover_stale_processing_jobs(), (0, 0))
        job.refresh_from_db()
        self.identity_document.refresh_from_db()
        decision.refresh_from_db()
        self.assertEqual(job.status, "completed")
        self.assertEqual(self.identity_document.status, "manual_review_required")
        self.assertEqual(decision.decision, "manual_review_required")
        dispatch.assert_not_called()

    @patch("apps.identity_documents.tasks.run_document_quality")
    def test_handoff_after_route_commit_rejects_old_owner_and_new_owner_does_not_call_provider(
        self, quality
    ):
        old = self.job()
        self.route_decision()
        ProcessingJob.objects.filter(pk=old.pk).update(
            lease_generation=old.lease_generation + 1,
            status="queued",
            lease_expires_at=timezone.now() - timedelta(seconds=1),
        )
        with self.assertRaises(ProcessingJobOwnershipLost):
            complete_processing_job(old)
        self.assertEqual(
            process_identity_document_task(self.identity_document.public_id),
            "manual_review_required",
        )
        self.assertEqual(ProcessingJob.objects.get(pk=old.pk).status, "completed")
        quality.assert_not_called()

    def test_unrelated_document_or_biometric_route_is_not_a_document_completion(self):
        job = self.job()
        decision = self.route_decision(document_id="doc_other")
        self.assertIsNone(document_processing_stop_status(job))
        decision.evidence_summary_json = {
            "identity_document_id": self.identity_document.public_id,
            "capability": "liveness",
        }
        decision.save(update_fields=["evidence_summary_json"])
        self.assertIsNone(document_processing_stop_status(job))

    @patch("apps.identity_documents.tasks.run_document_quality")
    def test_failure_after_terminal_transition_keeps_owned_failure_and_case_outcome(
        self, quality
    ):
        def fail(**kwargs):
            Verification.objects.filter(pk=self.verification.pk).update(
                status="cancelled"
            )
            raise RuntimeError("Synthetic provider processing failure")

        quality.side_effect = fail
        self.assertEqual(
            process_identity_document_task(self.identity_document.public_id), "failed"
        )
        self.identity_document.refresh_from_db()
        self.verification.refresh_from_db()
        self.assertEqual(self.identity_document.status, "failed")
        self.assertEqual(self.verification.status, "cancelled")
        self.assertEqual(
            ProcessingJob.objects.get(
                resource_public_id=self.identity_document.public_id
            ).status,
            "completed",
        )
