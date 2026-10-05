from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.consent.serializers import (
    serialize_consent_record,
    serialize_consent_template,
)
from common.permissions import IsTenantUser
from common.responses import success_response


class ConsentTemplateListView(APIView):
    permission_classes = [IsAuthenticated, IsTenantUser]

    def get(self, request):
        templates = request.user.tenant.consent_templates.order_by(
            "name", "-version", "language"
        )
        return success_response(
            {
                "results": [
                    serialize_consent_template(template) for template in templates
                ]
            },
            request=request,
        )


class ConsentRecordListView(APIView):
    permission_classes = [IsAuthenticated, IsTenantUser]

    def get(self, request):
        from common.authorization import AuthorizationAction, decide_user_access
        from rest_framework.exceptions import PermissionDenied
        if getattr(request.user, "is_platform_admin", False) or not decide_user_access(request.user, action=AuthorizationAction.TENANT_ACCESS, tenant=request.user.tenant, permission_code="manage_consent").allowed:
            raise PermissionDenied("Consent administration permission is required.")
        records = request.user.tenant.consent_records.select_related(
            "verification",
            "verification_subject",
            "consent_template",
        ).order_by("-accepted_at")
        return success_response(
            {"results": [serialize_consent_record(record) for record in records]},
            request=request,
        )


class ConsentWithdrawView(APIView):
    permission_classes = [IsAuthenticated, IsTenantUser]

    def post(self, request, record_id):
        from django.shortcuts import get_object_or_404
        from common.authorization import AuthorizationAction, decide_user_access
        from rest_framework.exceptions import PermissionDenied, ValidationError
        from django.core.exceptions import ValidationError as ConsentError
        from apps.consent.models import ConsentRecord
        from apps.consent.services import withdraw
        tenant = request.user.tenant
        if getattr(request.user, "is_platform_admin", False) or not decide_user_access(request.user, action=AuthorizationAction.TENANT_ACCESS, tenant=tenant, permission_code="manage_consent").allowed:
            raise PermissionDenied("Consent administration permission is required.")
        record = get_object_or_404(ConsentRecord, tenant=tenant, public_id=record_id, deleted_at__isnull=True)
        try:
            record = withdraw(record, actor=request.user, request=request)
        except ConsentError:
            raise ValidationError("Consent withdrawal is unavailable.") from None
        return success_response({"consent_record_id": record.public_id, "withdrawn_at": record.withdrawn_at.isoformat()}, request=request)
