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
        "projects.Project", on_delete=models.PROTECT, related_name="billing_usage_events"
    )
    provider_check = models.OneToOneField(
        "providers.ProviderCheck", on_delete=models.PROTECT,
        related_name="billing_usage_event"
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
