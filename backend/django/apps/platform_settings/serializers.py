from apps.platform_settings.models import PlatformSetting, PlatformSettingRevision


def serialize_platform_setting(setting: PlatformSetting) -> dict:
    return {
        "id": setting.public_id,
        "key": setting.key,
        "group": setting.group,
        "title": setting.title,
        "description": setting.description,
        "value_type": setting.value_type,
        "status": setting.status,
        "value": setting.effective_value,
        "default_value": setting.default_value_json,
        "is_editable": setting.is_editable,
        "is_secret": setting.is_secret,
        "requires_restart": setting.requires_restart,
        "created_at": setting.created_at.isoformat(),
        "updated_at": setting.updated_at.isoformat(),
        "updated_by_email": setting.updated_by.email if setting.updated_by else None,
    }


def serialize_platform_setting_revision(revision: PlatformSettingRevision) -> dict:
    return {
        "id": revision.public_id,
        "setting_id": revision.setting.public_id,
        "old_value": revision.old_value_json,
        "new_value": revision.new_value_json,
        "change_reason": revision.change_reason,
        "changed_by_email": revision.changed_by.email if revision.changed_by else None,
        "created_at": revision.created_at.isoformat(),
        "updated_at": revision.updated_at.isoformat(),
    }
