"""Claims retain their asserted values; trust and availability are evaluated live."""

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.evidence.models import GovernedRecord, RetainedQuerySet
from common.fields import EncryptedJSONField


class Claim(GovernedRecord):
    public_id_prefix = "clm"
    project = models.ForeignKey("projects.Project", on_delete=models.PROTECT)
    subject = models.ForeignKey(
        "verification_subjects.VerificationSubject",
        on_delete=models.PROTECT,
        related_name="governed_claims",
    )
    authorization = models.ForeignKey(
        "evidence.PurposeAuthorization", on_delete=models.PROTECT
    )
    schema = models.ForeignKey("evidence.ResourceSchema", on_delete=models.PROTECT)
    purpose = models.CharField(max_length=255)
    claim_class = models.CharField(
        max_length=24,
        choices=[
            ("candidate", "Candidate"),
            ("provider_asserted", "Provider asserted"),
            ("normalized", "Normalized"),
            ("corroborated", "Corroborated"),
            ("derived", "Derived"),
            ("reviewed", "Reviewed"),
        ],
    )
    value_json = EncryptedJSONField(encryption_purpose="claims.value")
    value_sha256 = models.CharField(max_length=64)
    confidence = models.DecimalField(
        max_digits=6,
        decimal_places=5,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
    )
    rule_name = models.SlugField(max_length=64, blank=True)
    rule_version = models.PositiveIntegerField(default=1)
    rule_parameters_json = EncryptedJSONField(
        default=dict, blank=True, encryption_purpose="claims.rule_parameters"
    )
    observed_at = models.DateTimeField()
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField(db_index=True)
    delete_after = models.DateTimeField(db_index=True)
    status = models.CharField(
        max_length=16,
        default="active",
        choices=[
            ("active", "Active"),
            ("revoked", "Revoked"),
            ("superseded", "Superseded"),
            ("deleted", "Deleted"),
        ],
    )
    supersedes = models.OneToOneField(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="superseded_by",
    )
    invalidated_at = models.DateTimeField(null=True, blank=True)
    invalidation_reason = models.CharField(max_length=120, blank=True)
    created_by_id_snapshot = models.CharField(max_length=64)
    source_evidence = models.ManyToManyField(
        "evidence.Evidence", through="ClaimEvidence", related_name="supported_claims"
    )
    source_claims = models.ManyToManyField(
        "self", through="ClaimSource", symmetrical=False, related_name="descendants"
    )

    class Meta:
        indexes = [
            models.Index(
                fields=[
                    "tenant",
                    "project",
                    "subject",
                    "purpose",
                    "schema",
                    "-created_at",
                    "-id",
                ]
            )
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(valid_until__gt=models.F("valid_from")),
                name="claims_valid_window",
            ),
            models.CheckConstraint(
                condition=models.Q(delete_after__gte=models.F("valid_until")),
                name="claims_retention_covers_validity",
            ),
        ]

    def clean(self):
        super().clean()
        if self.schema_id and (
            self.schema.tenant_id != self.tenant_id or self.schema.kind != "claim"
        ):
            raise ValidationError({"schema": "Choose a claim schema in this tenant."})
        if self.authorization_id:
            auth = self.authorization
            if (auth.project_id, auth.subject_id, auth.purpose) != (
                self.project_id,
                self.subject_id,
                self.purpose,
            ):
                raise ValidationError(
                    {"authorization": "The authorization must match the claim context."}
                )


class ClaimEvidence(models.Model):
    objects = RetainedQuerySet.as_manager()
    claim = models.ForeignKey(
        Claim, on_delete=models.PROTECT, related_name="evidence_edges"
    )
    evidence = models.ForeignKey(
        "evidence.Evidence", on_delete=models.PROTECT, related_name="claim_edges"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["claim", "evidence"], name="claims_unique_source_evidence"
            )
        ]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Claim provenance is immutable.")
        if (self.claim.tenant_id, self.claim.project_id, self.claim.subject_id) != (
            self.evidence.tenant_id,
            self.evidence.project_id,
            self.evidence.subject_id,
        ):
            raise ValidationError(
                "Claim provenance must match the subject and project."
            )
        self.full_clean()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Claim provenance is retained.")


class ClaimSource(models.Model):
    objects = RetainedQuerySet.as_manager()
    claim = models.ForeignKey(
        Claim, on_delete=models.PROTECT, related_name="source_edges"
    )
    source = models.ForeignKey(
        Claim, on_delete=models.PROTECT, related_name="derived_edges"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["claim", "source"], name="claims_unique_source_claim"
            ),
            models.CheckConstraint(
                condition=~models.Q(claim=models.F("source")),
                name="claims_no_self_source",
            ),
        ]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Claim provenance is immutable.")
        if (self.claim.tenant_id, self.claim.project_id, self.claim.subject_id) != (
            self.source.tenant_id,
            self.source.project_id,
            self.source.subject_id,
        ) or self.source.pk >= self.claim.pk:
            raise ValidationError(
                "Source claims must be earlier records in the same context."
            )
        self.full_clean()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Claim provenance is retained.")


class ClaimResolution(GovernedRecord):
    public_id_prefix = "clr"
    project = models.ForeignKey("projects.Project", on_delete=models.PROTECT)
    subject = models.ForeignKey(
        "verification_subjects.VerificationSubject", on_delete=models.PROTECT
    )
    schema = models.ForeignKey("evidence.ResourceSchema", on_delete=models.PROTECT)
    purpose = models.CharField(max_length=255)
    delete_after = models.DateTimeField(db_index=True)
    selected_claim = models.ForeignKey(
        Claim, on_delete=models.PROTECT, null=True, blank=True
    )
    member_ids_json = models.JSONField()
    outcome = models.CharField(
        max_length=24,
        choices=[
            ("selected", "Selected"),
            ("disputed", "Disputed"),
            ("more_evidence", "More evidence required"),
        ],
    )
    reason_json = EncryptedJSONField(encryption_purpose="claims.resolution_reason")
    decided_by_id_snapshot = models.CharField(max_length=64)

    def clean(self):
        super().clean()
        if self.selected_claim_id:
            c = self.selected_claim
            if (c.tenant_id, c.project_id, c.subject_id, c.purpose, c.schema_id) != (
                self.tenant_id,
                self.project_id,
                self.subject_id,
                self.purpose,
                self.schema_id,
            ):
                raise ValidationError(
                    {"selected_claim": "Conflict resolution context must match."}
                )


class ClaimDisclosure(GovernedRecord):
    public_id_prefix = "dcl"
    project = models.ForeignKey("projects.Project", on_delete=models.PROTECT)
    subject = models.ForeignKey(
        "verification_subjects.VerificationSubject", on_delete=models.PROTECT
    )
    authorization = models.ForeignKey(
        "evidence.PurposeAuthorization", on_delete=models.PROTECT
    )
    purpose = models.CharField(max_length=255)
    audience = models.ForeignKey("api_clients.APIClient", on_delete=models.PROTECT)
    selections_json = models.JSONField()
    token_sha256 = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField(db_index=True)
    created_by_id_snapshot = models.CharField(max_length=64)
    revoked_at = models.DateTimeField(null=True, blank=True)
    redemption_count = models.PositiveIntegerField(default=0)
    max_redemptions = models.PositiveSmallIntegerField(default=1)

    def clean(self):
        super().clean()
        if self.audience_id and (self.audience.tenant_id, self.audience.project_id) != (
            self.tenant_id,
            self.project_id,
        ):
            raise ValidationError(
                {
                    "audience": "The recipient must belong to the same authorized project."
                }
            )
        if self.authorization_id and (
            self.authorization.project_id,
            self.authorization.subject_id,
            self.authorization.purpose,
        ) != (self.project_id, self.subject_id, self.purpose):
            raise ValidationError(
                {"authorization": "Disclosure authorization must match."}
            )


class ClaimReusePolicy(GovernedRecord):
    public_id_prefix = "crp"
    project = models.ForeignKey("projects.Project", on_delete=models.PROTECT)
    schema = models.ForeignKey("evidence.ResourceSchema", on_delete=models.PROTECT)
    name = models.SlugField(max_length=120)
    version = models.PositiveIntegerField()
    purposes_json = models.JSONField()
    accepted_classes_json = models.JSONField()
    disclosure_fields_json = models.JSONField()
    max_age_seconds = models.PositiveIntegerField()
    minimum_confidence = models.DecimalField(
        max_digits=6,
        decimal_places=5,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
    )
    proposed_by_id_snapshot = models.CharField(max_length=64)
    approved_by_id_snapshot = models.CharField(max_length=64, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    retired_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "project", "name", "version"],
                name="claims_unique_reuse_policy_version",
            )
        ]

    def clean(self):
        super().clean()
        if self.schema_id and (
            self.schema.tenant_id != self.tenant_id or self.schema.kind != "claim"
        ):
            raise ValidationError({"schema": "Choose a claim schema in this tenant."})


class ClaimDisclosureRedemption(GovernedRecord):
    public_id_prefix = "cdr"
    disclosure = models.ForeignKey(
        ClaimDisclosure, on_delete=models.PROTECT, related_name="redemptions"
    )
    request_key_sha256 = models.CharField(max_length=64)
    audience_id_snapshot = models.CharField(max_length=64)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["disclosure", "request_key_sha256"],
                name="claims_disclosure_unique_redemption",
            )
        ]

    @property
    def project_id(self):
        return self.disclosure.project_id

    @property
    def project(self):
        return self.disclosure.project

    def clean(self):
        super().clean()
        if self.disclosure_id and self.disclosure.tenant_id != self.tenant_id:
            raise ValidationError({"disclosure": "Resource ownership must match."})
