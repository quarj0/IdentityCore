from datetime import timedelta

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.settings import api_settings
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.audit.services import record_audit_event
from apps.platform_settings.services import get_platform_setting_value
from apps.notifications.services import (
    queue_verification_created_notifications,
    queue_verification_status_notifications,
)
from apps.verifications.evidence import (
    build_verification_evidence_download_url,
    build_verification_evidence_pdf_download_url,
    download_verification_evidence_object,
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


class VerificationAccessMixin:
    authentication_classes = [
        APIClientAuthentication,
        *api_settings.DEFAULT_AUTHENTICATION_CLASSES,
    ]

    def _is_api_client_request(self, request) -> bool:
        return getattr(request, "api_client", None) is not None

    def _get_tenant(self, request):
        if self._is_api_client_request(request):
            return request.tenant
        return request.user.tenant

    def _get_actor(self, request):
        if self._is_api_client_request(request):
            return request.api_client
        return request.user

    def _set_request_tenant(self, request) -> None:
        if not hasattr(request, "tenant") or request.tenant is None:
            request.tenant = self._get_tenant(request)

    def get_permissions(self):
        if self._is_api_client_request(self.request):
            return [HasAPIClientScopes()]
        return [IsAuthenticated(), IsTenantUser()]


class VerificationListCreateView(VerificationAccessMixin, APIView):

    def get_permissions(self):
        self.required_scopes = (
            ("verifications:read",)
            if self.request.method == "GET"
            else ("verifications:create",)
        )
        return super().get_permissions()

    def get(self, request):
        verifications = self._get_tenant(request).verifications.select_related(
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
        self._set_request_tenant(request)
        tenant = self._get_tenant(request)
        if tenant.organization.status != "active":
            month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if tenant.verifications.filter(created_at__gte=month_start).count() >= 25:
                from rest_framework.exceptions import Throttled
                raise Throttled(detail="The pending-workspace sandbox limit is 25 verification requests per month.")
        serializer = VerificationCreateSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        verification = serializer.save()
        session = verification._initial_session
        record_audit_event(
            tenant=self._get_tenant(request),
            actor=self._get_actor(request),
            request=request,
            action="verification.created",
            target_type="verification",
            target_id=verification.public_id,
            metadata={"session_id": session.public_id},
        )
        queue_webhook_events(
            tenant=self._get_tenant(request),
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
                "session_token": verification._initial_session_token,
                "expires_at": verification.expires_at.isoformat(),
            },
            request=request,
            status=status.HTTP_201_CREATED,
        )


class VerificationDetailView(VerificationAccessMixin, APIView):
    required_scopes = ("verifications:read",)

    def get(self, request, verification_id: str):
        verification = get_object_or_404(
            Verification.objects.select_related("verification_subject"),
            tenant=self._get_tenant(request),
            public_id=verification_id,
        )
        return success_response(
            serialize_verification(verification, request=request),
            request=request,
        )


class VerificationCancelView(VerificationAccessMixin, APIView):
    required_scopes = ("verifications:create",)

    def post(self, request, verification_id: str):
        verification = get_object_or_404(
            Verification,
            tenant=self._get_tenant(request),
            public_id=verification_id,
        )
        serializer = VerificationCancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        verification.status = VerificationStatus.CANCELLED
        verification.cancelled_at = timezone.now()
        verification.save(update_fields=["status", "cancelled_at", "updated_at"])
        record_audit_event(
            tenant=self._get_tenant(request),
            actor=self._get_actor(request),
            request=request,
            action="verification.cancelled",
            target_type="verification",
            target_id=verification.public_id,
            metadata={"reason": serializer.validated_data.get("reason", "")},
            sensitive_metadata={"reason": serializer.validated_data.get("reason", "")},
        )
        queue_webhook_events(
            tenant=self._get_tenant(request),
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


class VerificationResendLinkView(VerificationAccessMixin, APIView):
    required_scopes = ("verifications:create",)

    def post(self, request, verification_id: str):
        verification = get_object_or_404(
            Verification.objects.select_related("verification_subject", "tenant"),
            tenant=self._get_tenant(request),
            public_id=verification_id,
        )
        serializer = VerificationResendLinkSerializer(data=request.data or {})
        serializer.is_valid(raise_exception=True)

        verification.sessions.exclude(status="revoked").update(status="revoked")
        raw_session_token = VerificationSession.generate_session_token()
        session = VerificationSession(
            verification=verification,
            tenant=verification.tenant,
            expires_at=max(verification.expires_at, timezone.now() + timedelta(minutes=10)),
        )
        session.set_session_token(raw_session_token)
        session.save()

        verification_url = (
            f"{str(get_platform_setting_value('integrations.verification_portal_base_url', settings.VERIFICATION_PORTAL_BASE_URL)).rstrip('/')}/{session.public_id}"
            f"#token={raw_session_token}&verification_id={verification.public_id}"
        )
        notifications = queue_verification_created_notifications(
            verification=verification,
            verification_url=verification_url,
        )
        record_audit_event(
            tenant=self._get_tenant(request),
            actor=self._get_actor(request),
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
            {
                "sent": bool(notifications),
                "verification_url": verification_url,
                "session_id": session.public_id,
                "session_token": raw_session_token,
                "expires_at": session.expires_at.isoformat(),
                "channel": serializer.validated_data["channel"],
            },
            request=request,
            status=status.HTTP_200_OK,
        )


class VerificationEvidenceReportView(VerificationAccessMixin, APIView):
    required_scopes = ("verifications:read",)

    def get(self, request, verification_id: str):
        verification = get_object_or_404(
            Verification.objects.select_related("verification_subject", "organization"),
            tenant=self._get_tenant(request),
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
                "download_url": build_verification_evidence_download_url(
                    verification,
                    request=request,
                ),
                "pdf_storage_key": verification.metadata_json.get(
                    "evidence_report_pdf_storage_key", ""
                ),
                "pdf_download_url": build_verification_evidence_pdf_download_url(
                    verification,
                    request=request,
                ),
            },
            request=request,
        )


class VerificationEvidenceReportDownloadView(VerificationAccessMixin, APIView):
    required_scopes = ("verifications:read",)

    def get(self, request, verification_id: str):
        verification = get_object_or_404(
            Verification.objects.select_related("verification_subject", "organization"),
            tenant=self._get_tenant(request),
            public_id=verification_id,
        )
        ensure_verification_evidence_report(verification)
        content, content_type, filename = download_verification_evidence_object(
            verification,
            pdf=False,
        )
        response = HttpResponse(content, content_type=content_type)
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


class VerificationEvidenceReportPDFDownloadView(VerificationAccessMixin, APIView):
    required_scopes = ("verifications:read",)

    def get(self, request, verification_id: str):
        verification = get_object_or_404(
            Verification.objects.select_related("verification_subject", "organization"),
            tenant=self._get_tenant(request),
            public_id=verification_id,
        )
        ensure_verification_evidence_report(verification)
        content, content_type, filename = download_verification_evidence_object(
            verification,
            pdf=True,
        )
        response = HttpResponse(content, content_type=content_type)
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response


class ManualReviewListView(APIView):
    permission_classes = [IsAuthenticated, IsTenantUser]

    def get(self, request):
        verifications = request.user.tenant.verifications.select_related(
            "verification_subject"
        ).filter(status=VerificationStatus.MANUAL_REVIEW_REQUIRED).order_by("-created_at")
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
