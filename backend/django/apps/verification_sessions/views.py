from django.utils import timezone
from rest_framework.views import APIView

from apps.verification_sessions.serializers import (
    VerificationSessionConsentSerializer,
    serialize_verification_session,
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
        return success_response(
            {
                "consent_record_id": consent_record.public_id,
                "next_step": "document_capture",
            },
            request=request,
        )
