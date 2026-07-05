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
        records = request.user.tenant.consent_records.select_related(
            "verification",
            "verification_subject",
            "consent_template",
        ).order_by("-accepted_at")
        return success_response(
            {"results": [serialize_consent_record(record) for record in records]},
            request=request,
        )
