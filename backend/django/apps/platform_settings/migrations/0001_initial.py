# Generated manually for platform settings.

import common.fields
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="PlatformSetting",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                (
                    "public_id",
                    models.CharField(editable=False, max_length=64, unique=True),
                ),
                ("key", models.CharField(max_length=120, unique=True)),
                ("group", models.CharField(db_index=True, max_length=64)),
                ("title", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True)),
                (
                    "value_type",
                    models.CharField(
                        choices=[
                            ("string", "String"),
                            ("boolean", "Boolean"),
                            ("integer", "Integer"),
                            ("decimal", "Decimal"),
                            ("json", "JSON"),
                            ("secret", "Secret"),
                            ("url", "URL"),
                            ("enum", "Enum"),
                        ],
                        default="string",
                        max_length=32,
                    ),
                ),
                (
                    "default_value_json",
                    common.fields.EncryptedJSONField(
                        blank=True,
                        default=dict,
                        encryption_purpose="platform_settings.default_value",
                    ),
                ),
                (
                    "current_value_json",
                    common.fields.EncryptedJSONField(
                        blank=True,
                        default=dict,
                        encryption_purpose="platform_settings.current_value",
                    ),
                ),
                ("is_editable", models.BooleanField(default=True)),
                ("is_secret", models.BooleanField(default=False)),
                ("requires_restart", models.BooleanField(default=False)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("active", "Active"),
                            ("disabled", "Disabled"),
                            ("deprecated", "Deprecated"),
                        ],
                        db_index=True,
                        default="active",
                        max_length=32,
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="created_platform_settings",
                        to="accounts.platformuser",
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="updated_platform_settings",
                        to="accounts.platformuser",
                    ),
                ),
            ],
            options={
                "ordering": ["group", "title"],
            },
        ),
        migrations.CreateModel(
            name="PlatformSettingRevision",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                (
                    "public_id",
                    models.CharField(editable=False, max_length=64, unique=True),
                ),
                (
                    "old_value_json",
                    common.fields.EncryptedJSONField(
                        blank=True,
                        default=dict,
                        encryption_purpose="platform_settings.revision.old_value",
                    ),
                ),
                (
                    "new_value_json",
                    common.fields.EncryptedJSONField(
                        blank=True,
                        default=dict,
                        encryption_purpose="platform_settings.revision.new_value",
                    ),
                ),
                ("change_reason", models.TextField(blank=True)),
                (
                    "changed_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="platform_setting_revisions",
                        to="accounts.platformuser",
                    ),
                ),
                (
                    "setting",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="revisions",
                        to="platform_settings.platformsetting",
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
    ]
