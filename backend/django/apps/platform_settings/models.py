from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import BaseModel, PublicIdModel
from common.fields import EncryptedJSONField


class PlatformSettingStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    DISABLED = "disabled", "Disabled"
    DEPRECATED = "deprecated", "Deprecated"


class PlatformSettingValueType(models.TextChoices):
    STRING = "string", "String"
    BOOLEAN = "boolean", "Boolean"
    INTEGER = "integer", "Integer"
    DECIMAL = "decimal", "Decimal"
    JSON = "json", "JSON"
    SECRET = "secret", "Secret"
    URL = "url", "URL"
    ENUM = "enum", "Enum"


class PlatformSetting(PublicIdModel, BaseModel):
    public_id_prefix = "pst"

    key = models.CharField(max_length=120, unique=True)
    group = models.CharField(max_length=64, db_index=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    value_type = models.CharField(
        max_length=32,
        choices=PlatformSettingValueType.choices,
        default=PlatformSettingValueType.STRING,
    )
    default_value_json = EncryptedJSONField(
        default=dict,
        blank=True,
        encryption_purpose="platform_settings.default_value",
    )
    current_value_json = EncryptedJSONField(
        default=dict,
        blank=True,
        encryption_purpose="platform_settings.current_value",
    )
    is_editable = models.BooleanField(default=True)
    is_secret = models.BooleanField(default=False)
    requires_restart = models.BooleanField(default=False)
    status = models.CharField(
        max_length=32,
        choices=PlatformSettingStatus.choices,
        default=PlatformSettingStatus.ACTIVE,
        db_index=True,
    )
    created_by = models.ForeignKey(
        "accounts.PlatformUser",
        on_delete=models.PROTECT,
        related_name="created_platform_settings",
        null=True,
        blank=True,
    )
    updated_by = models.ForeignKey(
        "accounts.PlatformUser",
        on_delete=models.PROTECT,
        related_name="updated_platform_settings",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["group", "title"]

    def clean(self):
        super().clean()
        if self.key != self.key.strip().lower():
            raise ValidationError({"key": "Use lowercase snake_case or dot notation."})

    @property
    def effective_value(self):
        return self.current_value_json if self.current_value_json != {} else self.default_value_json

    def __str__(self) -> str:
        return self.key


class PlatformSettingRevision(PublicIdModel, BaseModel):
    public_id_prefix = "psr"

    setting = models.ForeignKey(
        PlatformSetting,
        on_delete=models.CASCADE,
        related_name="revisions",
    )
    old_value_json = EncryptedJSONField(
        default=dict,
        blank=True,
        encryption_purpose="platform_settings.revision.old_value",
    )
    new_value_json = EncryptedJSONField(
        default=dict,
        blank=True,
        encryption_purpose="platform_settings.revision.new_value",
    )
    change_reason = models.TextField(blank=True)
    changed_by = models.ForeignKey(
        "accounts.PlatformUser",
        on_delete=models.PROTECT,
        related_name="platform_setting_revisions",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.public_id
