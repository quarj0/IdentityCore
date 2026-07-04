from django.utils import timezone
from rest_framework import serializers

from apps.consent.models import ConsentRecord, ConsentTemplate, ConsentTemplateStatus
from apps.document_captures.models import DocumentCapture, DocumentCaptureSide
from apps.identity_documents.models import IdentityDocument, IdentityDocumentStatus
from apps.verifications.models import VerificationSession, VerificationSessionStatus, VerificationStatus


REQUIRED_STEPS = [
    "consent",
    "document_capture",
    "selfie_capture",
    "liveness_check",
]


def serialize_verification_session(verification_session: VerificationSession) -> dict:
    verification = verification_session.verification
    organization = verification.organization
    organization_logo_url = organization.settings_json.get("logo_url", "")
    return {
        "session_id": verification_session.public_id,
        "verification_id": verification.public_id,
        "status": verification_session.status,
        "organization": {
            "name": organization.name,
            "logo_url": organization_logo_url,
        },
        "purpose": verification.purpose,
        "required_steps": REQUIRED_STEPS,
        "expires_at": verification_session.expires_at.isoformat(),
    }


class VerificationSessionConsentSerializer(serializers.Serializer):
    accepted = serializers.BooleanField()

    def validate_accepted(self, value):
        if not value:
            raise serializers.ValidationError("Consent must be accepted to continue.")
        return value

    def save(self, **kwargs):
        request = self.context["request"]
        verification_session = request.verification_session
        verification = verification_session.verification

        existing_record = verification.consent_records.order_by("-accepted_at").first()
        if existing_record:
            if verification.status == VerificationStatus.PENDING_CONSENT:
                verification.status = VerificationStatus.IN_PROGRESS
                verification.save(update_fields=["status", "updated_at"])
            return existing_record

        consent_template = (
            ConsentTemplate.objects.filter(
                tenant=verification.tenant,
                status=ConsentTemplateStatus.ACTIVE,
            )
            .order_by("-version", "-created_at")
            .first()
        )
        consent_text_snapshot = (
            consent_template.content
            if consent_template is not None
            else f"I consent to the identity verification process for {verification.purpose}."
        )

        now = timezone.now()
        consent_record = ConsentRecord.objects.create(
            tenant=verification.tenant,
            verification=verification,
            verification_subject=verification.verification_subject,
            consent_template=consent_template,
            consent_text_snapshot=consent_text_snapshot,
            accepted=True,
            accepted_at=now,
            ip_address=request.META.get("REMOTE_ADDR"),
            user_agent=request.headers.get("User-Agent", ""),
            device_fingerprint=request.headers.get("X-Device-Fingerprint", ""),
        )

        update_session_fields = ["last_seen_at", "updated_at"]
        verification_session.last_seen_at = now
        if verification_session.status != VerificationSessionStatus.ACTIVE:
            verification_session.status = VerificationSessionStatus.ACTIVE
            update_session_fields.append("status")
        if verification_session.started_at is None:
            verification_session.started_at = now
            update_session_fields.append("started_at")
        verification_session.ip_address = request.META.get("REMOTE_ADDR")
        verification_session.user_agent = request.headers.get("User-Agent", "")
        verification_session.device_fingerprint = request.headers.get("X-Device-Fingerprint", "")
        update_session_fields.extend(["ip_address", "user_agent", "device_fingerprint"])
        verification_session.save(update_fields=update_session_fields)

        verification.status = VerificationStatus.IN_PROGRESS
        verification.save(update_fields=["status", "updated_at"])
        return consent_record


class DocumentCaptureInputSerializer(serializers.Serializer):
    side = serializers.ChoiceField(choices=DocumentCaptureSide.choices)
    upload_id = serializers.CharField(max_length=64)


class VerificationSessionDocumentSerializer(serializers.Serializer):
    document_type = serializers.CharField(max_length=64)
    country_code = serializers.CharField(max_length=8, required=False, allow_blank=True)
    captures = DocumentCaptureInputSerializer(many=True, allow_empty=False)

    def validate(self, attrs):
        request = self.context["request"]
        verification = request.verification_session.verification

        if not verification.consent_records.filter(accepted=True).exists():
            raise serializers.ValidationError(
                {"detail": "Consent must be accepted before document submission."}
            )

        capture_sides = [capture["side"] for capture in attrs["captures"]]
        if len(capture_sides) != len(set(capture_sides)):
            raise serializers.ValidationError({"captures": "Each document side may be submitted only once."})

        if len(capture_sides) == 1 and capture_sides[0] == DocumentCaptureSide.BACK:
            raise serializers.ValidationError({"captures": "Back-only document submissions are not supported."})

        return attrs

    def save(self, **kwargs):
        request = self.context["request"]
        verification_session = request.verification_session
        verification = verification_session.verification

        identity_document = IdentityDocument.objects.create(
            tenant=verification.tenant,
            verification=verification,
            verification_subject=verification.verification_subject,
            document_type_id=self.validated_data["document_type"],
            country_profile_id=self.validated_data.get("country_code", ""),
            local_document_name=self.validated_data["document_type"].replace("_", " ").title(),
            status=IdentityDocumentStatus.PROCESSING,
        )

        now = timezone.now()
        for capture in self.validated_data["captures"]:
            upload_id = capture["upload_id"]
            DocumentCapture.objects.create(
                tenant=verification.tenant,
                identity_document=identity_document,
                side=capture["side"],
                storage_key=f"uploads/documents/{upload_id}",
                storage_provider="local",
                mime_type="image/jpeg",
                file_size_bytes=0,
                checksum_sha256="",
                status="uploaded",
                captured_at=now,
            )

        verification.status = VerificationStatus.AWAITING_SELFIE
        verification.save(update_fields=["status", "updated_at"])
        verification_session.last_seen_at = now
        verification_session.save(update_fields=["last_seen_at", "updated_at"])
        return identity_document
