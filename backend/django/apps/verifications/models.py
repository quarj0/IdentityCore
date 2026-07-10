import secrets

from django.contrib.auth.hashers import check_password, make_password
from django.db import models

from apps.core.models import BaseModel, PublicIdModel
from common.fields import EncryptedJSONField


class VerificationStatus(models.TextChoices):
    CREATED = "created", "Created"
    PENDING_CONSENT = "pending_consent", "Pending Consent"
    IN_PROGRESS = "in_progress", "In Progress"
    AWAITING_DOCUMENT = "awaiting_document", "Awaiting Document"
    AWAITING_SELFIE = "awaiting_selfie", "Awaiting Selfie"
    PROCESSING = "processing", "Processing"
    MANUAL_REVIEW_REQUIRED = "manual_review_required", "Manual Review Required"
    VERIFIED = "verified", "Verified"
    REJECTED = "rejected", "Rejected"
    EXPIRED = "expired", "Expired"
    CANCELLED = "cancelled", "Cancelled"
    FAILED = "failed", "Failed"


class VerificationSessionStatus(models.TextChoices):
    CREATED = "created", "Created"
    ACTIVE = "active", "Active"
    COMPLETED = "completed", "Completed"
    EXPIRED = "expired", "Expired"
    REVOKED = "revoked", "Revoked"


class VerificationDecisionType(models.TextChoices):
    AUTOMATIC = "automatic", "Automatic"
    MANUAL = "manual", "Manual"
    SYSTEM = "system", "System"


class Verification(PublicIdModel, BaseModel):
    public_id_prefix = "ver"

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.PROTECT,
        related_name="verifications",
    )
    organization = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.PROTECT,
        related_name="verifications",
    )
    verification_subject = models.ForeignKey(
        "verification_subjects.VerificationSubject",
        on_delete=models.PROTECT,
        related_name="verifications",
    )
    policy_public_id = models.CharField(max_length=64, blank=True)
    policy_snapshot_json = EncryptedJSONField(
        default=dict,
        blank=True,
        encryption_purpose="verifications.policy_snapshot",
    )
    status = models.CharField(
        max_length=32,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING_CONSENT,
        db_index=True,
    )
    purpose = models.CharField(max_length=255)
    external_reference = models.CharField(max_length=255, blank=True, db_index=True)
    metadata_json = EncryptedJSONField(
        default=dict,
        blank=True,
        encryption_purpose="verifications.metadata",
    )
    redirect_url = models.URLField(blank=True)
    expires_at = models.DateTimeField(db_index=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        "accounts.PlatformUser",
        on_delete=models.PROTECT,
        related_name="created_verifications",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.public_id


class VerificationSession(PublicIdModel):
    public_id_prefix = "ses"

    verification = models.ForeignKey(
        Verification,
        on_delete=models.CASCADE,
        related_name="sessions",
    )
    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.PROTECT,
        related_name="verification_sessions",
    )
    session_token_hash = models.CharField(max_length=255, unique=True)
    status = models.CharField(
        max_length=32,
        choices=VerificationSessionStatus.choices,
        default=VerificationSessionStatus.CREATED,
        db_index=True,
    )
    started_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(db_index=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_seen_at = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    device_fingerprint = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    @classmethod
    def generate_session_token(cls) -> str:
        return secrets.token_urlsafe(32)

    def set_session_token(self, raw_token: str) -> None:
        self.session_token_hash = make_password(raw_token)

    @property
    def is_authenticated(self) -> bool:
        return True

    def __str__(self) -> str:
        return self.public_id


class VerificationMobileHandoff(PublicIdModel):
    public_id_prefix = "hnd"

    source_session = models.ForeignKey(
        VerificationSession, on_delete=models.CASCADE, related_name="mobile_handoffs"
    )
    redeemed_session = models.OneToOneField(
        VerificationSession,
        on_delete=models.SET_NULL,
        related_name="redeemed_mobile_handoff",
        null=True,
        blank=True,
    )
    token_hash = models.CharField(max_length=255)
    expires_at = models.DateTimeField(db_index=True)
    redeemed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def generate_token(cls) -> str:
        return secrets.token_urlsafe(32)

    def set_token(self, raw_token: str) -> None:
        self.token_hash = make_password(raw_token)

    def matches_token(self, raw_token: str) -> bool:
        return check_password(raw_token, self.token_hash)


class VerificationDecision(PublicIdModel, BaseModel):
    public_id_prefix = "dec"

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.PROTECT,
        related_name="verification_decisions",
    )
    verification = models.OneToOneField(
        Verification,
        on_delete=models.PROTECT,
        related_name="decision_record",
    )
    decision = models.CharField(
        max_length=32,
        choices=VerificationStatus.choices,
        db_index=True,
    )
    decision_type = models.CharField(
        max_length=32,
        choices=VerificationDecisionType.choices,
    )
    reason_code = models.CharField(max_length=120, blank=True)
    reason_detail = models.TextField(blank=True)
    evidence_summary_json = EncryptedJSONField(
        default=dict,
        blank=True,
        encryption_purpose="verifications.decision.evidence_summary",
    )
    decided_by = models.ForeignKey(
        "accounts.PlatformUser",
        on_delete=models.PROTECT,
        related_name="verification_decisions",
        null=True,
        blank=True,
    )
    decided_at = models.DateTimeField(db_index=True)

    class Meta:
        ordering = ["-decided_at"]

    def __str__(self) -> str:
        return self.public_id
