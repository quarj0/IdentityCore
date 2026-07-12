from django.shortcuts import get_object_or_404
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.views import APIView

from apps.api_clients.models import APIClient
from apps.api_clients.serializers import serialize_api_client
from apps.audit.models import AuditEvent
from apps.audit.serializers import serialize_audit_event
from apps.providers.models import Provider
from apps.providers.serializers import serialize_provider
from apps.verification_policies.models import VerificationPolicy
from apps.verification_policies.serializers import serialize_verification_policy
from apps.webhooks.models import WebhookEndpoint
from apps.webhooks.serializers import serialize_webhook_endpoint
from common.responses import success_response
from apps.verifications.serializers import paginate_results


class IsPlatformAdmin(BasePermission):
    message = "A platform administrator is required."

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and getattr(user, "is_platform_admin", False)
        )


class PlatformAdminBaseView(APIView):
    permission_classes = [IsAuthenticated, IsPlatformAdmin]


class PlatformAuditEventListView(PlatformAdminBaseView):
    def get(self, request):
        queryset = AuditEvent.objects.select_related("tenant").order_by("-created_at")
        actor_type = request.query_params.get("actor_type")
        action = request.query_params.get("action")
        target_type = request.query_params.get("target_type")
        target_id = request.query_params.get("target_id")
        created_from = request.query_params.get("created_from")
        created_to = request.query_params.get("created_to")

        if actor_type:
            queryset = queryset.filter(actor_type=actor_type)
        if action:
            queryset = queryset.filter(action=action)
        if target_type:
            queryset = queryset.filter(target_type=target_type)
        if target_id:
            queryset = queryset.filter(target_id=target_id)
        if created_from:
            queryset = queryset.filter(created_at__date__gte=created_from)
        if created_to:
            queryset = queryset.filter(created_at__date__lte=created_to)

        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))
        page_obj, pagination = paginate_results(queryset, page, page_size)
        return success_response(
            {
                "results": [serialize_audit_event(event) for event in page_obj.object_list],
                "pagination": pagination,
            },
            request=request,
        )


class PlatformAuditEventDetailView(PlatformAdminBaseView):
    def get(self, request, event_id):
        return success_response(
            serialize_audit_event(
                get_object_or_404(AuditEvent, public_id=event_id)
            ),
            request=request,
        )


class PlatformProviderListView(PlatformAdminBaseView):
    def get(self, request):
        providers = Provider.objects.order_by("provider_type", "name")
        return success_response(
            {"results": [serialize_provider(provider) for provider in providers]},
            request=request,
        )


class PlatformProviderDetailView(PlatformAdminBaseView):
    def get(self, request, provider_id):
        return success_response(
            serialize_provider(get_object_or_404(Provider, public_id=provider_id)),
            request=request,
        )


class PlatformVerificationPolicyListView(PlatformAdminBaseView):
    def get(self, request):
        queryset = VerificationPolicy.objects.select_related("tenant", "project").order_by(
            "name", "-version"
        )
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 50))
        page_obj, pagination = paginate_results(queryset, page, page_size)
        return success_response(
            {
                "results": [
                    serialize_verification_policy(policy)
                    for policy in page_obj.object_list
                ],
                "pagination": pagination,
            },
            request=request,
        )


class PlatformVerificationPolicyDetailView(PlatformAdminBaseView):
    def get(self, request, policy_id):
        return success_response(
            serialize_verification_policy(
                get_object_or_404(VerificationPolicy, public_id=policy_id)
            ),
            request=request,
        )


class PlatformAPIClientListView(PlatformAdminBaseView):
    def get(self, request):
        queryset = APIClient.objects.select_related("tenant", "project").order_by("name")
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 50))
        page_obj, pagination = paginate_results(queryset, page, page_size)
        return success_response(
            {
                "results": [
                    serialize_api_client(client) for client in page_obj.object_list
                ],
                "pagination": pagination,
            },
            request=request,
        )


class PlatformAPIClientDetailView(PlatformAdminBaseView):
    def get(self, request, client_id):
        return success_response(
            serialize_api_client(get_object_or_404(APIClient, public_id=client_id)),
            request=request,
        )


class PlatformWebhookEndpointListView(PlatformAdminBaseView):
    def get(self, request):
        queryset = WebhookEndpoint.objects.select_related("tenant", "project").order_by(
            "url"
        )
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 50))
        page_obj, pagination = paginate_results(queryset, page, page_size)
        return success_response(
            {
                "results": [
                    serialize_webhook_endpoint(endpoint)
                    for endpoint in page_obj.object_list
                ],
                "pagination": pagination,
            },
            request=request,
        )


class PlatformWebhookEndpointDetailView(PlatformAdminBaseView):
    def get(self, request, webhook_id):
        return success_response(
            serialize_webhook_endpoint(
                get_object_or_404(WebhookEndpoint, public_id=webhook_id)
            ),
            request=request,
        )

