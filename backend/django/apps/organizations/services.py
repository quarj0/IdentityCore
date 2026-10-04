import secrets
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
        f"{ORGANIZATION_BRANDING_SEGMENTS[asset_type]}/{secrets.token_hex(16)}{extension}"
    )


def build_organization_branding_upload(
    *,
    organization: Organization,
    asset_type: str,
    filename: str,
    mime_type: str,
    file_size_bytes: int,
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
            content_length=file_size_bytes,
            bucket_name=get_object_storage_public_bucket_name(),
        ),
        "asset_url": build_public_asset_url(storage_key),
    }


def update_organization_branding_settings(
    *,
    organization: Organization,
    environment: str = "sandbox",
    logo_storage_key: str | None = None,
    branding_image_storage_keys: list[str] | None = None,
    primary_color: str | None = None,
    primary_text_color: str | None = None,
    background_color: str | None = None,
    publish: bool = False,
) -> Organization:
    settings_json = dict(organization.settings_json or {})
    environments = dict(settings_json.get("branding_environments") or {})
    environment_state = dict(environments.get(environment) or {})
    draft = dict(
        environment_state.get("draft")
        or {
            "logo_storage_key": settings_json.get("logo_storage_key", ""),
            "logo_url": settings_json.get("logo_url", ""),
            "primary_color": settings_json.get("primary_color", "#2563eb"),
            "primary_text_color": settings_json.get("primary_text_color", "#ffffff"),
            "background_color": settings_json.get("background_color", "#ffffff"),
        }
    )
    if logo_storage_key is not None:
        draft["logo_storage_key"] = logo_storage_key
        draft["logo_url"] = build_public_asset_url(logo_storage_key)
    if primary_color is not None:
        draft["primary_color"] = primary_color
    if primary_text_color is not None:
        draft["primary_text_color"] = primary_text_color
    if background_color is not None:
        draft["background_color"] = background_color
    if branding_image_storage_keys is not None:
        settings_json["branding_image_storage_keys"] = branding_image_storage_keys
        settings_json["branding_image_urls"] = [
            build_public_asset_url(storage_key)
            for storage_key in branding_image_storage_keys
        ]

    environment_state["draft"] = draft
    if publish:
        environment_state["published"] = dict(draft)
    environments[environment] = environment_state
    settings_json["branding_environments"] = environments

    organization.settings_json = settings_json
    organization.save(update_fields=["settings_json", "updated_at"])
    return organization
