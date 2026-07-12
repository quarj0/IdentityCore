from django.test import TestCase

from apps.platform_settings.models import PlatformSettingRevision
from apps.platform_settings.services import (
    get_platform_setting_value,
    reset_platform_setting,
    upsert_platform_setting,
)


class PlatformSettingsTests(TestCase):
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

