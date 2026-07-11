from django.utils import timezone
from rest_framework import serializers

from apps.webhooks.models import SUPPORTED_WEBHOOK_EVENTS, WebhookEndpoint, WebhookEvent
from apps.organizations.models import OrganizationStatus


def serialize_webhook_endpoint(endpoint: WebhookEndpoint) -> dict:
    return {
        "id": endpoint.public_id,
        "project_id": endpoint.project.public_id if endpoint.project else None,
        "url": endpoint.url,
        "description": endpoint.description,
        "events": endpoint.events,
        "status": endpoint.status,
        "created_at": endpoint.created_at.isoformat(),
        "updated_at": endpoint.updated_at.isoformat(),
    }


class WebhookEndpointCreateSerializer(serializers.Serializer):
    project_id = serializers.CharField(required=False, allow_blank=True)
    url = serializers.URLField()
    description = serializers.CharField(required=False, allow_blank=True)
    events = serializers.ListField(
        child=serializers.CharField(max_length=120),
        allow_empty=False,
    )

    def validate_events(self, value):
        invalid = sorted(set(value) - SUPPORTED_WEBHOOK_EVENTS)
        if invalid:
            raise serializers.ValidationError(
                f"Unsupported webhook events: {', '.join(invalid)}"
            )
        return value

    def validate(self, attrs):
        tenant = self.context["request"].user.tenant
        if tenant.organization.status != OrganizationStatus.ACTIVE:
            if tenant.webhook_endpoints.exclude(status="disabled").exists() or tenant.webhook_endpoints.exists():
                raise serializers.ValidationError({"detail": "Pending workspaces are limited to one disabled test webhook."})
            project = tenant.projects.filter(public_id=attrs.get("project_id")).first() or tenant.projects.filter(is_default=True).first()
            if project is None or project.environment != "sandbox":
                raise serializers.ValidationError({"project_id": "Pending workspaces can configure webhooks only for the sandbox project."})
            attrs["resolved_project"] = project
        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        raw_secret = WebhookEndpoint.generate_secret()
        endpoint = WebhookEndpoint(
            tenant=request.user.tenant,
            project=validated_data.pop("resolved_project", None) or request.user.tenant.projects.filter(
                public_id=validated_data.get("project_id")
            ).first()
            or request.user.tenant.projects.filter(is_default=True).first(),
            url=validated_data["url"],
            description=validated_data.get("description", ""),
            events_json=validated_data["events"],
            created_by=request.user,
        )
        endpoint.set_secret(raw_secret)
        if request.user.tenant.organization.status != OrganizationStatus.ACTIVE:
            endpoint.status = "disabled"
        endpoint.save()
        endpoint._raw_secret = raw_secret
        return endpoint


class WebhookTestSerializer(serializers.Serializer):
    pass

    def save(self, *, endpoint: WebhookEndpoint):
        payload = {
            "id": "evt_test",
            "type": "webhook.test",
            "created_at": timezone.now().isoformat(),
            "data": {
                "webhook_id": endpoint.public_id,
                "status": "test",
            },
        }
        return WebhookEvent.objects.create(
            tenant=endpoint.tenant,
            webhook_endpoint=endpoint,
            event_type="webhook.test",
            payload_json=payload,
        )
