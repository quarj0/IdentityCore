from pathlib import Path

from apps.organizations.models import Organization
from common.storage import (
    build_public_asset_url,
    build_signed_upload_url,
    get_object_storage_public_bucket_name,
)


ORGANIZATION_BRANDING_SEGMENTS = {
    "logo": "logos",
    "branding_image": "branding-images",
}


def build_public_branding_asset_key(
    *, organization: Organization, asset_type: str, filename: str
) -> str:
    extension = Path(filename).suffix.lower() or ".bin"
    return (
        f"organizations/{organization.public_id}/branding/"
        f"{ORGANIZATION_BRANDING_SEGMENTS[asset_type]}/{organization.public_id}{extension}"
    )


def build_organization_branding_upload(
    *, organization: Organization, asset_type: str, filename: str, mime_type: str
) -> dict:
    storage_key = build_public_branding_asset_key(
        organization=organization,
        asset_type=asset_type,
        filename=filename,
    )
    return {
        "asset_type": asset_type,
        "storage_key": storage_key,
        "bucket_name": get_object_storage_public_bucket_name(),
        "upload_url": build_signed_upload_url(
            storage_key=storage_key,
            mime_type=mime_type,
            bucket_name=get_object_storage_public_bucket_name(),
        ),
        "asset_url": build_public_asset_url(storage_key),
    }


def update_organization_branding_settings(
    *,
    organization: Organization,
    logo_storage_key: str | None = None,
    branding_image_storage_keys: list[str] | None = None,
) -> Organization:
    settings_json = dict(organization.settings_json or {})
    if logo_storage_key is not None:
        settings_json["logo_storage_key"] = logo_storage_key
        settings_json["logo_url"] = build_public_asset_url(logo_storage_key)
    if branding_image_storage_keys is not None:
        settings_json["branding_image_storage_keys"] = branding_image_storage_keys
        settings_json["branding_image_urls"] = [
            build_public_asset_url(storage_key)
            for storage_key in branding_image_storage_keys
        ]
    organization.settings_json = settings_json
    organization.save(update_fields=["settings_json", "updated_at"])
    return organization
