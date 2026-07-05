from django.db import models

from apps.core.models import BaseModel, PublicIdModel


class RiskLevel(models.TextChoices):
    LOW = "low", "Low"
    MEDIUM = "medium", "Medium"
    HIGH = "high", "High"
    CRITICAL = "critical", "Critical"


class RiskRecommendation(models.TextChoices):
    APPROVE = "approve", "Approve"
    REJECT = "reject", "Reject"
    MANUAL_REVIEW = "manual_review", "Manual Review"


class RiskAssessment(PublicIdModel, BaseModel):
    public_id_prefix = "rsk"

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.PROTECT,
        related_name="risk_assessments",
    )
    verification = models.OneToOneField(
        "verifications.Verification",
        on_delete=models.PROTECT,
        related_name="risk_assessment",
    )
    risk_score = models.DecimalField(max_digits=5, decimal_places=2)
    risk_level = models.CharField(
        max_length=16,
        choices=RiskLevel.choices,
        db_index=True,
    )
    signals_json = models.JSONField(default=dict, blank=True)
    recommendation = models.CharField(
        max_length=32,
        choices=RiskRecommendation.choices,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.public_id
