import re

from rest_framework import serializers
from django.utils import timezone

from apps.organizations.models import Organization, OrganizationSupportingDocument
from common.storage import build_public_asset_url
from pathlib import Path
import secrets
from apps.organizations.services import (
    ORGANIZATION_BRANDING_SEGMENTS,
    build_organization_branding_upload,
)


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
    tenant = organization.tenant
    month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    pending = organization.status != "active"
    return {
        "id": organization.public_id,
        "name": organization.name,
        "slug": organization.slug,
        "industry": organization.industry,
        "status": organization.status,
        "tenant_id": tenant.public_id,
        "tenant_name": tenant.name,
        "tenant_status": tenant.status,
        "default_country_profile_id": organization.default_country_profile_id,
        "default_jurisdiction_id": organization.default_jurisdiction_id,
        "settings": settings_json,
        "sandbox_usage": {
            "pending_approval": pending,
            "projects": tenant.projects.count(), "project_limit": 1 if pending else None,
            "api_keys": tenant.api_clients.exclude(status="revoked").count(), "api_key_limit": 1 if pending else None,
            "workflows": tenant.workflows.count(), "workflow_limit": 1 if pending else None,
            "webhooks": tenant.webhook_endpoints.count(), "webhook_limit": 1 if pending else None,
            "monthly_verifications": tenant.verifications.filter(created_at__gte=month_start).count(),
            "monthly_verification_limit": 25 if pending else None,
        },
        "created_at": organization.created_at.isoformat(),
        "updated_at": organization.updated_at.isoformat(),
    }


def _color_luminance(value: str) -> float:
    channels = [int(value[index : index + 2], 16) / 255 for index in (1, 3, 5)]
    linear = [
        channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4
        for channel in channels
    ]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _contrast_ratio(foreground: str, background: str) -> float:
    first, second = sorted(
        (_color_luminance(foreground), _color_luminance(background)),
        reverse=True,
    )
    return (first + 0.05) / (second + 0.05)


class OrganizationBrandingAssetUploadSerializer(serializers.Serializer):
    asset_type = serializers.ChoiceField(choices=tuple(ORGANIZATION_BRANDING_SEGMENTS.items()))
    filename = serializers.CharField(max_length=255)
    mime_type = serializers.CharField(max_length=100)
    file_size_bytes = serializers.IntegerField(min_value=1, max_value=5 * 1024 * 1024)

    def validate(self, attrs):
        extensions = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".webp": "image/webp",
        }
        extension = Path(attrs["filename"]).suffix.lower()
        mime_type = attrs["mime_type"].lower()
        if extension not in extensions:
            raise serializers.ValidationError(
                {"filename": "Use a PNG, JPEG, or WebP branding image. SVG is not supported."}
            )
        if mime_type != extensions[extension]:
            raise serializers.ValidationError(
                {"mime_type": "The image type must match the file extension."}
            )
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
    primary_color = serializers.RegexField(r"^#[0-9a-fA-F]{6}$", required=False)
    primary_text_color = serializers.RegexField(r"^#[0-9a-fA-F]{6}$", required=False)
    background_color = serializers.RegexField(r"^#[0-9a-fA-F]{6}$", required=False)
    publish = serializers.BooleanField(default=False, required=False)
    environment = serializers.ChoiceField(
        choices=("sandbox", "production"),
        default="sandbox",
        required=False,
    )

    def validate_logo_storage_key(self, value):
        organization = self.context["request"].user.tenant.organization
        expected_prefix = f"organizations/{organization.public_id}/branding/logos/"
        if not value.startswith(expected_prefix):
            raise serializers.ValidationError("Logo must be stored in the organization public branding path.")
        if Path(value).suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
            raise serializers.ValidationError("Only raster branding images can be published.")
        return value

    def validate_branding_image_storage_keys(self, value):
        organization = self.context["request"].user.tenant.organization
        expected_prefix = f"organizations/{organization.public_id}/branding/branding-images/"
        for storage_key in value:
            if not storage_key.startswith(expected_prefix):
                raise serializers.ValidationError("Branding images must be stored in the organization public branding path.")
            if Path(storage_key).suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
                raise serializers.ValidationError("Only raster branding images are supported.")
        return value

    def validate(self, attrs):
        if not attrs.get("publish"):
            return attrs
        organization = self.context["request"].user.tenant.organization
        settings_json = organization.settings_json or {}
        environment = attrs.get("environment", "sandbox")
        environment_state = (
            settings_json.get("branding_environments", {}).get(environment, {})
        )
        current = environment_state.get("draft") or {}
        candidate = {
            "primary_color": attrs.get("primary_color", current.get("primary_color", "#2563eb")),
            "primary_text_color": attrs.get("primary_text_color", current.get("primary_text_color", "#ffffff")),
            "background_color": attrs.get("background_color", current.get("background_color", "#ffffff")),
        }
        if _contrast_ratio(candidate["primary_color"], candidate["primary_text_color"]) < 4.5:
            raise serializers.ValidationError(
                {"primary_text_color": "Published button colors must meet WCAG AA contrast (4.5:1)."}
            )
        if _contrast_ratio(candidate["background_color"], "#111827") < 4.5:
            raise serializers.ValidationError(
                {"background_color": "The primary text on this background must meet WCAG AA contrast (4.5:1)."}
            )
        return attrs


class OrganizationDocumentUploadSerializer(serializers.Serializer):
    filename = serializers.CharField(max_length=255)
    mime_type = serializers.CharField(max_length=100)
    file_size_bytes = serializers.IntegerField(min_value=1, max_value=10 * 1024 * 1024)

    def validate(self, attrs):
        if attrs["mime_type"].lower() != "application/pdf" or Path(attrs["filename"]).suffix.lower() != ".pdf":
            raise serializers.ValidationError({"filename": "Choose a PDF document."})
        tenant = self.context["request"].user.tenant
        if tenant.organization.supporting_documents.filter(deleted_at__isnull=True).count() >= 5:
            raise serializers.ValidationError({"filename": "A maximum of five supporting documents is allowed."})
        return attrs

    def create(self, validated_data):
        user = self.context["request"].user
        organization = user.tenant.organization
        key = f"organizations/{organization.public_id}/verification/{secrets.token_urlsafe(16)}.pdf"
        document = OrganizationSupportingDocument.objects.create(
            organization=organization, tenant=user.tenant, uploaded_by=user,
            storage_key=key, status="initiated", **validated_data,
        )
        return {"document_id": document.public_id, "filename": document.filename,
                "file_size_bytes": document.file_size_bytes, "status": document.status,
                "storage_key": key, "download_url": build_public_asset_url(key),
                "upload_url": f"/organization/me/verification-documents/{document.public_id}/content/"}
