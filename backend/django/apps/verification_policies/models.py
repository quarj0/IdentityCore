from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from apps.core.models import BaseModel, PublicIdModel


class VerificationPolicyStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    ACTIVE = "active", "Active"
    ARCHIVED = "archived", "Archived"


class VerificationPolicy(PublicIdModel, BaseModel):
    public_id_prefix = "pol"

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.PROTECT,
        related_name="verification_policies",
    )
    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.PROTECT,
        related_name="verification_policies",
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    version = models.PositiveIntegerField(default=1)
    consent_template = models.ForeignKey(
        "consent.ConsentTemplate",
        on_delete=models.PROTECT,
        related_name="verification_policies",
        null=True,
        blank=True,
    )
    default_locale = models.CharField(max_length=16, default="en")
    supported_locales_json = models.JSONField(default=list, blank=True)
    status = models.CharField(
        max_length=32,
        choices=VerificationPolicyStatus.choices,
        default=VerificationPolicyStatus.DRAFT,
        db_index=True,
    )
    required_document_types_json = models.JSONField(default=list, blank=True)
    required_liveness_level = models.CharField(max_length=32, default="passive")
    face_match_threshold = models.DecimalField(
        max_digits=5, decimal_places=4, default=0.8500
    )
    manual_review_threshold = models.DecimalField(
        max_digits=5, decimal_places=4, default=0.6500
    )
    document_authenticity_required = models.BooleanField(
        default=False, db_default=False
    )
    document_authenticity_min_confidence = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        default=0.9,
        db_default=0.9,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
    )
    external_risk_enabled = models.BooleanField(default=False, db_default=False)
    external_risk_failure_action = models.CharField(
        max_length=24,
        choices=[("manual_review", "Manual review"), ("ignore", "Ignore")],
        default="manual_review",
        db_default="manual_review",
    )
    external_risk_review_threshold = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=70,
        db_default=70,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    maker_checker_required = models.BooleanField(default=False)
    verification_expiry_minutes = models.PositiveIntegerField(default=1440)
    media_retention_days = models.PositiveIntegerField(default=30)
    metadata_retention_days = models.PositiveIntegerField(default=365)
    created_by = models.ForeignKey(
        "accounts.PlatformUser",
        on_delete=models.PROTECT,
        related_name="created_verification_policies",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["name", "-version"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "name", "version"],
                name="verification_policy_tenant_name_version_uniq",
            )
        ]

    def clean(self):
        super().clean()
        from apps.verifications.review_reasons import validate_reason_rules

        validate_reason_rules(
            {}
            if self.review_reason_rules_json is None
            else self.review_reason_rules_json
        )
        if self.created_by_id and self.created_by.tenant_id != self.tenant_id:
            raise ValidationError(
                {
                    "created_by": "Verification policies must be created by a user in the same tenant."
                }
            )

    def save(self, *args, **kwargs):
        from apps.verifications.review_reasons import validate_reason_rules

        validate_reason_rules(
            {}
            if self.review_reason_rules_json is None
            else self.review_reason_rules_json
        )
        return super().save(*args, **kwargs)

    @property
    def required_document_types(self) -> list[str]:
        return list(self.required_document_types_json)

    review_reason_rules_json = models.JSONField(default=dict, blank=True, null=True)
    reuse_rules_json = models.JSONField(default=dict, blank=True)
    document_consistency_rules_json = models.JSONField(default=dict, blank=True)

    def snapshot(self) -> dict:
        from apps.consent.services import validate_policy_consent_scope
        validate_policy_consent_scope(self.consent_template, self.supported_locales_json or [self.default_locale])
        consent = None
        if self.consent_template_id:
            base_template = self.consent_template
            translations = {
                base_template.language: {
                    "template_id": base_template.public_id,
                    "version": base_template.version,
                    "language": base_template.language,
                    "content": base_template.content,
                    "evidence_scope": base_template.evidence_scope_json,
                }
            }
            configured_locales = self.supported_locales_json or [self.default_locale]
            translated_templates = base_template.__class__.objects.filter(
                tenant_id=self.tenant_id,
                name=base_template.name,
                version=base_template.version,
                language__in=configured_locales,
                status="active",
            )
            for template in translated_templates:
                translations[template.language] = {
                    "template_id": template.public_id,
                    "version": template.version,
                    "language": template.language,
                    "content": template.content,
                    "evidence_scope": template.evidence_scope_json,
                }
            consent = {
                "template_id": base_template.public_id,
                "name": base_template.name,
                "version": base_template.version,
                "language": base_template.language,
                "content": base_template.content,
                "translations": translations,
            }
        return {
            "id": self.public_id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "default_locale": self.default_locale,
            "supported_locales": self.supported_locales_json or [self.default_locale],
            "consent": consent,
            "status": self.status,
            "required_document_types": self.required_document_types,
            "required_liveness_level": self.required_liveness_level,
            "face_match_threshold": float(self.face_match_threshold),
            "manual_review_threshold": float(self.manual_review_threshold),
            "maker_checker_required": self.maker_checker_required,
            "document_consistency_rules": self.document_consistency_rules_json,
            "reuse_rules": self.reuse_rules_json,
            "review_reason_rules": self.review_reason_rules_json or {},
            "document_authenticity_required": self.document_authenticity_required,
            "document_authenticity_min_confidence": float(
                self.document_authenticity_min_confidence
            ),
            "external_risk_enabled": self.external_risk_enabled,
            "external_risk_failure_action": self.external_risk_failure_action,
            "external_risk_review_threshold": float(
                self.external_risk_review_threshold
            ),
            "verification_expiry_minutes": self.verification_expiry_minutes,
            "media_retention_days": self.media_retention_days,
            "metadata_retention_days": self.metadata_retention_days,
        }

    def __str__(self) -> str:
        return f"{self.name} v{self.version}"
