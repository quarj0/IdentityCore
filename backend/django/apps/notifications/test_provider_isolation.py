from django.test import TestCase
from apps.organizations.models import Organization
from apps.tenants.models import Tenant
from apps.notifications.models import Notification
from apps.notifications.providers import (
    get_notification_provider,
    NotificationProviderNotConfigured,
)
from apps.providers.models import Provider, ProviderAssignment


class NotificationProviderIsolationTests(TestCase):
    def setUp(self):
        self.tenants = [
            Tenant.objects.create(
                organization=Organization.objects.create(
                    name=f"Synthetic {i}", slug=f"synthetic-{i}"
                ),
                name=f"Synthetic {i}",
                slug=f"synthetic-{i}",
            )
            for i in range(2)
        ]
        self.foreign = Provider.objects.create(
            tenant=self.tenants[1],
            name="A foreign provider",
            code="foreign-email",
            provider_type="notification",
            status="active",
            configuration_json={
                "channel": "email",
                "password": "synthetic-foreign-credential",
            },
        )
        self.notification = Notification.objects.create(
            tenant=self.tenants[0],
            recipient="synthetic@example.test",
            recipient_type="platform_user",
            channel="email",
        )

    def test_unassigned_tenant_does_not_use_foreign_provider_credentials(self):
        provider = get_notification_provider(self.notification)
        self.assertNotEqual(provider.provider_code, self.foreign.code)
        self.assertNotIn("synthetic-foreign-credential", str(provider.configuration))

    def test_platform_default_is_used_without_considering_foreign_tenant(self):
        default = Provider.objects.create(
            name="Platform default",
            code="platform-email",
            provider_type="notification",
            status="active",
            configuration_json={"channel": "email"},
        )
        self.assertEqual(
            get_notification_provider(self.notification).provider_code, default.code
        )

    def test_corrupt_foreign_assignment_fails_closed(self):
        default = Provider.objects.create(
            name="Platform default",
            code="platform-email",
            provider_type="notification",
            status="active",
            configuration_json={"channel": "email"},
        )
        assignment = ProviderAssignment.objects.create(
            tenant=self.tenants[0],
            provider=default,
            assignment_key="notification_email",
            status="active",
        )
        ProviderAssignment.objects.filter(pk=assignment.pk).update(
            provider=self.foreign
        )
        with self.assertRaises(NotificationProviderNotConfigured):
            get_notification_provider(self.notification)
