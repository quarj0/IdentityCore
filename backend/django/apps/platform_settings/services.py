from __future__ import annotations

from typing import Any

from django.utils import timezone

from apps.platform_settings.models import PlatformSetting, PlatformSettingRevision


PLATFORM_SETTING_DEFINITIONS: dict[str, dict[str, Any]] = {
    "security.admin_mfa_required": {
        "group": "security",
        "title": "Admin MFA required",
        "description": "Require multi-factor authentication for platform admin accounts.",
        "value_type": "boolean",
        "default_value": True,
        "is_editable": True,
        "is_secret": False,
        "requires_restart": False,
    },
    "security.session_timeout_minutes": {
        "group": "security",
        "title": "Session timeout",
        "description": "Default session lifetime for platform users.",
        "value_type": "integer",
        "default_value": 60,
        "is_editable": True,
        "is_secret": False,
        "requires_restart": False,
    },
    "accounts.support_email": {
        "group": "accounts",
        "title": "Support email",
        "description": "Default support contact shown in platform-admin and notifications.",
        "value_type": "string",
        "default_value": "support@identitycore.local",
        "is_editable": True,
        "is_secret": False,
        "requires_restart": False,
    },
    "integrations.verification_portal_base_url": {
        "group": "integrations",
        "title": "Verification portal URL",
        "description": "Base URL used for hosted verification links.",
        "value_type": "url",
        "default_value": "http://localhost:3002/verify",
        "is_editable": True,
        "is_secret": False,
        "requires_restart": False,
    },
    "integrations.ai_service_base_url": {
        "group": "integrations",
        "title": "AI service URL",
        "description": "Internal AI service endpoint used by provider orchestration.",
        "value_type": "url",
        "default_value": "http://localhost:8001",
        "is_editable": True,
        "is_secret": False,
        "requires_restart": False,
    },
    "integrations.ai_service_shared_token": {
        "group": "integrations",
        "title": "AI service shared token",
        "description": "Optional shared token used to authenticate internal AI service calls.",
        "value_type": "secret",
        "default_value": "",
        "is_editable": True,
        "is_secret": True,
        "requires_restart": False,
    },
    "integrations.ai_service_timeout_seconds": {
        "group": "integrations",
        "title": "AI service timeout",
        "description": "Timeout applied to AI service requests.",
        "value_type": "integer",
        "default_value": 15,
        "is_editable": True,
        "is_secret": False,
        "requires_restart": False,
    },
    "storage.object_storage_bucket": {
        "group": "storage",
        "title": "Object storage bucket",
        "description": "Default bucket used for uploads and media.",
        "value_type": "string",
        "default_value": "",
        "is_editable": True,
        "is_secret": False,
        "requires_restart": False,
    },
    "storage.object_storage_provider": {
        "group": "storage",
        "title": "Object storage provider",
        "description": "Default object storage provider name.",
        "value_type": "string",
        "default_value": "",
        "is_editable": True,
        "is_secret": False,
        "requires_restart": False,
    },
    "storage.object_storage_endpoint_url": {
        "group": "storage",
        "title": "Object storage endpoint",
        "description": "Endpoint used for S3-compatible object storage.",
        "value_type": "url",
        "default_value": "",
        "is_editable": True,
        "is_secret": False,
        "requires_restart": False,
    },
    "storage.object_storage_media_bucket": {
        "group": "storage",
        "title": "Media bucket",
        "description": "Bucket used for promoted media and verification evidence.",
        "value_type": "string",
        "default_value": "",
        "is_editable": True,
        "is_secret": False,
        "requires_restart": False,
    },
    "storage.object_storage_temp_bucket": {
        "group": "storage",
        "title": "Temporary upload bucket",
        "description": "Bucket used for temporary upload storage.",
        "value_type": "string",
        "default_value": "",
        "is_editable": True,
        "is_secret": False,
        "requires_restart": False,
    },
    "storage.object_storage_evidence_bucket": {
        "group": "storage",
        "title": "Evidence bucket",
        "description": "Bucket used for immutable evidence records.",
        "value_type": "string",
        "default_value": "",
        "is_editable": True,
        "is_secret": False,
        "requires_restart": False,
    },
    "storage.object_storage_public_bucket": {
        "group": "storage",
        "title": "Public assets bucket",
        "description": "Bucket used for public assets.",
        "value_type": "string",
        "default_value": "",
        "is_editable": True,
        "is_secret": False,
        "requires_restart": False,
    },
    "notifications.default_from_email": {
        "group": "notifications",
        "title": "Default from email",
        "description": "Default sender identity for email notifications.",
        "value_type": "string",
        "default_value": "no-reply@identitycore.local",
        "is_editable": True,
        "is_secret": False,
        "requires_restart": False,
    },
    "notifications.email_provider_code": {
        "group": "notifications",
        "title": "Email provider code",
        "description": "Default platform email provider code.",
        "value_type": "string",
        "default_value": "default-email",
        "is_editable": True,
        "is_secret": False,
        "requires_restart": False,
    },
    "notifications.sms_provider_code": {
        "group": "notifications",
        "title": "SMS provider code",
        "description": "Default platform SMS provider code.",
        "value_type": "string",
        "default_value": "default-sms",
        "is_editable": True,
        "is_secret": False,
        "requires_restart": False,
    },
}


def get_platform_setting_definition(key: str) -> dict[str, Any] | None:
    return PLATFORM_SETTING_DEFINITIONS.get(key)


def get_platform_setting_queryset():
    return PlatformSetting.objects.select_related("created_by", "updated_by")


def get_platform_setting_record(key: str) -> PlatformSetting | None:
    return PlatformSetting.objects.filter(key=key).first()


def get_platform_setting_value(key: str, default: Any = None) -> Any:
    definition = get_platform_setting_definition(key)
    if definition is None:
        return default
    setting = get_platform_setting_record(key)
    if setting is None:
        return definition["default_value"]
    value = setting.effective_value
    return definition["default_value"] if value == {} else value


def list_platform_settings() -> list[dict[str, Any]]:
    rows = []
    for key, definition in PLATFORM_SETTING_DEFINITIONS.items():
        setting = get_platform_setting_record(key)
        value = definition["default_value"] if setting is None else setting.effective_value
        rows.append(
            {
                "id": setting.public_id if setting else key,
                "key": key,
                "group": definition["group"],
                "title": definition["title"],
                "description": definition["description"],
                "value_type": definition["value_type"],
                "status": setting.status if setting else "active",
                "value": value,
                "default_value": definition["default_value"],
                "is_editable": definition["is_editable"],
                "is_secret": definition["is_secret"],
                "requires_restart": definition["requires_restart"],
                "created_at": setting.created_at.isoformat() if setting else None,
                "updated_at": setting.updated_at.isoformat() if setting else None,
                "updated_by_email": setting.updated_by.email if setting and setting.updated_by else None,
            }
        )
    return rows


def upsert_platform_setting(*, key: str, value: Any, changed_by=None, change_reason: str = "") -> PlatformSetting:
    definition = get_platform_setting_definition(key)
    if definition is None:
        raise KeyError(key)
    setting = PlatformSetting.objects.filter(key=key).first()
    if setting is None:
        setting = PlatformSetting(
            key=key,
            group=definition["group"],
            title=definition["title"],
            description=definition["description"],
            value_type=definition["value_type"],
            default_value_json=definition["default_value"],
            current_value_json=value,
            is_editable=definition["is_editable"],
            is_secret=definition["is_secret"],
            requires_restart=definition["requires_restart"],
            created_by=changed_by,
            updated_by=changed_by,
        )
        setting.save()
        PlatformSettingRevision.objects.create(
            setting=setting,
            old_value_json=definition["default_value"],
            new_value_json=value,
            change_reason=change_reason,
            changed_by=changed_by,
        )
        return setting
    previous = setting.effective_value
    setting.current_value_json = value
    setting.updated_by = changed_by
    setting.save(update_fields=["current_value_json", "updated_by", "updated_at"])
    PlatformSettingRevision.objects.create(
        setting=setting,
        old_value_json=previous,
        new_value_json=value,
        change_reason=change_reason,
        changed_by=changed_by,
    )
    return setting


def reset_platform_setting(*, key: str, changed_by=None, change_reason: str = "") -> PlatformSetting:
    definition = get_platform_setting_definition(key)
    if definition is None:
        raise KeyError(key)
    return upsert_platform_setting(
        key=key,
        value=definition["default_value"],
        changed_by=changed_by,
        change_reason=change_reason or "reset to default",
    )
