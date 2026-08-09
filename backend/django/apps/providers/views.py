from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.providers.health import provider_health_scope
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
            "verification",
            "provider",
            "execution_attempt__route",
            "execution_attempt__route_step",
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


class ProviderHealthView(APIView):
    permission_classes = [IsAuthenticated, IsTenantUser]

    def get(self, request):
        environment = request.query_params.get("environment", "")
        if environment not in {"sandbox", "production"}:
            return Response(
                {
                    "error": {
                        "code": "invalid_environment",
                        "message": "Choose the sandbox or production environment.",
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            window_hours = int(request.query_params.get("window_hours", "24"))
        except ValueError:
            window_hours = 0
        if not 1 <= window_hours <= 720:
            return Response(
                {
                    "error": {
                        "code": "invalid_window",
                        "message": "Window hours must be between 1 and 720.",
                    }
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        return success_response(
            provider_health_scope(
                tenant=request.user.tenant,
                environment=environment,
                window_hours=window_hours,
            ),
            request=request,
        )
