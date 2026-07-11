from django.utils import timezone
from rest_framework import serializers

from apps.webhooks.models import SUPPORTED_WEBHOOK_EVENTS, WebhookEndpoint, WebhookEvent


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

    def create(self, validated_data):
        request = self.context["request"]
        raw_secret = WebhookEndpoint.generate_secret()
        endpoint = WebhookEndpoint(
            tenant=request.user.tenant,
            project=request.user.tenant.projects.filter(
                public_id=validated_data.get("project_id")
            ).first()
            or request.user.tenant.projects.filter(is_default=True).first(),
            url=validated_data["url"],
            description=validated_data.get("description", ""),
            events_json=validated_data["events"],
            created_by=request.user,
        )
        endpoint.set_secret(raw_secret)
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
