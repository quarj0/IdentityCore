from django.utils import timezone
from rest_framework import serializers

from apps.biometrics.models import (
    FaceMatch,
    FaceMatchStatus,
    LivenessCheck,
    LivenessCheckStatus,
    LivenessType,
    SelfieCapture,
    SelfieCaptureStatus,
    SelfieCaptureType,
)
from apps.consent.models import ConsentRecord, ConsentTemplate, ConsentTemplateStatus
from apps.document_captures.models import DocumentCapture, DocumentCaptureSide
from apps.identity_documents.models import IdentityDocument, IdentityDocumentStatus
from apps.providers.models import ProviderCheckStatus, ProviderCheckType
from apps.providers.services import create_provider_check
from apps.uploads.models import Upload, UploadPurpose, UploadStatus
from apps.uploads.services import consume_upload
from apps.verifications.models import (
    VerificationSession,
    VerificationSessionStatus,
    VerificationStatus,
)
from common.catalog import COUNTRY_PROFILES, DOCUMENT_TYPES


REQUIRED_STEPS = [
    "consent",
    "document_capture",
    "selfie_capture",
    "liveness_check",
]


def resolve_session_upload(
    *, verification_session: VerificationSession, upload_id: str, purpose: str
) -> Upload:
    try:
        upload = Upload.objects.get(
            public_id=upload_id,
            tenant=verification_session.tenant,
            verification=verification_session.verification,
            verification_session=verification_session,
            purpose=purpose,
            deleted_at__isnull=True,
        )
    except Upload.DoesNotExist as exc:
        raise serializers.ValidationError(
            {"upload_id": "Upload is invalid for this verification session."}
        ) from exc

    if upload.status == UploadStatus.CONSUMED:
        raise serializers.ValidationError(
            {"upload_id": "Upload has already been used."}
        )
    if upload.is_expired or upload.status == UploadStatus.EXPIRED:
        raise serializers.ValidationError({"upload_id": "Upload URL has expired."})
    return upload


STATUS_PRESENTATION = {
    VerificationStatus.PENDING_CONSENT: (
        "consent",
        "Please review and accept consent to continue.",
    ),
    VerificationStatus.IN_PROGRESS: (
        "document_capture",
        "Please submit your identity document.",
    ),
    VerificationStatus.AWAITING_SELFIE: (
        "selfie_capture",
        "Please capture and submit your selfie.",
    ),
    VerificationStatus.PROCESSING: (
        "processing",
        "Your verification is being processed.",
    ),
    VerificationStatus.MANUAL_REVIEW_REQUIRED: (
        "processing",
        "Your verification requires additional review.",
    ),
    VerificationStatus.VERIFIED: (
        "completed",
        "Your verification has been completed successfully.",
    ),
    VerificationStatus.REJECTED: (
        "completed",
        "Your verification could not be completed.",
    ),
    VerificationStatus.EXPIRED: ("expired", "Your verification session has expired."),
    VerificationStatus.CANCELLED: (
        "cancelled",
        "This verification has been cancelled.",
    ),
    VerificationStatus.FAILED: (
        "processing",
        "We could not complete your verification at this time.",
    ),
}


def serialize_verification_session(verification_session: VerificationSession) -> dict:
    verification = verification_session.verification
    organization = verification.organization
    organization_logo_url = organization.settings_json.get("logo_url", "")
    metadata = verification.metadata_json or {}
    onboarding = (organization.settings_json or {}).get("onboarding") or {}
    registration = onboarding.get("registration") or {}
    country_code = str(
        metadata.get("country_code")
        or registration.get("organization_country", "")
    ).upper()
    document_type = str(metadata.get("document_type", "national_id"))
    document_label = next(
        (
            supported["local_name"]
            for profile in COUNTRY_PROFILES
            if profile["code"] == country_code
            for supported in profile["supported_document_types"]
            if supported["document_type"] == document_type
        ),
        next(
            (item["name"] for item in DOCUMENT_TYPES if item["code"] == document_type),
            "identity document",
        ),
    )
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
        "document": {
            "country_code": country_code,
            "document_type": document_type,
            "label": document_label,
        },
        "expires_at": verification_session.expires_at.isoformat(),
    }


def serialize_verification_session_status(
    verification_session: VerificationSession,
) -> dict:
    verification = verification_session.verification
    latest_selfie = verification.selfie_captures.order_by("-created_at").first()
    latest_document = verification.identity_documents.order_by("-created_at").first()
    latest_liveness = verification.liveness_checks.order_by("-created_at").first()
    if latest_selfie is not None and latest_liveness is None:
        current_step = "liveness_check"
        message = "Please complete the passive liveness check."
    else:
        current_step, message = STATUS_PRESENTATION.get(
            verification.status,
            ("processing", "Your verification is being processed."),
        )
    return {
        "verification_id": verification.public_id,
        "status": verification.status,
        "current_step": current_step,
        "message": message,
        "evidence": {
            "identity_document_id": (
                latest_document.public_id if latest_document is not None else ""
            ),
            "selfie_capture_id": (
                latest_selfie.public_id if latest_selfie is not None else ""
            ),
            "liveness_check_id": (
                latest_liveness.public_id if latest_liveness is not None else ""
            ),
        },
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
        verification_session.device_fingerprint = request.headers.get(
            "X-Device-Fingerprint", ""
        )
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
        verification_session = request.verification_session
        verification = verification_session.verification

        if not verification.consent_records.filter(accepted=True).exists():
            raise serializers.ValidationError(
                {"detail": "Consent must be accepted before document submission."}
            )

        capture_sides = [capture["side"] for capture in attrs["captures"]]
        if len(capture_sides) != len(set(capture_sides)):
            raise serializers.ValidationError(
                {"captures": "Each document side may be submitted only once."}
            )

        if len(capture_sides) == 1 and capture_sides[0] == DocumentCaptureSide.BACK:
            raise serializers.ValidationError(
                {"captures": "Back-only document submissions are not supported."}
            )

        upload_ids = [capture["upload_id"] for capture in attrs["captures"]]
        if len(upload_ids) != len(set(upload_ids)):
            raise serializers.ValidationError(
                {"captures": "Each upload may be submitted only once."}
            )

        resolved_uploads = {}
        for capture in attrs["captures"]:
            resolved_uploads[capture["upload_id"]] = resolve_session_upload(
                verification_session=verification_session,
                upload_id=capture["upload_id"],
                purpose=UploadPurpose.DOCUMENT_CAPTURE,
            )
        attrs["resolved_uploads"] = resolved_uploads
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
            local_document_name=self.validated_data["document_type"]
            .replace("_", " ")
            .title(),
            status=IdentityDocumentStatus.PROCESSING,
        )

        now = timezone.now()
        for capture in self.validated_data["captures"]:
            upload = self.validated_data["resolved_uploads"][capture["upload_id"]]
            DocumentCapture.objects.create(
                tenant=verification.tenant,
                identity_document=identity_document,
                side=capture["side"],
                storage_key=upload.storage_key,
                storage_provider=upload.storage_provider,
                mime_type=upload.mime_type,
                file_size_bytes=upload.file_size_bytes,
                checksum_sha256=upload.checksum_sha256,
                status="uploaded",
                captured_at=now,
            )
            consume_upload(upload=upload)
        create_provider_check(
            verification=verification,
            check_type=ProviderCheckType.DOCUMENT_QUALITY,
            status=ProviderCheckStatus.PENDING,
            request_metadata={
                "identity_document_id": identity_document.public_id,
                "capture_count": len(self.validated_data["captures"]),
            },
        )
        create_provider_check(
            verification=verification,
            check_type=ProviderCheckType.DOCUMENT_CLASSIFICATION,
            status=ProviderCheckStatus.PENDING,
            request_metadata={
                "identity_document_id": identity_document.public_id,
                "document_type": identity_document.document_type_id,
                "country_code": identity_document.country_profile_id,
            },
        )
        create_provider_check(
            verification=verification,
            check_type=ProviderCheckType.DOCUMENT_OCR,
            status=ProviderCheckStatus.PENDING,
            request_metadata={
                "identity_document_id": identity_document.public_id,
                "document_type": identity_document.document_type_id,
                "country_code": identity_document.country_profile_id,
            },
        )

        verification.status = VerificationStatus.AWAITING_SELFIE
        verification.save(update_fields=["status", "updated_at"])
        verification_session.last_seen_at = now
        verification_session.save(update_fields=["last_seen_at", "updated_at"])
        return identity_document


class VerificationSessionSelfieSerializer(serializers.Serializer):
    capture_type = serializers.ChoiceField(choices=SelfieCaptureType.choices)
    upload_id = serializers.CharField(max_length=64)

    def validate(self, attrs):
        request = self.context["request"]
        verification_session = request.verification_session
        verification = verification_session.verification

        if not verification.consent_records.filter(accepted=True).exists():
            raise serializers.ValidationError(
                {"detail": "Consent must be accepted before selfie submission."}
            )
        if not verification.identity_documents.exists():
            raise serializers.ValidationError(
                {
                    "detail": "An identity document must be submitted before selfie capture."
                }
            )
        expected_purpose = (
            UploadPurpose.LIVENESS_CAPTURE
            if attrs["capture_type"] == SelfieCaptureType.VIDEO
            else UploadPurpose.SELFIE_CAPTURE
        )
        attrs["resolved_upload"] = resolve_session_upload(
            verification_session=verification_session,
            upload_id=attrs["upload_id"],
            purpose=expected_purpose,
        )
        return attrs

    def save(self, **kwargs):
        request = self.context["request"]
        verification_session = request.verification_session
        verification = verification_session.verification
        capture_type = self.validated_data["capture_type"]
        upload = self.validated_data["resolved_upload"]
        now = timezone.now()

        selfie_capture = SelfieCapture.objects.create(
            tenant=verification.tenant,
            verification=verification,
            verification_subject=verification.verification_subject,
            storage_key=upload.storage_key,
            storage_provider=upload.storage_provider,
            capture_type=capture_type,
            mime_type=upload.mime_type,
            file_size_bytes=upload.file_size_bytes,
            checksum_sha256=upload.checksum_sha256,
            face_count=1,
            status=SelfieCaptureStatus.UPLOADED,
            captured_at=now,
        )
        consume_upload(upload=upload)

        verification.status = VerificationStatus.PROCESSING
        verification.save(update_fields=["status", "updated_at"])
        verification_session.last_seen_at = now
        verification_session.save(update_fields=["last_seen_at", "updated_at"])
        return selfie_capture


class VerificationSessionLivenessSerializer(serializers.Serializer):
    liveness_type = serializers.ChoiceField(choices=LivenessType.choices)
    selfie_capture_id = serializers.CharField(max_length=64)

    def validate(self, attrs):
        request = self.context["request"]
        verification = request.verification_session.verification

        try:
            selfie_capture = verification.selfie_captures.get(
                public_id=attrs["selfie_capture_id"]
            )
        except SelfieCapture.DoesNotExist as exc:
            raise serializers.ValidationError(
                {
                    "selfie_capture_id": "Selfie capture was not found for this verification session."
                }
            ) from exc

        attrs["selfie_capture"] = selfie_capture
        return attrs

    def save(self, **kwargs):
        request = self.context["request"]
        verification_session = request.verification_session
        verification = verification_session.verification
        now = timezone.now()
        identity_document = verification.identity_documents.order_by(
            "-created_at"
        ).first()
        document_capture = None
        if identity_document is not None:
            document_capture = (
                identity_document.captures.filter(
                    side__in=[DocumentCaptureSide.FRONT, DocumentCaptureSide.SINGLE]
                )
                .order_by("created_at")
                .first()
            )

        liveness_check = LivenessCheck.objects.create(
            tenant=verification.tenant,
            verification=verification,
            selfie_capture=self.validated_data["selfie_capture"],
            liveness_type=self.validated_data["liveness_type"],
            status=LivenessCheckStatus.INCONCLUSIVE,
            checked_at=now,
        )
        liveness_provider_check = create_provider_check(
            verification=verification,
            check_type=ProviderCheckType.LIVENESS,
            status=ProviderCheckStatus.COMPLETED,
            normalized_result={
                "status": LivenessCheckStatus.INCONCLUSIVE,
                "source": "bootstrap-placeholder",
            },
            request_metadata={
                "selfie_capture_id": self.validated_data["selfie_capture"].public_id,
                "liveness_type": self.validated_data["liveness_type"],
            },
        )
        liveness_check.provider_check_id = liveness_provider_check.public_id
        liveness_check.save(update_fields=["provider_check_id", "updated_at"])
        if identity_document is not None:
            face_match = FaceMatch.objects.create(
                tenant=verification.tenant,
                verification=verification,
                selfie_capture=self.validated_data["selfie_capture"],
                identity_document=identity_document,
                document_capture=document_capture,
                status=FaceMatchStatus.INCONCLUSIVE,
                matched_at=now,
            )
            face_match_provider_check = create_provider_check(
                verification=verification,
                check_type=ProviderCheckType.FACE_MATCH,
                status=ProviderCheckStatus.COMPLETED,
                normalized_result={
                    "status": FaceMatchStatus.INCONCLUSIVE,
                    "source": "bootstrap-placeholder",
                },
                request_metadata={
                    "selfie_capture_id": self.validated_data[
                        "selfie_capture"
                    ].public_id,
                    "identity_document_id": identity_document.public_id,
                    "document_capture_id": (
                        document_capture.public_id
                        if document_capture is not None
                        else ""
                    ),
                },
            )
            face_match.provider_check_id = face_match_provider_check.public_id
            face_match.save(update_fields=["provider_check_id", "updated_at"])

        verification.status = VerificationStatus.PROCESSING
        verification.save(update_fields=["status", "updated_at"])
        verification_session.last_seen_at = now
        verification_session.save(update_fields=["last_seen_at", "updated_at"])
        return liveness_check
