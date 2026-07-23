from django.test import TestCase

from apps.platform_settings.models import PlatformSettingRevision
from apps.platform_settings.services import (
    get_platform_setting_value,
    reset_platform_setting,
    upsert_platform_setting,
)


class PlatformSettingsTests(TestCase):
    def test_caller_fallback_is_used_when_no_database_override_exists(self):
        self.assertEqual(
            get_platform_setting_value(
                "integrations.ai_service_base_url",
                "http://ai-service:8001",
            ),
            "http://ai-service:8001",
        )

    def test_definition_default_is_used_when_caller_omits_fallback(self):
        self.assertEqual(
            get_platform_setting_value("integrations.ai_service_base_url"),
            "http://localhost:8001",
        )

    def test_upsert_and_reset_platform_setting_records_revisions(self):
        setting = upsert_platform_setting(
            key="security.session_timeout_minutes",
            value=45,
            change_reason="tighten idle timeout",
        )

        self.assertEqual(setting.effective_value, 45)
        self.assertEqual(
            get_platform_setting_value("security.session_timeout_minutes"), 45
        )
        self.assertEqual(PlatformSettingRevision.objects.count(), 1)

        reset_setting = reset_platform_setting(
            key="security.session_timeout_minutes",
            change_reason="restore default",
        )

        self.assertEqual(reset_setting.effective_value, 60)
        self.assertEqual(PlatformSettingRevision.objects.count(), 2)

