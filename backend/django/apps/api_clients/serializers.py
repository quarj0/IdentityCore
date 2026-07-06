from django.utils import timezone
from rest_framework import serializers

from apps.api_clients.models import APIClient
from apps.organizations.models import OrganizationStatus


def serialize_api_client(api_client: APIClient, include_secret: str | None = None) -> dict:
    payload = {
        "public_id": api_client.public_id,
        "tenant_public_id": api_client.tenant.public_id,
        "name": api_client.name,
        "client_id": api_client.client_id,
        "status": api_client.status,
        "scopes": api_client.scopes,
        "allowed_networks": api_client.allowed_ips,
        "rate_limit_per_minute": api_client.rate_limit_per_minute,
        "last_used_at": api_client.last_used_at.isoformat() if api_client.last_used_at else None,
        "created_at": api_client.created_at.isoformat(),
        "updated_at": api_client.updated_at.isoformat(),
    }
    if include_secret is not None:
        payload["client_secret"] = include_secret
    return payload


class APIClientCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    scopes = serializers.ListField(child=serializers.CharField(max_length=120), allow_empty=False)
    allowed_networks = serializers.ListField(
        child=serializers.CharField(max_length=64),
        allow_empty=True,
        required=False,
        default=list,
    )
    rate_limit_per_minute = serializers.IntegerField(min_value=1, default=60)

    def validate(self, attrs):
        tenant = self.context["request"].user.tenant
        organization = tenant.organization
        if organization.status != OrganizationStatus.ACTIVE:
            raise serializers.ValidationError(
                {
                    "detail": (
                        "Production API keys are unavailable until the organization "
                        "has completed platform approval."
                    )
                }
            )
        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        user = request.user
        tenant = user.tenant
        raw_secret = APIClient.generate_client_secret()
        api_client = APIClient(
            tenant=tenant,
            created_by=user,
            name=validated_data["name"],
            scopes_json=validated_data["scopes"],
            allowed_ips_json=validated_data["allowed_networks"],
            rate_limit_per_minute=validated_data["rate_limit_per_minute"],
        )
        api_client.set_client_secret(raw_secret)
        api_client.save()
        api_client._raw_client_secret = raw_secret
        return api_client


class APIClientAuthenticationResultSerializer(serializers.Serializer):
    client_id = serializers.CharField()
    client_secret = serializers.CharField()

    def validate(self, attrs):
        try:
            api_client = APIClient.objects.select_related("tenant").get(client_id=attrs["client_id"])
        except APIClient.DoesNotExist as exc:
            raise serializers.ValidationError({"detail": "Invalid API client credentials."}) from exc

        if api_client.status != api_client.APIClientStatus.ACTIVE:
            raise serializers.ValidationError({"detail": "API client is not active."})
        if not api_client.verify_client_secret(attrs["client_secret"]):
            raise serializers.ValidationError({"detail": "Invalid API client credentials."})

        api_client.last_used_at = timezone.now()
        api_client.save(update_fields=["last_used_at", "updated_at"])
        attrs["api_client"] = api_client
        return attrs
