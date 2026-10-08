from datetime import timedelta
from urllib.parse import urlsplit

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import APIException, Throttled, ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from apps.audit.services import lock_audit_chain, record_audit_event
from apps.verifications.transitions import TERMINAL_STATUSES
from apps.verifications.processing_jobs import (
    queue_biometrics_processing,
    queue_identity_document_processing,
)
from apps.platform_settings.services import get_platform_setting_value
from apps.organizations.onboarding import submit_administrator_identity_verification
from apps.webhooks.services import queue_webhook_events
from apps.verification_sessions.serializers import (
    VerificationSessionConsentSerializer,
    VerificationSessionDocumentSerializer,
    VerificationSessionLivenessChallengeSerializer,
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
from common.authentication import (
    VerificationSessionAuthentication,
    require_verification_session_action,
)
from common.responses import success_response
from common.throttling import MobileHandoffRateThrottle, SensitivePublicRateThrottle


class VerificationSessionBaseView(APIView):
    authentication_classes = [VerificationSessionAuthentication]
    required_session_action = "session:read"

    def _enforce_public_throttle(self, request) -> None:
        throttle = SensitivePublicRateThrottle()
        if not throttle.allow_request(request, self):
            raise Throttled(wait=throttle.wait())

    def initial(self, request, *args, **kwargs):
        # Authenticate first so valid session traffic uses the existing
        # per-session controls instead of sharing a public IP bucket with every
        # user behind the verification portal or ingress. Invalid and missing
        # credentials are still bounded by the public anti-enumeration limit.
        try:
            self.perform_authentication(request)
        except APIException:
            self._enforce_public_throttle(request)
            raise
        if getattr(request, "verification_session", None) is None:
            self._enforce_public_throttle(request)
        super().initial(request, *args, **kwargs)
        require_verification_session_action(request, self.required_session_action)

    def _touch_session(self, request) -> None:
        verification_session = request.verification_session
        now = timezone.now()
        update_fields = [
            "last_seen_at",
            "ip_address",
            "user_agent",
            "device_fingerprint",
            "updated_at",
        ]

        verification_session.last_seen_at = now
        verification_session.ip_address = request.META.get("REMOTE_ADDR")
        verification_session.user_agent = request.headers.get("User-Agent", "")
        verification_session.device_fingerprint = request.headers.get(
            "X-Device-Fingerprint", ""
        )
        if verification_session.started_at is None:
            verification_session.started_at = now
            update_fields.append("started_at")
        if verification_session.status == VerificationSessionStatus.CREATED:
            verification_session.status = VerificationSessionStatus.ACTIVE
            update_fields.append("status")
        verification_session.save(update_fields=update_fields)

    def _lock_processing_consent(self, request, scope):
        from apps.consent.services import lock_session_consent

        lock_session_consent(request, scope=scope, action=self.required_session_action)


class VerificationSessionDetailView(VerificationSessionBaseView):
    def get(self, request, session_id: str):
        self._touch_session(request)
        return success_response(
            serialize_verification_session(request.verification_session, request),
            request=request,
        )


def _validate_handoff_source(source):
    if (
        source.expires_at <= timezone.now()
        or source.status
        not in {VerificationSessionStatus.CREATED, VerificationSessionStatus.ACTIVE}
        or source.tenant_id != source.verification.tenant_id
        or source.tenant.deleted_at is not None
        or source.tenant.status in {"suspended", "closed"}
        or source.verification.organization.deleted_at is not None
        or source.verification.deleted_at is not None
        or source.verification.status in TERMINAL_STATUSES
        or source.verification.expires_at <= timezone.now()
        or "mobile_handoff:create" not in source.allowed_actions
    ):
        raise ValidationError(
            {"handoff": "This mobile handoff link is invalid or expired."}
        )


class VerificationMobileHandoffCreateView(VerificationSessionBaseView):
    required_session_action = "mobile_handoff:create"

    @transaction.atomic
    def post(self, request, session_id):
        lock_audit_chain(request.tenant.pk)
        source_session = (
            VerificationSession.objects.select_for_update()
            .select_related("tenant", "verification")
            .get(pk=request.verification_session.pk)
        )
        _validate_handoff_source(source_session)
        request.verification_session = source_session
        self._touch_session(request)
        base = str(
            get_platform_setting_value(
                "integrations.verification_portal_base_url",
                settings.VERIFICATION_PORTAL_BASE_URL,
            )
        ).rstrip("/")
        parsed = urlsplit(base)
        if (
            not parsed.hostname
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
            or parsed.scheme not in ({"http", "https"} if settings.DEBUG else {"https"})
        ):
            raise ValidationError(
                {"detail": "The verification portal URL is unavailable."}
            )
        now = timezone.now()
        source_session.mobile_handoffs.filter(
            redeemed_at__isnull=True, expires_at__gt=now
        ).update(expires_at=now)
        raw_token = VerificationMobileHandoff.generate_token()
        expires_at = min(
            source_session.expires_at,
            source_session.verification.expires_at,
            now + timedelta(minutes=5),
        )
        handoff = VerificationMobileHandoff(
            source_session=source_session, expires_at=expires_at, token_hash=""
        )
        handoff.set_token(raw_token, generated=True)
        handoff.save()
        handoff_url = (
            f"{base}/{source_session.public_id}#handoff={handoff.public_id}.{raw_token}"
        )
        record_audit_event(
            tenant=request.tenant,
            actor=source_session.verification.verification_subject,
            request=request,
            action="verification.mobile_handoff_created",
            target_type="verification_session",
            target_id=source_session.public_id,
            metadata={
                "handoff_id": handoff.public_id,
                "expires_at": expires_at.isoformat(),
            },
        )
        return success_response(
            {"handoff_url": handoff_url, "expires_at": expires_at.isoformat()},
            request=request,
        )


class VerificationMobileHandoffRedeemView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [MobileHandoffRateThrottle]

    @transaction.atomic
    def post(self, request):
        if not isinstance(request.data, dict):
            raise ValidationError({"handoff": "This mobile handoff link is invalid."})
        handoff_value = request.data.get("handoff", "")
        expected_session = request.data.get("session_id", "")
        if (
            not isinstance(handoff_value, str)
            or len(handoff_value) > 192
            or not isinstance(expected_session, str)
            or not expected_session
            or len(expected_session) > 64
        ):
            raise ValidationError({"handoff": "This mobile handoff link is invalid."})
        handoff_id, separator, raw_token = handoff_value.partition(".")
        if not separator or not raw_token or len(raw_token) > 128:
            raise ValidationError({"handoff": "This mobile handoff link is invalid."})
        candidate = (
            VerificationMobileHandoff.objects.select_related("source_session")
            .filter(public_id=handoff_id, source_session__public_id=expected_session)
            .first()
        )
        if candidate is None:
            raise ValidationError({"handoff": "This mobile handoff link is invalid."})
        lock_audit_chain(candidate.source_session.tenant_id)
        source = (
            VerificationSession.objects.select_for_update()
            .select_related("tenant", "verification")
            .get(pk=candidate.source_session_id)
        )
        handoff = VerificationMobileHandoff.objects.select_for_update().get(
            pk=candidate.pk
        )
        if (
            not handoff.matches_token(raw_token)
            or handoff.redeemed_at is not None
            or handoff.expires_at <= timezone.now()
        ):
            raise ValidationError(
                {"handoff": "This mobile handoff link is invalid or expired."}
            )
        _validate_handoff_source(source)
        session_token = VerificationSession.generate_session_token()
        mobile_session = VerificationSession(
            verification=source.verification,
            tenant=source.tenant,
            expires_at=min(source.expires_at, source.verification.expires_at),
            allowed_actions_json=list(source.allowed_actions),
        )
        mobile_session.set_session_token(session_token, generated=True)
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
            metadata={
                "handoff_id": handoff.public_id,
                "source_session_id": source.public_id,
            },
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
    required_session_action = "consent:accept"

    @transaction.atomic
    def post(self, request, session_id: str):
        from apps.verifications.models import Verification

        lock_audit_chain(request.tenant.pk)
        Verification.objects.select_for_update(no_key=True).get(
            pk=request.verification_session.verification_id
        )
        request.verification_session = (
            VerificationSession.objects.select_for_update(no_key=True)
            .select_related("verification")
            .get(pk=request.verification_session.pk)
        )
        if (
            request.verification_session.status
            not in {VerificationSessionStatus.CREATED, VerificationSessionStatus.ACTIVE}
            or request.verification_session.expires_at <= timezone.now()
        ):
            raise ValidationError("This consent session is unavailable.")
        self._touch_session(request)
        serializer = VerificationSessionConsentSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        consent_record = serializer.save()
        verification = request.verification_session.verification
        if getattr(consent_record, "_already_existing", False):
            return success_response(
                {
                    "consent_record_id": consent_record.public_id,
                    "next_step": "document_capture",
                },
                request=request,
            )
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
    required_session_action = "document:capture"

    @transaction.atomic
    def post(self, request, session_id: str):
        self._lock_processing_consent(request, "document")
        self._touch_session(request)
        serializer = VerificationSessionDocumentSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        identity_document = serializer.save()
        verification = request.verification_session.verification
        if getattr(serializer, "created", True):
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
            queue_identity_document_processing(identity_document)
        return success_response(
            {
                "identity_document_id": identity_document.public_id,
                "status": identity_document.status,
                "next_step": "document_processing",
            },
            request=request,
        )


class VerificationSessionSelfieView(VerificationSessionBaseView):
    required_session_action = "selfie:capture"

    @transaction.atomic
    def post(self, request, session_id: str):
        self._lock_processing_consent(request, "biometrics")
        self._touch_session(request)
        serializer = VerificationSessionSelfieSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        selfie_capture = serializer.save()
        verification = request.verification_session.verification
        if serializer.created:
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
    required_session_action = "liveness:submit"

    @transaction.atomic
    def post(self, request, session_id: str):
        self._lock_processing_consent(request, "biometrics")
        self._touch_session(request)
        serializer = VerificationSessionLivenessSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        liveness_check = serializer.save()
        verification = request.verification_session.verification
        if getattr(serializer, "created", True):
            if (
                verification.metadata_json.get("workflow") == "administrator_onboarding"
                and verification.created_by is not None
            ):
                submit_administrator_identity_verification(
                    user=verification.created_by,
                    verification_id=verification.public_id,
                    request=request,
                )
            queue_biometrics_processing(liveness_check)
        return success_response(
            {
                "liveness_check_id": liveness_check.public_id,
                "status": "processing",
            },
            request=request,
        )


class VerificationSessionLivenessChallengeView(VerificationSessionBaseView):
    required_session_action = "liveness:challenge"

    @transaction.atomic
    def post(self, request, session_id: str):
        self._lock_processing_consent(request, "biometrics")
        self._touch_session(request)
        serializer = VerificationSessionLivenessChallengeSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        challenge = serializer.save()
        record_audit_event(
            tenant=request.tenant,
            actor=request.verification_session.verification.verification_subject,
            request=request,
            action="liveness.challenge_issued",
            target_type="verification_session",
            target_id=request.verification_session.public_id,
            metadata={
                "challenge_id": challenge.public_id,
                "expires_at": challenge.expires_at.isoformat(),
            },
        )
        return success_response(
            {
                "challenge_id": challenge.public_id,
                "actions": challenge.actions,
                "expires_at": challenge.expires_at.isoformat(),
                "expires_in": max(
                    0, int((challenge.expires_at - timezone.now()).total_seconds())
                ),
            },
            request=request,
        )


class VerificationSessionStatusView(VerificationSessionBaseView):
    required_session_action = "session:read"

    def get(self, request, session_id: str):
        self._touch_session(request)
        return success_response(
            serialize_verification_session_status(request.verification_session),
            request=request,
        )


class VerificationSessionConsentWithdrawView(VerificationSessionBaseView):
    allow_consent_withdrawal_replay = True
    required_session_action = "consent:accept"

    def post(self, request, session_id):
        from apps.consent.services import withdraw
        from django.core.exceptions import ValidationError as ConsentError

        record = (
            request.verification_session.verification.consent_records.filter(
                accepted=True
            )
            .order_by("-accepted_at", "-pk")
            .first()
        )
        if record is None:
            raise ValidationError("No consent proof is available.")
        try:
            record = withdraw(
                record,
                actor=request.verification_session.verification.verification_subject,
                request=request,
            )
        except ConsentError:
            raise ValidationError("Consent withdrawal is unavailable.") from None
        return success_response(
            {
                "consent_record_id": record.public_id,
                "withdrawn_at": record.withdrawn_at.isoformat(),
            },
            request=request,
        )
