"""Operator financial records: money-state changes go through services only."""

from django.contrib import admin
from django.core.exceptions import PermissionDenied

from apps.billing.models import (
    BillingPlan,
    BillingMeter,
    BillingSubscription,
    BillingInvoice,
    BillingInvoiceLine,
    BillingPayment,
    BillingPaymentEvent,
    BillingRefund,
    BillingDispute,
    BillingUsageEvent,
)


class ReadOnlyFinancialAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class MeterInline(admin.TabularInline):
    model = BillingMeter
    extra = 0

    def has_add_permission(self, request, obj=None):
        return bool(obj and not obj.published)

    def has_change_permission(self, request, obj=None):
        return bool(obj and not obj.published)

    def has_delete_permission(self, request, obj=None):
        return bool(obj and not obj.published)


@admin.register(BillingPlan)
class PlanAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "version",
        "name",
        "currency",
        "monthly_price_minor",
        "published",
    )
    inlines = [MeterInline]

    def get_readonly_fields(self, request, obj=None):
        return (
            ("code", "version", "name", "currency", "monthly_price_minor", "published")
            if obj and obj.published
            else ()
        )

    def has_delete_permission(self, request, obj=None):
        return bool(obj is not None and not obj.published)


@admin.register(BillingSubscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("tenant", "plan", "status", "started_at")

    def get_readonly_fields(self, request, obj=None):
        return ("tenant", "plan", "started_at") if obj else ()


for model in (
    BillingInvoice,
    BillingInvoiceLine,
    BillingPayment,
    BillingPaymentEvent,
    BillingRefund,
    BillingDispute,
    BillingUsageEvent,
    BillingMeter,
):
    admin.site.register(model, ReadOnlyFinancialAdmin)
