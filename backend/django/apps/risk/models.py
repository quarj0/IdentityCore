from django.db import models

from apps.core.models import BaseModel, PublicIdModel
from common.fields import EncryptedJSONField


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
    signals_json = EncryptedJSONField(
        default=dict,
        blank=True,
        encryption_purpose="risk.signals",
    )
    recommendation = models.CharField(
        max_length=32,
        choices=RiskRecommendation.choices,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.public_id


class ReuseFingerprint(models.Model):
    """Expiring keyed correlation indexes; never raw subject or biometric values."""

    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE)
    verification = models.ForeignKey(
        "verifications.Verification",
        on_delete=models.CASCADE,
        related_name="reuse_fingerprints",
    )
    environment = models.CharField(max_length=16)
    kind = models.CharField(max_length=16)
    tenant_digest = models.CharField(max_length=64)
    global_digest = models.CharField(max_length=64, blank=True)
    observed_at = models.DateTimeField()
    expires_at = models.DateTimeField(db_index=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["verification", "kind"],
                name="reuse_case_kind_once",
            )
        ]
        indexes = [
            models.Index(
                fields=["tenant", "environment", "kind", "tenant_digest"],
                name="reuse_tenant_match",
            ),
            models.Index(
                fields=["environment", "kind", "global_digest"],
                name="reuse_global_match",
            ),
        ]
