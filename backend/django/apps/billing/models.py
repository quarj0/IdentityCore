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

