from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.risk.serializers import serialize_risk_assessment
from common.permissions import IsTenantUser
from common.responses import success_response


class RiskAssessmentListView(APIView):
    permission_classes = [IsAuthenticated, IsTenantUser]

    def get(self, request):
        risk_assessments = request.user.tenant.risk_assessments.select_related(
            "verification"
        ).order_by("-created_at")
        verification_id = request.query_params.get("verification_id")
        if verification_id:
            risk_assessments = risk_assessments.filter(
                verification__public_id=verification_id
            )
        return success_response(
            {
                "results": [
                    serialize_risk_assessment(risk_assessment)
                    for risk_assessment in risk_assessments
                ]
            },
            request=request,
        )
