from datetime import timedelta
from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from apps.accounts.models import PlatformUser, PlatformUserStatus
from apps.billing.models import BillingUsageEvent
from apps.billing.usage import BillingIntegrityError, record_provider_usage
from apps.organizations.models import Organization
from apps.projects.models import Project
from apps.providers.models import Provider, ProviderCheck, ProviderCheckStatus, ProviderCheckType, ProviderType
from apps.tenants.models import Tenant
from apps.verification_subjects.models import VerificationSubject
from apps.verifications.models import Verification


class UsageLedgerTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            name="Billing Test", slug="billing-test"
        )
        self.tenant = Tenant.objects.create(
            organization=self.organization, name="Billing Tenant",
            slug="billing-tenant", status="active",
        )
        self.user = PlatformUser.objects.create_user(
            email="billing-owner@example.com", password="SyntheticOnly123!",
            tenant=self.tenant, status=PlatformUserStatus.ACTIVE,
        )
        self.production = Project.objects.create(
            tenant=self.tenant, created_by=self.user, name="Prod",
            slug="prod", environment="production",
        )
        self.sandbox = Project.objects.create(
            tenant=self.tenant, created_by=self.user, name="Sandbox",
            slug="sandbox", environment="sandbox",
        )
        self.subject = VerificationSubject.objects.create(
            tenant=self.tenant, full_name="Synthetic Person"
        )
        self.platform_provider = Provider.objects.create(
            name="System test provider", code="billing-synthetic-platform",
            provider_type=ProviderType.LIVENESS,
        )
        self.byop_provider = Provider.objects.create(
            tenant=self.tenant, name="Tenant test provider",
            code="billing-synthetic-byop", provider_type=ProviderType.LIVENESS,
        )

    def make_check(self, project, provider, status=ProviderCheckStatus.COMPLETED):
        verification = Verification.objects.create(
            tenant=self.tenant, organization=self.organization,
            project=project, verification_subject=self.subject,
            purpose="Synthetic ledger regression",
            expires_at=timezone.now() + timedelta(hours=1),
        )
        return ProviderCheck.objects.create(
            tenant=self.tenant, verification=verification, provider=provider,
            check_type=ProviderCheckType.LIVENESS, status=status,
            started_at=timezone.now(),
            completed_at=timezone.now() if status != ProviderCheckStatus.PENDING else None,
        )

    def test_production_records_once_without_rating_or_charge(self):
        check = self.make_check(self.production, self.platform_provider)
        event, created = record_provider_usage(check.pk)
        self.assertTrue(created)
        self.assertEqual(event.quantity, 1)
        self.assertEqual(event.provider_scope, "platform")
        self.assertEqual(event.rating_state, "unrated")
        self.assertEqual(event.environment, "production")
        repeated, created = record_provider_usage(check.pk)
        self.assertFalse(created)
        self.assertEqual(event.pk, repeated.pk)
        self.assertEqual(BillingUsageEvent.objects.count(), 1)

    def test_byop_and_platform_usage_are_not_conflated(self):
        owned = self.make_check(self.production, self.byop_provider)
        managed = self.make_check(self.production, self.platform_provider)
        byop_event, _ = record_provider_usage(owned.pk)
        platform_event, _ = record_provider_usage(managed.pk)
        self.assertEqual(byop_event.provider_scope, "tenant_owned")
        self.assertEqual(platform_event.provider_scope, "platform")
        self.assertEqual(BillingUsageEvent.objects.count(), 2)

    def test_sandbox_and_pending_are_not_metered(self):
        sandbox = self.make_check(self.sandbox, self.platform_provider)
        pending = self.make_check(self.production, self.platform_provider, ProviderCheckStatus.PENDING)
        self.assertEqual(record_provider_usage(sandbox.pk), (None, False))
        self.assertEqual(record_provider_usage(pending.pk), (None, False))
        self.assertFalse(BillingUsageEvent.objects.exists())

    def test_terminal_failures_are_unrated_not_automatically_charged(self):
        failed = self.make_check(self.production, self.byop_provider, ProviderCheckStatus.FAILED)
        event, _ = record_provider_usage(failed.pk)
        self.assertEqual(event.outcome, ProviderCheckStatus.FAILED)
        self.assertEqual(event.rating_state, "unrated")

    def test_foreign_provider_is_not_attributed_to_customer(self):
        other_organization = Organization.objects.create(
            name="Other", slug="billing-other"
        )
        other_tenant = Tenant.objects.create(
            organization=other_organization, name="Other Tenant",
            slug="billing-other", status="active",
        )
        foreign = Provider.objects.create(
            tenant=other_tenant, name="Wrong provider",
            code="billing-foreign", provider_type=ProviderType.LIVENESS,
        )
        check = self.make_check(self.production, foreign)
        with self.assertRaises(BillingIntegrityError):
            record_provider_usage(check.pk)
        self.assertFalse(BillingUsageEvent.objects.exists())

    def test_recorded_status_cannot_silently_change(self):
        check = self.make_check(self.production, self.platform_provider)
        record_provider_usage(check.pk)
        ProviderCheck.objects.filter(pk=check.pk).update(status=ProviderCheckStatus.FAILED)
        with self.assertRaises(BillingIntegrityError):
            record_provider_usage(check.pk)
        self.assertEqual(BillingUsageEvent.objects.count(), 1)

    def test_operator_reconciliation_is_idempotent(self):
        self.make_check(self.production, self.byop_provider)
        self.make_check(self.sandbox, self.platform_provider)
        output = StringIO()
        call_command(
            "reconcile_provider_usage", tenant=self.tenant.public_id,
            limit=10, stdout=output
        )
        self.assertIn("recorded=1", output.getvalue())
        output = StringIO()
        call_command(
            "reconcile_provider_usage", tenant=self.tenant.public_id,
            limit=10, stdout=output
        )
        self.assertIn("recorded=0", output.getvalue())
        self.assertEqual(BillingUsageEvent.objects.count(), 1)
