from rest_framework import serializers

from apps.organizations.models import Organization
from apps.organizations.services import (
    ORGANIZATION_BRANDING_SEGMENTS,
    build_organization_branding_upload,
)
from common.storage import build_public_asset_url


def serialize_organization(organization: Organization) -> dict:
    settings_json = dict(organization.settings_json or {})
    logo_storage_key = settings_json.get("logo_storage_key", "")
    if logo_storage_key:
        settings_json["logo_url"] = build_public_asset_url(logo_storage_key)
    branding_image_storage_keys = settings_json.get("branding_image_storage_keys", [])
    if branding_image_storage_keys:
        settings_json["branding_image_urls"] = [
            build_public_asset_url(storage_key)
            for storage_key in branding_image_storage_keys
        ]
    return {
        "id": organization.public_id,
        "name": organization.name,
        "slug": organization.slug,
        "industry": organization.industry,
        "status": organization.status,
        "default_country_profile_id": organization.default_country_profile_id,
        "default_jurisdiction_id": organization.default_jurisdiction_id,
        "settings": settings_json,
        "created_at": organization.created_at.isoformat(),
        "updated_at": organization.updated_at.isoformat(),
    }


class OrganizationBrandingAssetUploadSerializer(serializers.Serializer):
    asset_type = serializers.ChoiceField(choices=tuple(ORGANIZATION_BRANDING_SEGMENTS.items()))
    filename = serializers.CharField(max_length=255)
    mime_type = serializers.CharField(max_length=100)

    def validate(self, attrs):
        filename = attrs["filename"].lower()
        mime_type = attrs["mime_type"].lower()
        if not any(filename.endswith(ext) for ext in (".png", ".jpg", ".jpeg", ".svg", ".webp")):
            raise serializers.ValidationError({"filename": "Unsupported branding asset file type."})
        if not (
            mime_type.startswith("image/")
            or mime_type == "image/svg+xml"
        ):
            raise serializers.ValidationError({"mime_type": "Branding assets must be image files."})
        return attrs

    def create(self, validated_data):
        organization = self.context["request"].user.tenant.organization
        return build_organization_branding_upload(
            organization=organization,
            asset_type=validated_data["asset_type"],
            filename=validated_data["filename"],
            mime_type=validated_data["mime_type"],
        )


class OrganizationBrandingUpdateSerializer(serializers.Serializer):
    logo_storage_key = serializers.CharField(max_length=255, required=False, allow_blank=False)
    branding_image_storage_keys = serializers.ListField(
        child=serializers.CharField(max_length=255),
        required=False,
        allow_empty=True,
    )

    def validate_logo_storage_key(self, value):
        organization = self.context["request"].user.tenant.organization
        expected_prefix = f"organizations/{organization.public_id}/branding/logos/"
        if not value.startswith(expected_prefix):
            raise serializers.ValidationError("Logo must be stored in the organization public branding path.")
        return value

    def validate_branding_image_storage_keys(self, value):
        organization = self.context["request"].user.tenant.organization
        expected_prefix = f"organizations/{organization.public_id}/branding/branding-images/"
        for storage_key in value:
            if not storage_key.startswith(expected_prefix):
                raise serializers.ValidationError(
                    "Branding images must be stored in the organization public branding path."
                )
        return value
