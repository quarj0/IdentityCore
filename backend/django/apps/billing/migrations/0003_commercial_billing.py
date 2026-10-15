"""Plan, metering, invoicing, hosted checkout and payment reconciliation."""
import django.db.models.deletion
from django.db import migrations, models


def common():
    return [
        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
        ("created_at", models.DateTimeField(auto_now_add=True)),
        ("updated_at", models.DateTimeField(auto_now=True)),
        ("deleted_at", models.DateTimeField(blank=True, null=True)),
        ("public_id", models.CharField(editable=False, max_length=64, unique=True)),
    ]


class Migration(migrations.Migration):
    dependencies = [
        ("billing", "0002_billingusageevent"),
    ]
    operations = [
        migrations.CreateModel(
            name="BillingPlan",
            fields=common() + [
                ("code", models.SlugField(max_length=80, unique=True)),
                ("version", models.PositiveIntegerField(default=1)),
                ("name", models.CharField(max_length=120)),
                ("currency", models.CharField(default="GHS", max_length=3)),
                ("monthly_price_minor", models.PositiveBigIntegerField(default=0)),
                ("published", models.BooleanField(default=False)),
            ],
        ),
        migrations.AddConstraint(
            model_name="billingplan",
            constraint=models.UniqueConstraint(fields=("code", "version"), name="billing_plan_code_version"),
        ),
        migrations.CreateModel(
            name="BillingMeter",
            fields=common() + [
                ("provider_scope", models.CharField(max_length=16, choices=[("platform", "Platform"), ("tenant_owned", "BYOP")])),
                ("capability", models.CharField(max_length=32)),
                ("outcome", models.CharField(default="completed", max_length=16)),
                ("unit_price_minor", models.PositiveBigIntegerField()),
                ("plan", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="meters", to="billing.billingplan")),
            ],
        ),
        migrations.AddConstraint(
            model_name="billingmeter",
            constraint=models.UniqueConstraint(fields=("plan", "provider_scope", "capability", "outcome"), name="billing_meter_unique"),
        ),
        migrations.CreateModel(
            name="BillingSubscription",
            fields=common() + [
                ("status", models.CharField(choices=[("active", "Active"), ("paused", "Paused"), ("cancelled", "Cancelled")], default="active", max_length=16)),
                ("started_at", models.DateTimeField()),
                ("plan", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="subscriptions", to="billing.billingplan")),
                ("tenant", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="billing_subscription", to="tenants.tenant")),
            ],
        ),
        migrations.CreateModel(
            name="BillingInvoice",
            fields=common() + [
                ("plan_code", models.CharField(max_length=80)),
                ("plan_version", models.PositiveIntegerField()),
                ("currency", models.CharField(max_length=3)),
                ("period_start", models.DateField()),
                ("period_end", models.DateField()),
                ("amount_minor", models.PositiveBigIntegerField(default=0)),
                ("status", models.CharField(choices=[("draft", "Draft"), ("issued", "Issued"), ("paid", "Paid"), ("void", "Void"), ("disputed", "Disputed")], default="draft", max_length=16)),
                ("issued_at", models.DateTimeField(blank=True, null=True)),
                ("due_at", models.DateTimeField(blank=True, null=True)),
                ("paid_at", models.DateTimeField(blank=True, null=True)),
                ("subscription", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="invoices", to="billing.billingsubscription")),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="invoices", to="tenants.tenant")),
            ],
            options={"ordering": ["-period_start"]},
        ),
        migrations.AddConstraint(
            model_name="billinginvoice",
            constraint=models.UniqueConstraint(fields=("tenant", "period_start"), name="billing_invoice_tenant_period"),
        ),
        migrations.CreateModel(
            name="BillingInvoiceLine",
            fields=common() + [
                ("description", models.CharField(max_length=200)),
                ("quantity", models.PositiveBigIntegerField()),
                ("unit_price_minor", models.PositiveBigIntegerField()),
                ("amount_minor", models.PositiveBigIntegerField()),
                ("invoice", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="lines", to="billing.billinginvoice")),
                ("usage_event", models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="invoice_line", to="billing.billingusageevent")),
            ],
        ),
        migrations.CreateModel(
            name="BillingPayment",
            fields=common() + [
                ("provider", models.CharField(default="paystack", max_length=32)),
                ("reference", models.CharField(max_length=64, unique=True)),
                ("amount_minor", models.PositiveBigIntegerField()),
                ("currency", models.CharField(max_length=3)),
                ("status", models.CharField(choices=[("pending", "Pending"), ("paid", "Paid"), ("failed", "Failed"), ("disputed", "Disputed")], default="pending", max_length=16)),
                ("checkout_url", models.URLField(blank=True, max_length=512)),
                ("gateway_transaction_id", models.CharField(blank=True, max_length=80)),
                ("confirmed_at", models.DateTimeField(blank=True, null=True)),
                ("invoice", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="payments", to="billing.billinginvoice")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="BillingPaymentEvent",
            fields=common() + [
                ("payload_sha256", models.CharField(max_length=64, unique=True)),
                ("event_type", models.CharField(max_length=80)),
                ("payment", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="events", to="billing.billingpayment")),
            ],
        ),
        migrations.CreateModel(
            name="BillingRefund",
            fields=common() + [
                ("gateway_refund_id", models.CharField(max_length=80, unique=True)),
                ("amount_minor", models.PositiveBigIntegerField()),
                ("status", models.CharField(choices=[("pending", "Pending"), ("completed", "Completed"), ("failed", "Failed")], default="pending", max_length=16)),
                ("confirmed_at", models.DateTimeField(blank=True, null=True)),
                ("payment", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="refunds", to="billing.billingpayment")),
            ],
        ),
    ]
