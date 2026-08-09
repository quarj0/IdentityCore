import secrets

from django.contrib.auth.hashers import check_password, make_password
from django.db import models
from django.utils import timezone

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


VERIFICATION_SESSION_ACTIONS = (
    "session:read",
    "consent:accept",
    "document:capture",
    "selfie:capture",
    "liveness:challenge",
    "liveness:submit",
    "upload:create",
    "upload:transfer",
    "mobile_handoff:create",
)


class VerificationDecisionType(models.TextChoices):
    AUTOMATIC = "automatic", "Automatic"
    MANUAL = "manual", "Manual"
    SYSTEM = "system", "System"


class VerificationApprovalStatus(models.TextChoices):
    NOT_REQUIRED = "not_required", "Not Required"
    PENDING = "pending", "Pending"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"


class VerificationReviewOwner(models.TextChoices):
    TENANT = "tenant", "Tenant"
    PLATFORM = "platform", "Platform"


class ProcessingJobType(models.TextChoices):
    IDENTITY_DOCUMENT = "identity_document", "Identity Document"
    BIOMETRICS = "biometrics", "Biometrics"


class ProcessingJobStatus(models.TextChoices):
    QUEUED = "queued", "Queued"
    PROCESSING = "processing", "Processing"
    COMPLETED = "completed", "Completed"
    EXHAUSTED = "exhausted", "Exhausted"


class RetentionLegalHold(PublicIdModel, BaseModel):
    """Prevents retention cleanup while a documented hold is active."""

    public_id_prefix = "hold"

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.PROTECT,
        related_name="retention_legal_holds",
    )
    verification = models.ForeignKey(
        "verifications.Verification",
        on_delete=models.PROTECT,
        related_name="retention_legal_holds",
        null=True,
        blank=True,
    )
    reason = models.CharField(max_length=255)
    expires_at = models.DateTimeField(null=True, blank=True, db_index=True)
    released_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def is_active(self) -> bool:
        return self.released_at is None and (
            self.expires_at is None or self.expires_at > timezone.now()
        )


class Verification(PublicIdModel, BaseModel):
    public_id_prefix = "ver"

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.PROTECT,
        related_name="verifications",
    )
    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.PROTECT,
        related_name="verifications",
        null=True,
        blank=True,
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
    workflow_snapshot_json = EncryptedJSONField(
        default=dict,
        blank=True,
        encryption_purpose="verifications.workflow_snapshot",
    )
    status = models.CharField(
        max_length=32,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING_CONSENT,
        db_index=True,
    )
    purpose = models.CharField(max_length=255)
    review_owner = models.CharField(
        max_length=16,
        choices=VerificationReviewOwner.choices,
        default=VerificationReviewOwner.TENANT,
        db_index=True,
    )
    assigned_reviewer = models.ForeignKey(
        "accounts.PlatformUser",
        on_delete=models.PROTECT,
        related_name="assigned_verification_reviews",
        null=True,
        blank=True,
    )
    assigned_at = models.DateTimeField(null=True, blank=True)
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
        indexes = [
            models.Index(
                fields=["tenant", "-created_at", "-id"],
                name="verif_tenant_created_pk_idx",
            ),
        ]

    def __str__(self) -> str:
        return self.public_id


class ProcessingJob(PublicIdModel, BaseModel):
    """Durable lease for recoverable verification processing work."""

    public_id_prefix = "job"

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.PROTECT,
        related_name="processing_jobs",
    )
    verification = models.ForeignKey(
        Verification,
        on_delete=models.PROTECT,
        related_name="processing_jobs",
    )
    job_type = models.CharField(
        max_length=32,
        choices=ProcessingJobType.choices,
        db_index=True,
    )
    resource_public_id = models.CharField(max_length=64)
    status = models.CharField(
        max_length=16,
        choices=ProcessingJobStatus.choices,
        default=ProcessingJobStatus.QUEUED,
        db_index=True,
    )
    attempt_count = models.PositiveSmallIntegerField(default=0)
    max_attempts = models.PositiveSmallIntegerField(default=3)
    heartbeat_at = models.DateTimeField(null=True, blank=True)
    lease_expires_at = models.DateTimeField(db_index=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_code = models.CharField(max_length=120, blank=True)

    class Meta:
        ordering = ["created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["job_type", "resource_public_id"],
                name="processing_job_resource_uniq",
            )
        ]
        indexes = [
            models.Index(
                fields=["status", "lease_expires_at"],
                name="processing_job_due_idx",
            )
        ]


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
    allowed_actions_json = models.JSONField(default=list, blank=True)
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
    def allowed_actions(self) -> list[str]:
        return list(self.allowed_actions_json or VERIFICATION_SESSION_ACTIONS)

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
    contract_version = models.CharField(max_length=16, default="1")
    reason_codes_json = models.JSONField(default=list, blank=True)
    input_snapshot_json = EncryptedJSONField(
        default=dict,
        blank=True,
        encryption_purpose="verifications.decision.input_snapshot",
    )
    approval_status = models.CharField(
        max_length=16,
        choices=VerificationApprovalStatus.choices,
        default=VerificationApprovalStatus.NOT_REQUIRED,
        db_index=True,
    )
    approved_by = models.ForeignKey(
        "accounts.PlatformUser",
        on_delete=models.PROTECT,
        related_name="approved_verification_decisions",
        null=True,
        blank=True,
    )
    approved_at = models.DateTimeField(null=True, blank=True)
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
