"""Dashboard billing routes; intentionally not public machine API until versioned."""

from common.public_api import internal_api_path
from apps.billing.api_views import (
    BillingPlansView,
    BillingAccountView,
    BillingSubscribeView,
    BillingInvoiceListView,
    BillingInvoiceDetailView,
    BillingCheckoutView,
    BillingPaymentStatusView,
    PaystackWebhookView,
    StripeWebhookView,
)

urlpatterns = [
    internal_api_path("plans", BillingPlansView.as_view(), name="billing-plans"),
    internal_api_path("account", BillingAccountView.as_view(), name="billing-account"),
    internal_api_path(
        "subscribe", BillingSubscribeView.as_view(), name="billing-subscribe"
    ),
    internal_api_path(
        "invoices", BillingInvoiceListView.as_view(), name="billing-invoices"
    ),
    internal_api_path(
        "invoices/<str:invoice_id>",
        BillingInvoiceDetailView.as_view(),
        name="billing-invoice-detail",
    ),
    internal_api_path(
        "invoices/<str:invoice_id>/checkout",
        BillingCheckoutView.as_view(),
        name="billing-checkout",
    ),
    internal_api_path(
        "payments/<str:payment_id>",
        BillingPaymentStatusView.as_view(),
        name="billing-payment",
    ),
    internal_api_path(
        "paystack/webhook",
        PaystackWebhookView.as_view(),
        name="billing-paystack-webhook",
    ),
    internal_api_path(
        "stripe/webhook", StripeWebhookView.as_view(), name="billing-stripe-webhook"
    ),
]
