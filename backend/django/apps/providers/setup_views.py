"""Internal dashboard provider setup endpoints."""

from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.providers.configuration import (
    activate_configuration,
    assign_configuration,
    create_configuration,
    serialize_configuration,
    test_configuration,
)
from apps.providers.http_adapter import SecureHTTPAdapterError
from apps.providers.models import Provider, ProviderEnvironmentConfiguration
from apps.providers.serializers import serialize_provider
from common.permissions import IsTenantUser
from common.responses import error_response, success_response


class ProviderSetupView(APIView):
    permission_classes = [IsAuthenticated, IsTenantUser]
    required_permission_code = "manage_providers"

    def post(self, request):
        from apps.core.models import generate_public_id
        from apps.providers.manifests import validate_manifest

        payload = request.data
        try:
            if (
                set(payload) != {"name", "provider_type", "manifest"}
                or not isinstance(payload["name"], str)
                or not 1 <= len(payload["name"].strip()) <= 255
            ):
                raise ValidationError("Supply provider name, type and manifest.")
            validate_manifest(
                payload["manifest"], provider_type=payload["provider_type"]
            )
            provider = Provider.objects.create(
                tenant=request.user.tenant,
                name=payload["name"].strip(),
                provider_type=payload["provider_type"],
                code=generate_public_id("custom"),
                manifest_json=payload["manifest"],
            )
        except (ValidationError, TypeError, ValueError):
            return error_response(
                "provider_setup_invalid",
                "Check the provider declaration and name.",
                request=request,
            )
        return success_response(
            serialize_provider(provider), request=request, status=201
        )


class ProviderConfigurationListView(APIView):
    permission_classes = [IsAuthenticated, IsTenantUser]
    required_permission_code = "manage_providers"

    def get(self, request, provider_id):
        provider = get_object_or_404(
            Provider,
            public_id=provider_id,
            tenant=request.user.tenant,
            deleted_at__isnull=True,
        )
        configs = provider.environment_configurations.select_related(
            "provider", "source", "requested_by", "approved_by"
        )
        return success_response(
            {"results": [serialize_configuration(c) for c in configs]}, request=request
        )

    def post(self, request, provider_id):
        provider = get_object_or_404(
            Provider,
            public_id=provider_id,
            tenant=request.user.tenant,
            deleted_at__isnull=True,
        )
        payload = request.data
        try:
            if not isinstance(payload, dict) or set(payload) - {
                "environment",
                "configuration",
                "credentials",
                "source_id",
            }:
                raise ValidationError("Invalid configuration fields.")
            source = (
                get_object_or_404(
                    ProviderEnvironmentConfiguration,
                    public_id=payload["source_id"],
                    provider=provider,
                )
                if payload.get("source_id")
                else None
            )
            config = create_configuration(
                provider=provider,
                user=request.user,
                environment=payload.get("environment"),
                public_configuration=payload.get("configuration"),
                credentials=payload.get("credentials"),
                source=source,
            )
        except (ValidationError, SecureHTTPAdapterError, TypeError, ValueError):
            return error_response(
                "provider_configuration_invalid",
                "Check environment, endpoint, credentials and sandbox source.",
                request=request,
            )
        return success_response(
            serialize_configuration(config), request=request, status=201
        )


class ProviderConfigurationActionView(APIView):
    permission_classes = [IsAuthenticated, IsTenantUser]

    def post(self, request, configuration_id, action):
        config = get_object_or_404(
            ProviderEnvironmentConfiguration.objects.select_related(
                "provider", "source", "requested_by", "approved_by"
            ),
            public_id=configuration_id,
            provider__tenant=request.user.tenant,
            provider__deleted_at__isnull=True,
        )
        try:
            if action == "test":
                config = test_configuration(config=config, user=request.user)
            elif action == "activate":
                config = activate_configuration(config=config, user=request.user)
            elif action == "assign":
                route = assign_configuration(
                    config=config,
                    user=request.user,
                    capability=request.data.get("capability"),
                    countries=request.data.get("countries", []),
                    document_types=request.data.get("document_types", []),
                )
                return success_response(
                    {
                        "route_id": route.public_id,
                        "environment": route.environment,
                        "version": route.version,
                    },
                    request=request,
                )
            else:
                return error_response(
                    "provider_action_invalid",
                    "Choose test, activate or assign.",
                    request=request,
                )
        except PermissionError:
            return error_response(
                "permission_denied",
                "Provider configuration permission required.",
                request=request,
                status=403,
            )
        except (ValidationError, SecureHTTPAdapterError, TypeError, ValueError):
            return error_response(
                "provider_action_invalid",
                "The action failed its permission, connection or approval requirements.",
                request=request,
            )
        return success_response(serialize_configuration(config), request=request)
