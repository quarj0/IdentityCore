from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.providers.models import Provider
from apps.providers.serializers import serialize_provider, serialize_provider_check
from common.permissions import IsTenantUser
from common.responses import success_response


class ProviderListView(APIView):
    permission_classes = [IsAuthenticated, IsTenantUser]

    def get(self, request):
        providers = Provider.objects.order_by("provider_type", "name")
        return success_response(
            {"results": [serialize_provider(provider) for provider in providers]},
            request=request,
        )


class ProviderCheckListView(APIView):
    permission_classes = [IsAuthenticated, IsTenantUser]

    def get(self, request):
        provider_checks = request.user.tenant.provider_checks.select_related(
            "verification", "provider"
        ).order_by("-started_at")
        verification_id = request.query_params.get("verification_id")
        if verification_id:
            provider_checks = provider_checks.filter(
                verification__public_id=verification_id
            )
        return success_response(
            {
                "results": [
                    serialize_provider_check(provider_check)
                    for provider_check in provider_checks
                ]
            },
            request=request,
        )
