from datetime import timedelta

from django.test import TestCase
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
from apps.providers.services import (
    _apply_route_final_action,
    get_or_create_system_provider,
)
from apps.tenants.models import Tenant
from apps.verification_subjects.models import VerificationSubject
from apps.verifications.models import (
    ProcessingJob,
    ProcessingJobStatus,
    ProcessingJobType,
    Verification,
    VerificationDecision,
    VerificationStatus,
)
from apps.verifications.processing_jobs import ProcessingJobOwnershipLost


class RouteFinalActionOwnershipTests(TestCase):
    def setUp(self):
        organization = Organization.objects.create(
            name="Route Final Ownership", slug="route-final-ownership"
        )
        self.tenant = Tenant.objects.create(
            organization=organization,
            name="Route Final Ownership Tenant",
            slug="route-final-ownership-tenant",
            status="active",
        )
        subject = VerificationSubject.objects.create(
            tenant=self.tenant,
            full_name="Route Final Ownership Subject",
        )
        self.verification = Verification.objects.create(
            tenant=self.tenant,
            organization=organization,
            verification_subject=subject,
            purpose="Route ownership regression",
            status=VerificationStatus.PROCESSING,
            expires_at=timezone.now() + timedelta(hours=1),
        )
        selfie = SelfieCapture.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            verification_subject=subject,
            storage_key="uploads/selfies/route-final-ownership",
            capture_type="image",
            captured_at=timezone.now(),
        )
        self.liveness = LivenessCheck.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            selfie_capture=selfie,
            liveness_type="passive",
            status=LivenessCheckStatus.INCONCLUSIVE,
            checked_at=timezone.now(),
        )
        now = timezone.now()
        provider = get_or_create_system_provider(ProviderCheckType.LIVENESS)
        provider_check = ProviderCheck.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            provider=provider,
            check_type=ProviderCheckType.LIVENESS,
            status=ProviderCheckStatus.FAILED,
            request_metadata_json={"liveness_check_id": self.liveness.public_id},
            error_code="provider_timeout",
            error_message="timeout",
            started_at=now - timedelta(seconds=2),
            completed_at=now - timedelta(seconds=1),
        )
        self.attempt = ProviderExecutionAttempt.objects.create(
            execution_id="pex_route_final_ownership",
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

    def _job(self, status):
        return ProcessingJob.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            job_type=ProcessingJobType.BIOMETRICS,
            resource_public_id=self.liveness.public_id,
            status=status,
            attempt_count=3,
            max_attempts=3,
            heartbeat_at=timezone.now() - timedelta(minutes=10),
            lease_expires_at=timezone.now() - timedelta(minutes=5),
            error_code=(
                "processing_retries_exhausted"
                if status == ProcessingJobStatus.EXHAUSTED
                else ""
            ),
        )

    def test_exhausted_job_blocks_route_decision_before_side_effects_commit(self):
        self._job(ProcessingJobStatus.EXHAUSTED)

        with self.assertRaises(ProcessingJobOwnershipLost):
            _apply_route_final_action(
                verification=self.verification,
                route=None,
                check_type=ProviderCheckType.LIVENESS,
                attempts=[self.attempt],
            )

        self.verification.refresh_from_db()
        self.assertEqual(self.verification.status, VerificationStatus.PROCESSING)
        self.assertFalse(
            VerificationDecision.objects.filter(verification=self.verification).exists()
        )

    def test_route_decision_persists_originating_liveness_identifier(self):
        self._job(ProcessingJobStatus.PROCESSING)

        _apply_route_final_action(
            verification=self.verification,
            route=None,
            check_type=ProviderCheckType.LIVENESS,
            attempts=[self.attempt],
        )

        decision = VerificationDecision.objects.get(verification=self.verification)
        self.assertEqual(
            decision.evidence_summary_json["liveness_check_id"],
            self.liveness.public_id,
        )
