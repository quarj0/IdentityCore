from django.utils import timezone
from rest_framework.views import APIView

from apps.audit.services import record_audit_event
from apps.verification_sessions.serializers import (
    VerificationSessionConsentSerializer,
    VerificationSessionDocumentSerializer,
    VerificationSessionLivenessSerializer,
    VerificationSessionSelfieSerializer,
    serialize_verification_session,
    serialize_verification_session_status,
)
from apps.verifications.models import VerificationSessionStatus
from common.authentication import VerificationSessionAuthentication
from common.responses import success_response


class VerificationSessionBaseView(APIView):
    authentication_classes = [VerificationSessionAuthentication]

    def _touch_session(self, request) -> None:
        verification_session = request.verification_session
        now = timezone.now()
        update_fields = ["last_seen_at", "ip_address", "user_agent", "device_fingerprint", "updated_at"]

        verification_session.last_seen_at = now
        verification_session.ip_address = request.META.get("REMOTE_ADDR")
        verification_session.user_agent = request.headers.get("User-Agent", "")
        verification_session.device_fingerprint = request.headers.get("X-Device-Fingerprint", "")
        if verification_session.started_at is None:
            verification_session.started_at = now
            update_fields.append("started_at")
        if verification_session.status == VerificationSessionStatus.CREATED:
            verification_session.status = VerificationSessionStatus.ACTIVE
            update_fields.append("status")
        verification_session.save(update_fields=update_fields)


class VerificationSessionDetailView(VerificationSessionBaseView):
    def get(self, request, session_id: str):
        self._touch_session(request)
        return success_response(
            serialize_verification_session(request.verification_session),
            request=request,
        )


class VerificationSessionConsentView(VerificationSessionBaseView):
    def post(self, request, session_id: str):
        self._touch_session(request)
        serializer = VerificationSessionConsentSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        consent_record = serializer.save()
        verification = request.verification_session.verification
        record_audit_event(
            tenant=request.tenant,
            actor=verification.verification_subject,
            request=request,
            action="consent.accepted",
            target_type="verification",
            target_id=verification.public_id,
            metadata={"consent_record_id": consent_record.public_id},
        )
        return success_response(
            {
                "consent_record_id": consent_record.public_id,
                "next_step": "document_capture",
            },
            request=request,
        )


class VerificationSessionDocumentView(VerificationSessionBaseView):
    def post(self, request, session_id: str):
        self._touch_session(request)
        serializer = VerificationSessionDocumentSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        identity_document = serializer.save()
        verification = request.verification_session.verification
        record_audit_event(
            tenant=request.tenant,
            actor=verification.verification_subject,
            request=request,
            action="document.uploaded",
            target_type="verification",
            target_id=verification.public_id,
            metadata={"identity_document_id": identity_document.public_id},
        )
        return success_response(
            {
                "identity_document_id": identity_document.public_id,
                "status": identity_document.status,
                "next_step": "selfie_capture",
            },
            request=request,
        )


class VerificationSessionSelfieView(VerificationSessionBaseView):
    def post(self, request, session_id: str):
        self._touch_session(request)
        serializer = VerificationSessionSelfieSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        selfie_capture = serializer.save()
        verification = request.verification_session.verification
        record_audit_event(
            tenant=request.tenant,
            actor=verification.verification_subject,
            request=request,
            action="selfie.uploaded",
            target_type="verification",
            target_id=verification.public_id,
            metadata={"selfie_capture_id": selfie_capture.public_id},
        )
        return success_response(
            {
                "selfie_capture_id": selfie_capture.public_id,
                "status": "processing",
                "next_step": "liveness_check",
            },
            request=request,
        )


class VerificationSessionLivenessView(VerificationSessionBaseView):
    def post(self, request, session_id: str):
        self._touch_session(request)
        serializer = VerificationSessionLivenessSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        liveness_check = serializer.save()
        verification = request.verification_session.verification
        record_audit_event(
            tenant=request.tenant,
            actor=verification.verification_subject,
            request=request,
            action="liveness.completed",
            target_type="verification",
            target_id=verification.public_id,
            metadata={"liveness_check_id": liveness_check.public_id},
        )
        latest_face_match = verification.face_matches.order_by("-matched_at").first()
        if latest_face_match is not None:
            record_audit_event(
                tenant=request.tenant,
                actor=verification.verification_subject,
                request=request,
                action="face_match.completed",
                target_type="verification",
                target_id=verification.public_id,
                metadata={"face_match_id": latest_face_match.public_id},
            )
        return success_response(
            {
                "liveness_check_id": liveness_check.public_id,
                "status": "processing",
            },
            request=request,
        )


class VerificationSessionStatusView(VerificationSessionBaseView):
    def get(self, request, session_id: str):
        self._touch_session(request)
        return success_response(
            serialize_verification_session_status(request.verification_session),
            request=request,
        )
