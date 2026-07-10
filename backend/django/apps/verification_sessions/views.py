from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from apps.audit.services import record_audit_event
from apps.biometrics.tasks import process_verification_biometrics_task
from apps.identity_documents.tasks import process_identity_document_task
from apps.organizations.onboarding import submit_administrator_identity_verification
from apps.webhooks.services import queue_webhook_events
from apps.verification_sessions.serializers import (
    VerificationSessionConsentSerializer,
    VerificationSessionDocumentSerializer,
    VerificationSessionLivenessSerializer,
    VerificationSessionSelfieSerializer,
    serialize_verification_session,
    serialize_verification_session_status,
)
from apps.verifications.models import (
    VerificationMobileHandoff,
    VerificationSession,
    VerificationSessionStatus,
)
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


class VerificationMobileHandoffCreateView(VerificationSessionBaseView):
    def post(self, request, session_id: str):
        self._touch_session(request)
        source_session = request.verification_session
        if source_session.expires_at <= timezone.now():
            raise ValidationError({"detail": "This verification session has expired."})
        source_session.mobile_handoffs.filter(
            redeemed_at__isnull=True, expires_at__gt=timezone.now()
        ).update(expires_at=timezone.now())
        raw_token = VerificationMobileHandoff.generate_token()
        expires_at = min(
            source_session.expires_at,
            timezone.now() + timedelta(minutes=5),
        )
        handoff = VerificationMobileHandoff(
            source_session=source_session,
            expires_at=expires_at,
            token_hash="",
        )
        handoff.set_token(raw_token)
        handoff.save()
        handoff_url = (
            f"{settings.VERIFICATION_PORTAL_BASE_URL.rstrip('/')}/{source_session.public_id}"
            f"?handoff={handoff.public_id}.{raw_token}"
        )
        record_audit_event(
            tenant=request.tenant,
            actor=source_session.verification.verification_subject,
            request=request,
            action="verification.mobile_handoff_created",
            target_type="verification_session",
            target_id=source_session.public_id,
            metadata={"handoff_id": handoff.public_id, "expires_at": expires_at.isoformat()},
        )
        return success_response(
            {"handoff_url": handoff_url, "expires_at": expires_at.isoformat()},
            request=request,
        )


class VerificationMobileHandoffRedeemView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @transaction.atomic
    def post(self, request):
        handoff_value = str(request.data.get("handoff", ""))
        handoff_id, separator, raw_token = handoff_value.partition(".")
        if not separator or not raw_token:
            raise ValidationError({"handoff": "This mobile handoff link is invalid."})
        handoff = (
            VerificationMobileHandoff.objects.select_for_update()
            .select_related("source_session", "source_session__verification")
            .filter(public_id=handoff_id)
            .first()
        )
        if handoff is None or not handoff.matches_token(raw_token):
            raise NotFound("This mobile handoff link is invalid.")
        if handoff.redeemed_at is not None:
            raise ValidationError({"handoff": "This mobile handoff link has already been used."})
        if handoff.expires_at <= timezone.now():
            raise ValidationError({"handoff": "This mobile handoff link has expired."})

        source = handoff.source_session
        session_token = VerificationSession.generate_session_token()
        mobile_session = VerificationSession(
            verification=source.verification,
            tenant=source.tenant,
            expires_at=source.expires_at,
        )
        mobile_session.set_session_token(session_token)
        mobile_session.save()
        handoff.redeemed_session = mobile_session
        handoff.redeemed_at = timezone.now()
        handoff.save(update_fields=["redeemed_session", "redeemed_at", "updated_at"])
        record_audit_event(
            tenant=source.tenant,
            actor=source.verification.verification_subject,
            request=request,
            action="verification.mobile_handoff_redeemed",
            target_type="verification_session",
            target_id=mobile_session.public_id,
            metadata={"handoff_id": handoff.public_id, "source_session_id": source.public_id},
        )
        return success_response(
            {
                "session_id": mobile_session.public_id,
                "session_token": session_token,
                "verification_id": source.verification.public_id,
            },
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
        queue_webhook_events(
            tenant=request.tenant,
            event_type="verification.consent_accepted",
            payload={
                "verification_id": verification.public_id,
                "external_reference": verification.external_reference,
                "status": verification.status,
            },
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
        queue_webhook_events(
            tenant=request.tenant,
            event_type="verification.document_uploaded",
            payload={
                "verification_id": verification.public_id,
                "external_reference": verification.external_reference,
                "status": verification.status,
            },
        )
        process_identity_document_task.delay(identity_document.public_id)
        return success_response(
            {
                "identity_document_id": identity_document.public_id,
                "status": identity_document.status,
                "next_step": "document_processing",
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
        queue_webhook_events(
            tenant=request.tenant,
            event_type="verification.selfie_uploaded",
            payload={
                "verification_id": verification.public_id,
                "external_reference": verification.external_reference,
                "status": verification.status,
            },
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
        if (
            verification.metadata_json.get("workflow")
            == "administrator_onboarding"
            and verification.created_by is not None
        ):
            submit_administrator_identity_verification(
                user=verification.created_by,
                verification_id=verification.public_id,
                request=request,
            )
        process_verification_biometrics_task.delay(liveness_check.public_id)
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
