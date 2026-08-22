from datetime import timedelta
from unittest.mock import patch

from django.db import transaction
from django.test import TestCase, override_settings
from django.utils import timezone

from apps.audit.models import AuditEvent
from apps.biometrics.models import (
    LivenessCheck,
    LivenessCheckStatus,
    SelfieCapture,
)
from apps.identity_documents.models import IdentityDocument, IdentityDocumentStatus
from apps.organizations.models import Organization
from apps.providers.models import (
    ProviderAttemptOutcome,
    ProviderCheck,
    ProviderCheckStatus,
    ProviderCheckType,
    ProviderExecutionAttempt,
)
from apps.providers.services import get_or_create_system_provider
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
from apps.verifications.processing_jobs import recover_stale_processing_jobs


@override_settings(PROCESSING_JOB_LEASE_SECONDS=300, PROCESSING_JOB_MAX_ATTEMPTS=3)
class ProcessingJobLifecycleRecoveryTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            name="Lifecycle Recovery", slug="lifecycle-recovery"
        )
        self.tenant = Tenant.objects.create(
            organization=self.organization,
            name="Lifecycle Recovery Tenant",
            slug="lifecycle-recovery-tenant",
            status="active",
        )
        self.subject = VerificationSubject.objects.create(
            tenant=self.tenant,
            full_name="Lifecycle Recovery Subject",
        )

    def _verification(self, *, status):
        return Verification.objects.create(
            tenant=self.tenant,
            organization=self.organization,
            verification_subject=self.subject,
            purpose="Lifecycle recovery",
            status=status,
            expires_at=timezone.now() + timedelta(hours=1),
        )

    @patch("apps.biometrics.tasks.process_verification_biometrics_task.delay")
    def test_stale_route_exhaustion_repairs_biometric_state_without_overwriting_decision(
        self, mock_delay
    ):
        verification = self._verification(
            status=VerificationStatus.MANUAL_REVIEW_REQUIRED
        )
        selfie = SelfieCapture.objects.create(
            tenant=self.tenant,
            verification=verification,
            verification_subject=self.subject,
            storage_key="uploads/selfies/route-exhaustion-recovery",
            capture_type="image",
            captured_at=timezone.now(),
        )
        liveness = LivenessCheck.objects.create(
            tenant=self.tenant,
            verification=verification,
            selfie_capture=selfie,
            liveness_type="passive",
            status=LivenessCheckStatus.INCONCLUSIVE,
            checked_at=timezone.now(),
        )
        now = timezone.now()
        provider = get_or_create_system_provider(ProviderCheckType.LIVENESS)
        provider_check = ProviderCheck.objects.create(
            tenant=self.tenant,
            verification=verification,
            provider=provider,
            check_type=ProviderCheckType.LIVENESS,
            status=ProviderCheckStatus.FAILED,
            request_metadata_json={"liveness_check_id": liveness.public_id},
            error_code="provider_timeout",
            error_message="timeout",
            started_at=now - timedelta(seconds=2),
            completed_at=now - timedelta(seconds=1),
        )
        ProviderExecutionAttempt.objects.create(
            execution_id="pex_lifecycle_route_exhaustion",
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
        job = ProcessingJob.objects.create(
            tenant=self.tenant,
            verification=verification,
            job_type=ProcessingJobType.BIOMETRICS,
            resource_public_id=liveness.public_id,
            status=ProcessingJobStatus.PROCESSING,
            attempt_count=3,
            max_attempts=3,
            heartbeat_at=timezone.now() - timedelta(minutes=10),
            lease_expires_at=timezone.now() - timedelta(minutes=5),
        )

        recovered, exhausted = recover_stale_processing_jobs(limit=10)

        job.refresh_from_db()
        liveness.refresh_from_db()
        verification.refresh_from_db()
        self.assertEqual((recovered, exhausted), (0, 0))
        self.assertEqual(job.status, ProcessingJobStatus.COMPLETED)
        self.assertEqual(liveness.status, LivenessCheckStatus.ERROR)
        self.assertEqual(liveness.failure_reason, "provider_route_exhausted")
        self.assertEqual(
            verification.decision_record.reason_code, "provider_route_exhausted"
        )
        mock_delay.assert_not_called()

    @patch("apps.verifications.evidence_commit.ensure_verification_evidence_report")
    @patch("apps.notifications.services.queue_verification_status_notifications")
    @patch("apps.webhooks.services.queue_webhook_events")
    def test_retry_exhaustion_queues_lifecycle_outbox_and_notification_atomically(
        self, mock_webhooks, mock_notifications, _mock_evidence
    ):
        verification = self._verification(status=VerificationStatus.AWAITING_DOCUMENT)
        document = IdentityDocument.objects.create(
            tenant=self.tenant,
            verification=verification,
            verification_subject=self.subject,
            document_type_id="national_id",
            country_profile_id="GH",
            status=IdentityDocumentStatus.PROCESSING,
        )
        job = ProcessingJob.objects.create(
            tenant=self.tenant,
            verification=verification,
            job_type=ProcessingJobType.IDENTITY_DOCUMENT,
            resource_public_id=document.public_id,
            status=ProcessingJobStatus.PROCESSING,
            attempt_count=3,
            max_attempts=3,
            heartbeat_at=timezone.now() - timedelta(minutes=10),
            lease_expires_at=timezone.now() - timedelta(minutes=5),
        )
        atomic_observations = []

        def record_webhook_call(**kwargs):
            atomic_observations.append(transaction.get_connection().in_atomic_block)
            return []

        mock_webhooks.side_effect = record_webhook_call

        with self.captureOnCommitCallbacks(execute=True):
            recovered, exhausted = recover_stale_processing_jobs(limit=10)

        job.refresh_from_db()
        document.refresh_from_db()
        verification.refresh_from_db()
        self.assertEqual((recovered, exhausted), (0, 1))
        self.assertEqual(job.status, ProcessingJobStatus.EXHAUSTED)
        self.assertEqual(
            document.status, IdentityDocumentStatus.MANUAL_REVIEW_REQUIRED
        )
        self.assertEqual(
            verification.status, VerificationStatus.MANUAL_REVIEW_REQUIRED
        )
        self.assertEqual(
            verification.decision_record.reason_code, "processing_retries_exhausted"
        )
        self.assertEqual(atomic_observations, [True])
        mock_webhooks.assert_called_once()
        self.assertEqual(
            mock_webhooks.call_args.kwargs["event_type"],
            "verification.manual_review_required",
        )
        self.assertEqual(
            mock_webhooks.call_args.kwargs["payload"]["reason_code"],
            "processing_retries_exhausted",
        )
        mock_notifications.assert_called_once_with(
            verification=verification,
            decision=VerificationStatus.MANUAL_REVIEW_REQUIRED,
            risk_level="high",
        )
        event = AuditEvent.objects.get(
            action="verification.processing_retries_exhausted"
        )
        self.assertEqual(
            set(event.metadata_json),
            {"processing_job_id", "processing_job_type", "attempt_count"},
        )

    @patch("apps.notifications.services.queue_verification_status_notifications")
    @patch(
        "apps.webhooks.services.queue_webhook_events",
        side_effect=RuntimeError("outbox insert failed"),
    )
    def test_retry_exhaustion_rolls_back_when_outbox_insert_fails(
        self, _mock_webhooks, mock_notifications
    ):
        verification = self._verification(status=VerificationStatus.AWAITING_DOCUMENT)
        document = IdentityDocument.objects.create(
            tenant=self.tenant,
            verification=verification,
            verification_subject=self.subject,
            document_type_id="national_id",
            country_profile_id="GH",
            status=IdentityDocumentStatus.PROCESSING,
        )
        job = ProcessingJob.objects.create(
            tenant=self.tenant,
            verification=verification,
            job_type=ProcessingJobType.IDENTITY_DOCUMENT,
            resource_public_id=document.public_id,
            status=ProcessingJobStatus.PROCESSING,
            attempt_count=3,
            max_attempts=3,
            heartbeat_at=timezone.now() - timedelta(minutes=10),
            lease_expires_at=timezone.now() - timedelta(minutes=5),
        )

        with self.assertRaisesRegex(RuntimeError, "outbox insert failed"):
            recover_stale_processing_jobs(limit=10)

        job.refresh_from_db()
        document.refresh_from_db()
        verification.refresh_from_db()
        self.assertEqual(job.status, ProcessingJobStatus.PROCESSING)
        self.assertEqual(document.status, IdentityDocumentStatus.PROCESSING)
        self.assertEqual(verification.status, VerificationStatus.AWAITING_DOCUMENT)
        self.assertFalse(
            VerificationDecision.objects.filter(verification=verification).exists()
        )
        self.assertFalse(
            AuditEvent.objects.filter(
                action="verification.processing_retries_exhausted"
            ).exists()
        )
        mock_notifications.assert_not_called()
