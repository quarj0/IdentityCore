from datetime import timedelta

from django.test import TestCase, override_settings
from django.utils import timezone

from apps.biometrics.models import (
    FaceMatch,
    FaceMatchStatus,
    LivenessCheck,
    LivenessCheckStatus,
    SelfieCapture,
)
from apps.document_captures.models import DocumentCapture
from apps.identity_documents.models import IdentityDocument
from apps.organizations.models import Organization
from apps.providers.models import (
    Provider,
    ProviderCheck,
    ProviderCheckStatus,
    ProviderCheckType,
    ProviderStatus,
    ProviderType,
)
from apps.providers.services import create_provider_check
from apps.tenants.models import Tenant
from apps.verification_subjects.models import VerificationSubject
from apps.verifications.models import ProcessingJobType, Verification, VerificationStatus
from apps.verifications.processing_jobs import acquire_processing_job


@override_settings(PROCESSING_JOB_LEASE_SECONDS=300, PROCESSING_JOB_MAX_ATTEMPTS=3)
class BiometricProviderLinkRecoveryTests(TestCase):
    def setUp(self):
        organization = Organization.objects.create(
            name="Provider Link Recovery", slug="provider-link-recovery"
        )
        self.tenant = Tenant.objects.create(
            organization=organization,
            name="Provider Link Recovery Tenant",
            slug="provider-link-recovery-tenant",
            status="active",
        )
        subject = VerificationSubject.objects.create(
            tenant=self.tenant,
            full_name="Provider Link Subject",
        )
        self.verification = Verification.objects.create(
            tenant=self.tenant,
            organization=organization,
            verification_subject=subject,
            purpose="Provider link recovery",
            status=VerificationStatus.PROCESSING,
            expires_at=timezone.now() + timedelta(hours=1),
        )
        identity_document = IdentityDocument.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            verification_subject=subject,
            document_type_id="national_id",
            country_profile_id="GH",
            status="processing",
        )
        document_capture = DocumentCapture.objects.create(
            tenant=self.tenant,
            identity_document=identity_document,
            side="front",
            storage_key="uploads/documents/provider-link-recovery",
            captured_at=timezone.now(),
        )
        selfie = SelfieCapture.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            verification_subject=subject,
            storage_key="uploads/selfies/provider-link-recovery",
            capture_type="image",
            captured_at=timezone.now(),
        )
        initial_liveness = create_provider_check(
            verification=self.verification,
            check_type=ProviderCheckType.LIVENESS,
            status=ProviderCheckStatus.PENDING,
        )
        initial_face = create_provider_check(
            verification=self.verification,
            check_type=ProviderCheckType.FACE_MATCH,
            status=ProviderCheckStatus.PENDING,
        )
        for check in (initial_liveness, initial_face):
            check.status = ProviderCheckStatus.FAILED
            check.completed_at = timezone.now()
            check.error_code = "provider_error"
            check.error_message = "Primary provider failed."
            check.save(
                update_fields=[
                    "status",
                    "completed_at",
                    "error_code",
                    "error_message",
                    "updated_at",
                ]
            )
        self.liveness = LivenessCheck.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            selfie_capture=selfie,
            provider_check_id=initial_liveness.public_id,
            liveness_type="passive",
            status=LivenessCheckStatus.INCONCLUSIVE,
            checked_at=timezone.now(),
        )
        self.face_match = FaceMatch.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            selfie_capture=selfie,
            identity_document=identity_document,
            document_capture=document_capture,
            provider_check_id=initial_face.public_id,
            status=FaceMatchStatus.INCONCLUSIVE,
            matched_at=timezone.now(),
        )
        fallback_liveness = Provider.objects.create(
            name="Fallback Liveness Link",
            code="fallback-liveness-link",
            provider_type=ProviderType.LIVENESS,
            status=ProviderStatus.ACTIVE,
        )
        fallback_face = Provider.objects.create(
            name="Fallback Face Link",
            code="fallback-face-link",
            provider_type=ProviderType.BIOMETRIC,
            status=ProviderStatus.ACTIVE,
        )
        self.completed_liveness = ProviderCheck.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            provider=fallback_liveness,
            check_type=ProviderCheckType.LIVENESS,
            status=ProviderCheckStatus.COMPLETED,
            request_metadata_json={"liveness_check_id": self.liveness.public_id},
            normalized_result_json={
                "contract_version": "1",
                "capability": ProviderCheckType.LIVENESS,
                "status": "completed",
                "passed": True,
                "score": 0.98,
            },
            started_at=timezone.now(),
            completed_at=timezone.now(),
        )
        self.completed_face = ProviderCheck.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            provider=fallback_face,
            check_type=ProviderCheckType.FACE_MATCH,
            status=ProviderCheckStatus.COMPLETED,
            request_metadata_json={"face_match_id": self.face_match.public_id},
            normalized_result_json={
                "contract_version": "1",
                "capability": ProviderCheckType.FACE_MATCH,
                "status": "completed",
                "matched": True,
                "match_score": 0.97,
            },
            started_at=timezone.now(),
            completed_at=timezone.now(),
        )

    def test_acquire_repairs_fallback_provider_links_before_worker_continues(self):
        job = acquire_processing_job(
            job_type=ProcessingJobType.BIOMETRICS,
            resource=self.liveness,
        )

        self.assertIsNotNone(job)
        self.liveness.refresh_from_db()
        self.face_match.refresh_from_db()
        self.assertEqual(
            self.liveness.provider_check_id, self.completed_liveness.public_id
        )
        self.assertEqual(
            self.face_match.provider_check_id, self.completed_face.public_id
        )
