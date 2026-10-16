"""Invoice completed activity independently of a subscription's current state."""

from datetime import datetime, timedelta, timezone as utc
from unittest.mock import patch
from django.test import TestCase, override_settings
from apps.billing import test_commercial as fixtures
from apps.billing.models import BillingInvoice
from apps.billing.services import BillingError, generate_invoice
from apps.billing.tasks import generate_closed_month_invoices_task


class SubscriptionPeriodTests(TestCase):
    setUp = fixtures.CommercialBillingTests.setUp
    usage = fixtures.CommercialBillingTests.usage

    def moment(self, day):
        return datetime.combine(
            self.period_start + timedelta(days=day - 1), datetime.min.time(), utc.utc
        ) + timedelta(hours=12)

    def change_status(self, status, day=None):
        from django.utils import timezone

        with patch(
            "django.utils.timezone.now",
            return_value=self.moment(day) if day is not None else timezone.now(),
        ):
            self.subscription.status = status
            self.subscription.save(update_fields=["status"])

    def usage_at(self, day):
        event = self.usage(self.provider)
        event.occurred_at = self.moment(day)
        event.save(update_fields=["occurred_at"])
        event.provider_check.started_at = event.provider_check.completed_at = (
            event.occurred_at
        )
        event.provider_check.save(update_fields=["started_at", "completed_at"])
        return event

    def test_pause_after_month_close_preserves_accrued_invoice(self):
        self.usage_at(4)
        self.change_status("paused")
        self.assertEqual(generate_invoice(self.tenant, self.month).amount_minor, 10500)

    def test_cancellation_after_month_close_preserves_accrued_invoice(self):
        self.usage_at(4)
        self.change_status("cancelled")
        self.assertEqual(generate_invoice(self.tenant, self.month).amount_minor, 10500)

    @override_settings(BILLING_AUTO_INVOICE_ENABLED=True)
    def test_scheduled_close_includes_deactivated_subscription(self):
        self.usage_at(4)
        self.change_status("cancelled")
        self.assertEqual(generate_closed_month_invoices_task(), 1)
        self.assertEqual(
            BillingInvoice.objects.get(tenant=self.tenant).status, "issued"
        )

    def test_partial_active_month_bills_only_active_usage_without_base_fee(self):
        active = self.usage_at(4)
        paused = self.usage_at(12)
        self.change_status("paused", 10)
        invoice = generate_invoice(self.tenant, self.month)
        self.assertEqual(invoice.amount_minor, 500)
        active.refresh_from_db()
        paused.refresh_from_db()
        self.assertEqual(active.rating_state, "rated")
        self.assertEqual(paused.rating_state, "unrated")

    def test_pause_and_resume_preserves_both_active_windows(self):
        self.usage_at(4)
        gap = self.usage_at(12)
        self.usage_at(20)
        self.change_status("paused", 10)
        self.change_status("active", 15)
        invoice = generate_invoice(self.tenant, self.month)
        self.assertEqual(invoice.amount_minor, 1000)
        gap.refresh_from_db()
        self.assertEqual(gap.rating_state, "unrated")

    def test_no_invoice_for_month_after_activity_ended(self):
        self.change_status("cancelled", 0)
        with self.assertRaises(BillingError):
            generate_invoice(self.tenant, self.month)
        self.assertFalse(BillingInvoice.objects.exists())

    def test_unknown_legacy_activity_blocks_invoice_instead_of_inventing_history(self):
        self.subscription.history_recorded_from = self.moment(15)
        self.subscription.save(update_fields=["history_recorded_from"])
        with self.assertRaisesMessage(BillingError, "history requires operator review"):
            generate_invoice(self.tenant, self.month)
        self.assertFalse(BillingInvoice.objects.exists())

    def test_recorded_periods_cannot_overlap_or_rewrite_closed_history(self):
        from django.core.exceptions import ValidationError
        from apps.billing.models import BillingSubscriptionPeriod

        with self.assertRaises(ValidationError):
            BillingSubscriptionPeriod.objects.create(
                subscription=self.subscription, started_at=self.moment(4)
            )
        self.change_status("paused", 10)
        period = self.subscription.periods.get()
        period.ended_at = self.moment(12)
        with self.assertRaises(ValidationError):
            period.save()

    def test_invoiced_start_date_cannot_be_rewritten(self):
        from django.core.exceptions import ValidationError

        generate_invoice(self.tenant, self.month)
        self.subscription.started_at = self.moment(4)
        with self.assertRaises(ValidationError):
            self.subscription.save(update_fields=["started_at"])
