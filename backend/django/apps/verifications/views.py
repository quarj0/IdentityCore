from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.audit.services import record_audit_event
from apps.notifications.services import (
    queue_verification_created_notifications,
    queue_verification_status_notifications,
)
from apps.verifications.evidence import (
    build_verification_evidence_download_url,
    build_verification_evidence_pdf_download_url,
    ensure_verification_evidence_report,
)
from apps.webhooks.services import queue_webhook_events
from apps.verifications.serializers import (
    ManualReviewDecisionSerializer,
    VerificationCancelSerializer,
    VerificationCreateSerializer,
    VerificationResendLinkSerializer,
    paginate_results,
    serialize_manual_review_summary,
    serialize_verification,
    serialize_verification_summary,
)
from apps.verifications.models import (
    Verification,
    VerificationSession,
    VerificationStatus,
)
from common.authentication import APIClientAuthentication
from common.permissions import HasAPIClientScopes, IsTenantUser
from common.responses import success_response


class VerificationListCreateView(APIView):
    authentication_classes = [APIClientAuthentication]

    def get_permissions(self):
        if self.request.method == "GET":
            self.required_scopes = ("verifications:read",)
        else:
            self.required_scopes = ("verifications:create",)
        return [HasAPIClientScopes()]

    def get(self, request):
        verifications = request.tenant.verifications.select_related(
            "verification_subject"
        ).order_by("-created_at")

        status_value = request.query_params.get("status")
        external_reference = request.query_params.get("external_reference")
        if status_value:
            verifications = verifications.filter(status=status_value)
        if external_reference:
            verifications = verifications.filter(external_reference=external_reference)

        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))
        page_obj, pagination = paginate_results(verifications, page, page_size)
        return success_response(
            {
                "results": [
                    serialize_verification_summary(item)
                    for item in page_obj.object_list
                ],
                "pagination": pagination,
            },
            request=request,
        )

    def post(self, request):
        serializer = VerificationCreateSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        verification = serializer.save()
        session = verification._initial_session
        record_audit_event(
            tenant=request.tenant,
            actor=request.api_client,
            request=request,
            action="verification.created",
            target_type="verification",
            target_id=verification.public_id,
            metadata={"session_id": session.public_id},
        )
        queue_webhook_events(
            tenant=request.tenant,
            event_type="verification.created",
            payload={
                "verification_id": verification.public_id,
                "external_reference": verification.external_reference,
                "status": verification.status,
            },
        )
        queue_verification_created_notifications(
            verification=verification,
            verification_url=verification._verification_url,
        )
        return success_response(
            {
                "id": verification.public_id,
                "status": verification.status,
                "verification_url": verification._verification_url,
                "session_id": session.public_id,
                "expires_at": verification.expires_at.isoformat(),
            },
            request=request,
            status=status.HTTP_201_CREATED,
        )


class VerificationDetailView(APIView):
    authentication_classes = [APIClientAuthentication]
    required_scopes = ("verifications:read",)
    permission_classes = [HasAPIClientScopes]

    def get(self, request, verification_id: str):
        verification = get_object_or_404(
            Verification.objects.select_related("verification_subject"),
            tenant=request.tenant,
            public_id=verification_id,
        )
        return success_response(serialize_verification(verification), request=request)


class VerificationCancelView(APIView):
    authentication_classes = [APIClientAuthentication]
    required_scopes = ("verifications:create",)
    permission_classes = [HasAPIClientScopes]

    def post(self, request, verification_id: str):
        verification = get_object_or_404(
            Verification,
            tenant=request.tenant,
            public_id=verification_id,
        )
        serializer = VerificationCancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        verification.status = VerificationStatus.CANCELLED
        verification.cancelled_at = timezone.now()
        verification.save(update_fields=["status", "cancelled_at", "updated_at"])
        record_audit_event(
            tenant=request.tenant,
            actor=request.api_client,
            request=request,
            action="verification.cancelled",
            target_type="verification",
            target_id=verification.public_id,
            metadata={"reason": serializer.validated_data.get("reason", "")},
            sensitive_metadata={"reason": serializer.validated_data.get("reason", "")},
        )
        queue_webhook_events(
            tenant=request.tenant,
            event_type="verification.cancelled",
            payload={
                "verification_id": verification.public_id,
                "external_reference": verification.external_reference,
                "status": verification.status,
            },
        )
        queue_verification_status_notifications(
            verification=verification,
            decision=VerificationStatus.CANCELLED,
        )
        ensure_verification_evidence_report(verification)
        return success_response(
            {
                "id": verification.public_id,
                "status": verification.status,
            },
            request=request,
        )


class VerificationResendLinkView(APIView):
    authentication_classes = [APIClientAuthentication]
    required_scopes = ("verifications:create",)
    permission_classes = [HasAPIClientScopes]

    def post(self, request, verification_id: str):
        verification = get_object_or_404(
            Verification.objects.select_related("verification_subject", "tenant"),
            tenant=request.tenant,
            public_id=verification_id,
        )
        serializer = VerificationResendLinkSerializer(data=request.data or {})
        serializer.is_valid(raise_exception=True)

        session = (
            verification.sessions.filter(expires_at__gt=timezone.now())
            .order_by("-created_at")
            .first()
        )
        if session is None:
            raw_session_token = VerificationSession.generate_session_token()
            session = VerificationSession(
                verification=verification,
                tenant=verification.tenant,
                expires_at=verification.expires_at,
            )
            session.set_session_token(raw_session_token)
            session.save()

        verification_url = (
            f"{settings.VERIFICATION_PORTAL_BASE_URL.rstrip('/')}/{session.public_id}"
        )
        notifications = queue_verification_created_notifications(
            verification=verification,
            verification_url=verification_url,
        )
        record_audit_event(
            tenant=request.tenant,
            actor=request.api_client,
            request=request,
            action="verification.link_resent",
            target_type="verification",
            target_id=verification.public_id,
            metadata={
                "channel": serializer.validated_data["channel"],
                "session_id": session.public_id,
            },
        )
        return success_response(
            {"sent": bool(notifications)},
            request=request,
            status=status.HTTP_200_OK,
        )


class VerificationEvidenceReportView(APIView):
    authentication_classes = [APIClientAuthentication]
    required_scopes = ("verifications:read",)
    permission_classes = [HasAPIClientScopes]

    def get(self, request, verification_id: str):
        verification = get_object_or_404(
            Verification.objects.select_related("verification_subject", "organization"),
            tenant=request.tenant,
            public_id=verification_id,
        )
        ensure_verification_evidence_report(verification)
        verification.refresh_from_db()
        return success_response(
            {
                "verification_id": verification.public_id,
                "storage_key": verification.metadata_json.get(
                    "evidence_report_storage_key", ""
                ),
                "download_url": build_verification_evidence_download_url(verification),
                "pdf_storage_key": verification.metadata_json.get(
                    "evidence_report_pdf_storage_key", ""
                ),
                "pdf_download_url": build_verification_evidence_pdf_download_url(
                    verification
                ),
            },
            request=request,
        )


class ManualReviewListView(APIView):
    permission_classes = [IsAuthenticated, IsTenantUser]

    def get(self, request):
        verifications = request.user.tenant.verifications.filter(
            status=VerificationStatus.MANUAL_REVIEW_REQUIRED
        ).order_by("-created_at")
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))
        page_obj, pagination = paginate_results(verifications, page, page_size)
        return success_response(
            {
                "results": [
                    serialize_manual_review_summary(item)
                    for item in page_obj.object_list
                ],
                "pagination": pagination,
            },
            request=request,
        )


class ManualReviewDecisionView(APIView):
    permission_classes = [IsAuthenticated, IsTenantUser]

    def post(self, request, verification_id: str):
        verification = get_object_or_404(
            Verification,
            tenant=request.user.tenant,
            public_id=verification_id,
        )
        serializer = ManualReviewDecisionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        decision_record = serializer.save(
            verification=verification, decided_by=request.user
        )
        record_audit_event(
            tenant=request.user.tenant,
            actor=request.user,
            request=request,
            action=f"verification.{decision_record.decision}",
            target_type="verification",
            target_id=verification.public_id,
            metadata={
                "decision_id": decision_record.public_id,
                "decision_type": decision_record.decision_type,
            },
            sensitive_metadata={"reason_detail": decision_record.reason_detail},
        )
        if decision_record.decision in {
            VerificationStatus.VERIFIED,
            VerificationStatus.REJECTED,
            VerificationStatus.MANUAL_REVIEW_REQUIRED,
        }:
            queue_webhook_events(
                tenant=request.user.tenant,
                event_type=f"verification.{decision_record.decision}",
                payload={
                    "verification_id": verification.public_id,
                    "external_reference": verification.external_reference,
                    "status": verification.status,
                },
            )
            risk_assessment = getattr(verification, "risk_assessment", None)
            queue_verification_status_notifications(
                verification=verification,
                decision=decision_record.decision,
                risk_level=(
                    risk_assessment.risk_level if risk_assessment is not None else ""
                ),
            )
        ensure_verification_evidence_report(verification)
        return success_response(
            {
                "verification_id": verification.public_id,
                "decision": decision_record.decision,
                "decision_type": decision_record.decision_type,
                "decided_at": decision_record.decided_at.isoformat(),
            },
            request=request,
            status=status.HTTP_200_OK,
        )
