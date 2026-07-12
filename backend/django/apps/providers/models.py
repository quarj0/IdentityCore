from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import BaseModel, PublicIdModel
from common.fields import EncryptedJSONField


class ProviderType(models.TextChoices):
    DOCUMENT = "document", "Document"
    BIOMETRIC = "biometric", "Biometric"
    IDENTITY_DATABASE = "identity_database", "Identity Database"
    LIVENESS = "liveness", "Liveness"
    RISK = "risk", "Risk"
    NOTIFICATION = "notification", "Notification"


class ProviderStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    DISABLED = "disabled", "Disabled"
    TESTING = "testing", "Testing"
    DEPRECATED = "deprecated", "Deprecated"


class ProviderCheckType(models.TextChoices):
    DOCUMENT_OCR = "document_ocr", "Document OCR"
    DOCUMENT_CLASSIFICATION = "document_classification", "Document Classification"
    DOCUMENT_QUALITY = "document_quality", "Document Quality"
    FACE_MATCH = "face_match", "Face Match"
    LIVENESS = "liveness", "Liveness"
    IDENTITY_LOOKUP = "identity_lookup", "Identity Lookup"
    RISK_CHECK = "risk_check", "Risk Check"


class ProviderCheckStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PROCESSING = "processing", "Processing"
    COMPLETED = "completed", "Completed"
    FAILED = "failed", "Failed"
    TIMEOUT = "timeout", "Timeout"
    CANCELLED = "cancelled", "Cancelled"


CHECK_TYPE_PROVIDER_TYPES = {
    ProviderCheckType.DOCUMENT_OCR: {ProviderType.DOCUMENT},
    ProviderCheckType.DOCUMENT_CLASSIFICATION: {ProviderType.DOCUMENT},
    ProviderCheckType.DOCUMENT_QUALITY: {ProviderType.DOCUMENT},
    ProviderCheckType.FACE_MATCH: {ProviderType.BIOMETRIC},
    ProviderCheckType.LIVENESS: {ProviderType.LIVENESS, ProviderType.BIOMETRIC},
    ProviderCheckType.IDENTITY_LOOKUP: {ProviderType.IDENTITY_DATABASE},
    ProviderCheckType.RISK_CHECK: {ProviderType.RISK},
}

TERMINAL_PROVIDER_CHECK_STATUSES = {
    ProviderCheckStatus.COMPLETED,
    ProviderCheckStatus.FAILED,
    ProviderCheckStatus.TIMEOUT,
    ProviderCheckStatus.CANCELLED,
}


class Provider(PublicIdModel, BaseModel):
    public_id_prefix = "prv"

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.PROTECT,
        related_name="providers",
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=120, unique=True)
    provider_type = models.CharField(
        max_length=32,
        choices=ProviderType.choices,
        db_index=True,
    )
    status = models.CharField(
        max_length=32,
        choices=ProviderStatus.choices,
        default=ProviderStatus.ACTIVE,
        db_index=True,
    )
    configuration_json = EncryptedJSONField(
        default=dict,
        blank=True,
        encryption_purpose="providers.configuration",
    )

    class Meta:
        ordering = ["provider_type", "name"]

    def __str__(self) -> str:
        return self.name


class ProviderAssignmentStatus(models.TextChoices):
    ACTIVE = "active", "Active"
    DISABLED = "disabled", "Disabled"


class ProviderAssignmentKey(models.TextChoices):
    DOCUMENT_OCR = ProviderCheckType.DOCUMENT_OCR, "Document OCR"
    DOCUMENT_CLASSIFICATION = ProviderCheckType.DOCUMENT_CLASSIFICATION, "Document Classification"
    DOCUMENT_QUALITY = ProviderCheckType.DOCUMENT_QUALITY, "Document Quality"
    FACE_MATCH = ProviderCheckType.FACE_MATCH, "Face Match"
    LIVENESS = ProviderCheckType.LIVENESS, "Liveness"
    IDENTITY_LOOKUP = ProviderCheckType.IDENTITY_LOOKUP, "Identity Lookup"
    RISK_CHECK = ProviderCheckType.RISK_CHECK, "Risk Check"
    NOTIFICATION_EMAIL = "notification_email", "Notification Email"
    NOTIFICATION_SMS = "notification_sms", "Notification SMS"
    NOTIFICATION_IN_APP = "notification_in_app", "Notification In-App"


class ProviderAssignment(PublicIdModel, BaseModel):
    public_id_prefix = "pva"

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.PROTECT,
        related_name="provider_assignments",
    )
    assignment_key = models.CharField(
        max_length=64,
        choices=ProviderAssignmentKey.choices,
        db_index=True,
    )
    provider = models.ForeignKey(
        Provider,
        on_delete=models.PROTECT,
        related_name="assignments",
    )
    status = models.CharField(
        max_length=32,
        choices=ProviderAssignmentStatus.choices,
        default=ProviderAssignmentStatus.ACTIVE,
        db_index=True,
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["tenant_id", "assignment_key", "created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "assignment_key"],
                name="provider_assignment_tenant_key_uniq",
            )
        ]

    def clean(self):
        super().clean()
        if self.provider.tenant_id not in {None, self.tenant_id}:
            raise ValidationError(
                {
                    "provider": "Assigned providers must belong to the tenant or be platform defaults."
                }
            )

        allowed_types = {
            ProviderAssignmentKey.DOCUMENT_OCR: {ProviderType.DOCUMENT},
            ProviderAssignmentKey.DOCUMENT_CLASSIFICATION: {ProviderType.DOCUMENT},
            ProviderAssignmentKey.DOCUMENT_QUALITY: {ProviderType.DOCUMENT},
            ProviderAssignmentKey.FACE_MATCH: {ProviderType.BIOMETRIC},
            ProviderAssignmentKey.LIVENESS: {
                ProviderType.LIVENESS,
                ProviderType.BIOMETRIC,
            },
            ProviderAssignmentKey.IDENTITY_LOOKUP: {ProviderType.IDENTITY_DATABASE},
            ProviderAssignmentKey.RISK_CHECK: {ProviderType.RISK},
            ProviderAssignmentKey.NOTIFICATION_EMAIL: {ProviderType.NOTIFICATION},
            ProviderAssignmentKey.NOTIFICATION_SMS: {ProviderType.NOTIFICATION},
            ProviderAssignmentKey.NOTIFICATION_IN_APP: {ProviderType.NOTIFICATION},
        }.get(self.assignment_key, set())
        if allowed_types and self.provider.provider_type not in allowed_types:
            raise ValidationError(
                {
                    "provider": f"{self.assignment_key} requires provider types: {', '.join(sorted(allowed_types))}."
                }
            )
        if self.status == ProviderAssignmentStatus.ACTIVE and self.provider.status != ProviderStatus.ACTIVE:
            raise ValidationError(
                {
                    "provider": "Active assignments require an active provider."
                }
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.tenant_id}:{self.assignment_key}"


class ProviderCheck(PublicIdModel, BaseModel):
    public_id_prefix = "pck"

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.PROTECT,
        related_name="provider_checks",
    )
    verification = models.ForeignKey(
        "verifications.Verification",
        on_delete=models.PROTECT,
        related_name="provider_checks",
    )
    provider = models.ForeignKey(
        Provider,
        on_delete=models.PROTECT,
        related_name="provider_checks",
    )
    check_type = models.CharField(
        max_length=32,
        choices=ProviderCheckType.choices,
        db_index=True,
    )
    status = models.CharField(
        max_length=32,
        choices=ProviderCheckStatus.choices,
        default=ProviderCheckStatus.PENDING,
        db_index=True,
    )
    provider_reference = models.CharField(max_length=255, blank=True, db_index=True)
    request_metadata_json = EncryptedJSONField(
        default=dict,
        blank=True,
        encryption_purpose="providers.check.request_metadata",
    )
    response_metadata_json = EncryptedJSONField(
        default=dict,
        blank=True,
        encryption_purpose="providers.check.response_metadata",
    )
    normalized_result_json = EncryptedJSONField(
        default=dict,
        blank=True,
        encryption_purpose="providers.check.normalized_result",
    )
    error_code = models.CharField(max_length=120, blank=True)
    error_message = models.TextField(blank=True)
    started_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-started_at"]

    def clean(self):
        super().clean()
        allowed_provider_types = CHECK_TYPE_PROVIDER_TYPES.get(self.check_type, set())
        if (
            allowed_provider_types
            and self.provider.provider_type not in allowed_provider_types
        ):
            raise ValidationError(
                {
                    "provider": f"{self.check_type} checks require provider types: {', '.join(sorted(allowed_provider_types))}."
                }
            )
        if self.verification_id and self.tenant_id != self.verification.tenant_id:
            raise ValidationError(
                {
                    "tenant": "Provider checks must belong to the same tenant as the verification."
                }
            )
        if self.status in TERMINAL_PROVIDER_CHECK_STATUSES and self.completed_at is None:
            raise ValidationError(
                {
                    "completed_at": "Terminal provider checks must include a completion timestamp."
                }
            )
        if (
            self.status not in TERMINAL_PROVIDER_CHECK_STATUSES
            and self.completed_at is not None
        ):
            raise ValidationError(
                {
                    "completed_at": "Only terminal provider checks may include a completion timestamp."
                }
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.public_id
