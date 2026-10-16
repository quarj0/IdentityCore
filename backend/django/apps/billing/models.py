from django.db import models

from apps.core.models import BaseModel, PublicIdModel


class BillingStatus(models.TextChoices):
    PAID = "paid", "Paid"
    DUE_SOON = "due_soon", "Due soon"
    OVERDUE = "overdue", "Overdue"
    SUSPENDED = "suspended", "Suspended"


class BillingRecord(PublicIdModel, BaseModel):
    public_id_prefix = "bill"

    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.PROTECT,
        related_name="billing_records",
    )
    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.PROTECT,
        related_name="billing_records",
    )
    title = models.CharField(max_length=255)
    subtitle = models.TextField(blank=True)
    status = models.CharField(
        max_length=32, choices=BillingStatus.choices, db_index=True
    )
    monthly_recurring_revenue = models.CharField(max_length=64)
    monthly_check_count = models.PositiveIntegerField(default=0)
    current_invoice = models.CharField(max_length=64, blank=True)
    plan = models.CharField(max_length=64, blank=True)
    billing_cycle = models.CharField(max_length=32, default="monthly")
    owner_team = models.CharField(max_length=120, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-updated_at"]


class BillingUsageEvent(PublicIdModel, BaseModel):
    """Unrated usage fact, NOT an invoice or authority to charge a customer.

    Exactly one fact per finished provider check. Keeping rating separate avoids
    treating BYOP calls as the same product as managed AI processing.
    """

    public_id_prefix = "bue"
    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.PROTECT, related_name="billing_usage_events"
    )
    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.PROTECT,
        related_name="billing_usage_events",
    )
    provider_check = models.OneToOneField(
        "providers.ProviderCheck",
        on_delete=models.PROTECT,
        related_name="billing_usage_event",
    )
    environment = models.CharField(
        max_length=16,
        choices=[("sandbox", "Sandbox"), ("production", "Production")],
    )
    capability = models.CharField(max_length=32)
    provider_scope = models.CharField(
        max_length=16,
        choices=[("tenant_owned", "Tenant owned"), ("platform", "Platform owned")],
    )
    outcome = models.CharField(max_length=16)
    quantity = models.PositiveSmallIntegerField(default=1)
    rating_state = models.CharField(max_length=16, default="unrated")
    occurred_at = models.DateTimeField()

    class Meta:
        ordering = ["-occurred_at"]
        indexes = [
            models.Index(
                fields=["tenant", "environment", "occurred_at"],
                name="bill_usage_ten_env_time",
            )
        ]


class BillingPlan(PublicIdModel, BaseModel):
    """Versioned commercial plan: never change a published plan's price in place."""

    public_id_prefix = "bpl"
    code = models.SlugField(max_length=80)
    version = models.PositiveIntegerField(default=1)
    name = models.CharField(max_length=120)
    currency = models.CharField(max_length=3, default="GHS")
    monthly_price_minor = models.PositiveBigIntegerField(default=0)
    published = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["code", "version"], name="billing_plan_code_version"
            )
        ]

    def save(self, *args, **kwargs):
        if self.pk:
            previous = type(self).objects.get(pk=self.pk)
            if previous.published and any(
                getattr(previous, field) != getattr(self, field)
                for field in (
                    "code",
                    "version",
                    "name",
                    "currency",
                    "monthly_price_minor",
                    "published",
                )
            ):
                from django.core.exceptions import ValidationError

                raise ValidationError(
                    "Published plan terms are immutable; create a new version."
                )
        return super().save(*args, **kwargs)


class BillingMeter(PublicIdModel, BaseModel):
    """Explicit unit price for one provider scope, capability and outcome."""

    public_id_prefix = "bmt"
    plan = models.ForeignKey(
        BillingPlan, on_delete=models.PROTECT, related_name="meters"
    )
    provider_scope = models.CharField(
        max_length=16, choices=[("platform", "Platform"), ("tenant_owned", "BYOP")]
    )
    capability = models.CharField(max_length=32)
    outcome = models.CharField(max_length=16, default="completed")
    unit_price_minor = models.PositiveBigIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["plan", "provider_scope", "capability", "outcome"],
                name="billing_meter_unique",
            )
        ]

    def save(self, *args, **kwargs):
        from django.core.exceptions import ValidationError

        if self.plan.published:
            previous = (
                type(self).objects.filter(pk=self.pk).first() if self.pk else None
            )
            if previous is None or any(
                getattr(previous, name) != getattr(self, name)
                for name in (
                    "plan_id",
                    "provider_scope",
                    "capability",
                    "outcome",
                    "unit_price_minor",
                )
            ):
                raise ValidationError(
                    "Published rates are immutable; create a new plan version."
                )
        return super().save(*args, **kwargs)


class BillingSubscription(PublicIdModel, BaseModel):
    public_id_prefix = "bsu"
    tenant = models.OneToOneField(
        "tenants.Tenant", on_delete=models.PROTECT, related_name="billing_subscription"
    )
    plan = models.ForeignKey(
        BillingPlan, on_delete=models.PROTECT, related_name="subscriptions"
    )
    status = models.CharField(
        max_length=16,
        default="active",
        choices=[
            ("active", "Active"),
            ("paused", "Paused"),
            ("cancelled", "Cancelled"),
        ],
    )
    started_at = models.DateTimeField()


class BillingInvoice(PublicIdModel, BaseModel):
    public_id_prefix = "bin"
    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.PROTECT, related_name="invoices"
    )
    subscription = models.ForeignKey(
        BillingSubscription, on_delete=models.PROTECT, related_name="invoices"
    )
    plan_code = models.CharField(max_length=80)
    plan_version = models.PositiveIntegerField()
    currency = models.CharField(max_length=3)
    period_start = models.DateField()
    period_end = models.DateField()
    amount_minor = models.PositiveBigIntegerField(default=0)
    status = models.CharField(
        max_length=20,
        default="draft",
        choices=[
            ("draft", "Draft"),
            ("issued", "Issued"),
            ("paid", "Paid"),
            ("void", "Void"),
            ("disputed", "Disputed"),
            ("partially_refunded", "Partially refunded"),
            ("refunded", "Refunded"),
        ],
    )
    issued_at = models.DateTimeField(null=True, blank=True)
    due_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "period_start"], name="billing_invoice_tenant_period"
            )
        ]
        ordering = ["-period_start"]


class BillingInvoiceLine(PublicIdModel, BaseModel):
    public_id_prefix = "bil"
    invoice = models.ForeignKey(
        BillingInvoice, on_delete=models.PROTECT, related_name="lines"
    )
    usage_event = models.OneToOneField(
        BillingUsageEvent,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="invoice_line",
    )
    description = models.CharField(max_length=200)
    quantity = models.PositiveBigIntegerField()
    unit_price_minor = models.PositiveBigIntegerField()
    amount_minor = models.PositiveBigIntegerField()


class BillingPayment(PublicIdModel, BaseModel):
    public_id_prefix = "bpa"
    invoice = models.ForeignKey(
        BillingInvoice, on_delete=models.PROTECT, related_name="payments"
    )
    provider = models.CharField(max_length=32, default="paystack")
    reference = models.CharField(max_length=64, unique=True)
    amount_minor = models.PositiveBigIntegerField()
    currency = models.CharField(max_length=3)
    status = models.CharField(
        max_length=20,
        default="pending",
        choices=[
            ("pending", "Pending"),
            ("paid", "Paid"),
            ("failed", "Failed"),
            ("disputed", "Disputed"),
            ("partially_refunded", "Partially refunded"),
            ("refunded", "Refunded"),
        ],
    )
    checkout_url = models.URLField(blank=True, max_length=2048)
    gateway_checkout_id = models.CharField(max_length=120, blank=True)
    gateway_transaction_id = models.CharField(max_length=80, blank=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "gateway_transaction_id"],
                condition=~models.Q(gateway_transaction_id=""),
                name="billing_gateway_transaction_unique",
            ),
            models.UniqueConstraint(
                fields=["invoice"],
                condition=models.Q(status="pending"),
                name="billing_pending_invoice_unique",
            ),
        ]


class BillingPaymentEvent(PublicIdModel, BaseModel):
    """Only digest, event name and reference; no PII-rich gateway payloads."""

    public_id_prefix = "bpe"
    payment = models.ForeignKey(
        BillingPayment, on_delete=models.PROTECT, related_name="events"
    )
    payload_sha256 = models.CharField(max_length=64, unique=True)
    event_type = models.CharField(max_length=80)
    gateway_event_id = models.CharField(max_length=120, blank=True)
    provider = models.CharField(max_length=32, default="paystack")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "gateway_event_id"],
                condition=~models.Q(gateway_event_id=""),
                name="billing_gateway_event_unique",
            ),
        ]


class BillingRefund(PublicIdModel, BaseModel):
    """Reconciled refund record. Initiation requires separate operator authorization."""

    public_id_prefix = "brf"
    payment = models.ForeignKey(
        BillingPayment, on_delete=models.PROTECT, related_name="refunds"
    )
    gateway_refund_id = models.CharField(max_length=120, unique=True)
    amount_minor = models.PositiveBigIntegerField()
    status = models.CharField(
        max_length=16,
        choices=[
            ("pending", "Pending"),
            ("completed", "Completed"),
            ("failed", "Failed"),
        ],
        default="pending",
    )
    confirmed_at = models.DateTimeField(null=True, blank=True)


class BillingDispute(PublicIdModel, BaseModel):
    public_id_prefix = "bdi"
    payment = models.ForeignKey(
        BillingPayment, on_delete=models.PROTECT, related_name="disputes"
    )
    gateway_dispute_id = models.CharField(max_length=120, unique=True)
    amount_minor = models.PositiveBigIntegerField()
    status = models.CharField(
        max_length=16, choices=[("open", "Open"), ("won", "Won"), ("lost", "Lost")]
    )
    gateway_status = models.CharField(max_length=40)
