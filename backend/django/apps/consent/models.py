from django.db import models
from django.core.exceptions import ValidationError
from common.fields import EncryptedJSONField

from apps.core.models import BaseModel, PublicIdModel


class ConsentTemplateStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    ACTIVE = "active", "Active"
    ARCHIVED = "archived", "Archived"


class ConsentTemplate(PublicIdModel, BaseModel):
    public_id_prefix = "ctm"

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.PROTECT,
        related_name="consent_templates",
    )
    name = models.CharField(max_length=255)
    version = models.PositiveIntegerField(default=1)
    language = models.CharField(max_length=16, default="en")
    content = models.TextField()
    evidence_scope_json = models.JSONField(null=True, blank=True, default=None)
    status = models.CharField(
        max_length=32,
        choices=ConsentTemplateStatus.choices,
        default=ConsentTemplateStatus.DRAFT,
        db_index=True,
    )
    created_by = models.ForeignKey(
        "accounts.PlatformUser",
        on_delete=models.PROTECT,
        related_name="created_consent_templates",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["name", "-version", "language"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "name", "version", "language"],
                name="consent_template_tenant_name_version_language_uniq",
            )
        ]

    def __str__(self) -> str:
        return f"{self.name} v{self.version}"


class ConsentRecord(PublicIdModel, BaseModel):
    public_id_prefix = "con"

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.PROTECT,
        related_name="consent_records",
    )
    verification = models.ForeignKey(
        "verifications.Verification",
        on_delete=models.PROTECT,
        related_name="consent_records",
    )
    verification_subject = models.ForeignKey(
        "verification_subjects.VerificationSubject",
        on_delete=models.PROTECT,
        related_name="consent_records",
    )
    consent_template = models.ForeignKey(
        ConsentTemplate,
        on_delete=models.PROTECT,
        related_name="consent_records",
        null=True,
        blank=True,
    )
    consent_text_snapshot = models.TextField()
    consent_locale = models.CharField(max_length=16, default="en")
    consent_content_hash = models.CharField(max_length=64, blank=True)
    accepted = models.BooleanField(default=True)
    accepted_at = models.DateTimeField(db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    device_fingerprint = models.CharField(max_length=255, blank=True)
    withdrawn_at = models.DateTimeField(null=True, blank=True)
    proof_json = EncryptedJSONField(
        null=True, blank=True, encryption_purpose="consent.proof"
    )

    class Meta:
        ordering = ["-accepted_at"]

    def save(self, *args, **kwargs):
        from apps.consent.services import build_proof

        if not self.pk:
            self.ensure_public_id()
            self.proof_json = build_proof(
                self, notice_version=getattr(self, "_notice_version", None)
            )
            self.consent_content_hash = self.proof_json["content_hash"]
        else:
            previous = type(self).objects.get(pk=self.pk)
            fields = (
                "public_id",
                "tenant_id",
                "verification_id",
                "verification_subject_id",
                "consent_template_id",
                "consent_text_snapshot",
                "consent_locale",
                "consent_content_hash",
                "accepted",
                "accepted_at",
                "ip_address",
                "user_agent",
                "device_fingerprint",
                "proof_json",
                "deleted_at",
            )
            updated = kwargs.get("update_fields")
            for field in fields:
                if updated is not None and field not in updated:
                    continue
                if getattr(previous, field) != getattr(self, field):
                    if (
                        field in {"proof_json", "consent_content_hash"}
                        and previous.proof_json is None
                        and (
                            field != "consent_content_hash"
                            or previous.consent_content_hash == ""
                        )
                        and getattr(self, "_legacy_binding_authorized", False)
                    ):
                        continue
                    raise ValidationError("Consent proof is immutable.")
            if previous.withdrawn_at != self.withdrawn_at and (
                previous.withdrawn_at is not None
                or self.withdrawn_at is None
                or not getattr(self, "_withdrawal_authorized", False)
            ):
                raise ValidationError(
                    "Consent withdrawal requires an audited transition."
                )
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.public_id
