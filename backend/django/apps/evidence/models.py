"""Immutable governed resources; lifecycle changes go through audited services."""

from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import BaseModel, PublicIdModel
from common.fields import EncryptedJSONField


class RetainedQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise ValidationError("Use the audited resource lifecycle service.")

    def delete(self):
        raise ValidationError("Governed records retain their audit identity.")

    def bulk_create(self, *args, **kwargs):
        raise ValidationError("Create governed records through their owning service.")

    def bulk_update(self, *args, **kwargs):
        raise ValidationError("Use the audited resource lifecycle service.")


class GovernedRecord(PublicIdModel, BaseModel):
    objects = RetainedQuerySet.as_manager()

    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.PROTECT)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError(
                "Governed content is immutable; use lifecycle services."
            )
        self.ensure_public_id()
        self.full_clean()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Governed records retain their audit identity.")

    def clean(self):
        super().clean()
        if self.tenant_id:
            for field in ("project", "subject", "authorization", "verification"):
                if getattr(self, field + "_id", None) is not None:
                    related = getattr(self, field)
                    if related.tenant_id != self.tenant_id:
                        raise ValidationError({field: "Resource ownership must match."})


class ResourceSchema(GovernedRecord):
    public_id_prefix = "sch"
    name = models.SlugField(max_length=120)
    version = models.PositiveIntegerField()
    kind = models.CharField(
        max_length=16, choices=[("evidence", "Evidence"), ("claim", "Claim")]
    )
    definition_json = models.JSONField()
    disclosure_fields_json = models.JSONField(default=list, blank=True)
    created_by_id_snapshot = models.CharField(max_length=64)
    retired_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "kind", "name", "version"],
                name="evidence_schema_unique_version",
            )
        ]


class PurposeAuthorization(GovernedRecord):
    public_id_prefix = "paz"
    project = models.ForeignKey("projects.Project", on_delete=models.PROTECT)
    subject = models.ForeignKey(
        "verification_subjects.VerificationSubject", on_delete=models.PROTECT
    )
    purpose = models.CharField(max_length=255)
    legal_basis = models.CharField(
        max_length=32,
        choices=[
            ("consent", "Consent"),
            ("contract", "Contract"),
            ("legal_obligation", "Legal obligation"),
            ("legitimate_interest", "Legitimate interest"),
        ],
    )
    justification_json = EncryptedJSONField(encryption_purpose="evidence.authorization")
    consent_record = models.ForeignKey(
        "consent.ConsentRecord", on_delete=models.PROTECT, null=True, blank=True
    )
    allowed_operations_json = models.JSONField()
    proposed_by_id_snapshot = models.CharField(max_length=64)
    approved_by_id_snapshot = models.CharField(max_length=64, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField(db_index=True)
    delete_after = models.DateTimeField(db_index=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    revocation_reason = models.CharField(max_length=120, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(valid_until__gt=models.F("valid_from")),
                name="evidence_authorization_valid_window",
            )
        ]
        indexes = [models.Index(fields=["tenant", "project", "subject", "purpose"])]


class Evidence(GovernedRecord):
    public_id_prefix = "evd"
    source_check = models.ForeignKey(
        "providers.ProviderCheck",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="governed_evidence",
    )
    project = models.ForeignKey("projects.Project", on_delete=models.PROTECT)
    subject = models.ForeignKey(
        "verification_subjects.VerificationSubject",
        on_delete=models.PROTECT,
        related_name="governed_evidence",
    )
    authorization = models.ForeignKey(PurposeAuthorization, on_delete=models.PROTECT)
    schema = models.ForeignKey(ResourceSchema, on_delete=models.PROTECT)
    verification = models.ForeignKey(
        "verifications.Verification", on_delete=models.PROTECT, null=True, blank=True
    )
    operation_reference = models.CharField(max_length=120)
    purpose = models.CharField(max_length=255)
    evidence_type = models.CharField(
        max_length=32,
        choices=[
            ("submitted", "Submitted"),
            ("provider", "Provider"),
            ("system", "System"),
            ("human", "Human"),
            ("authoritative", "Authoritative"),
        ],
    )
    payload_json = EncryptedJSONField(encryption_purpose="evidence.payload")
    provenance_json = EncryptedJSONField(encryption_purpose="evidence.provenance")
    payload_sha256 = models.CharField(max_length=64)
    provenance_sha256 = models.CharField(max_length=64)
    observed_at = models.DateTimeField()
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
    sources = models.ManyToManyField(
        "self", through="EvidenceSource", symmetrical=False, related_name="descendants"
    )

    class Meta:
        indexes = [
            models.Index(
                fields=["tenant", "project", "subject", "purpose", "-created_at", "-id"]
            )
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(delete_after__gte=models.F("valid_until")),
                name="evidence_retention_covers_validity",
            )
        ]

    def clean(self):
        super().clean()
        if self.schema_id and (
            self.schema.tenant_id != self.tenant_id or self.schema.kind != "evidence"
        ):
            raise ValidationError(
                {"schema": "Choose an evidence schema in this tenant."}
            )
        if self.authorization_id:
            auth = self.authorization
            if (auth.project_id, auth.subject_id, auth.purpose) != (
                self.project_id,
                self.subject_id,
                self.purpose,
            ):
                raise ValidationError(
                    {
                        "authorization": "Purpose authorization must match the resource context."
                    }
                )
        if self.verification_id and (
            self.verification.project_id,
            self.verification.verification_subject_id,
        ) != (self.project_id, self.subject_id):
            raise ValidationError({"verification": "Verification context must match."})


class EvidenceSource(models.Model):
    objects = RetainedQuerySet.as_manager()
    evidence = models.ForeignKey(
        Evidence, on_delete=models.PROTECT, related_name="source_edges"
    )
    source = models.ForeignKey(
        Evidence, on_delete=models.PROTECT, related_name="derived_edges"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["evidence", "source"], name="evidence_unique_source"
            ),
            models.CheckConstraint(
                condition=~models.Q(evidence=models.F("source")),
                name="evidence_no_self_source",
            ),
        ]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Evidence lineage is immutable.")
        child, parent = self.evidence, self.source
        if (child.tenant_id, child.project_id, child.subject_id, child.purpose) != (
            parent.tenant_id,
            parent.project_id,
            parent.subject_id,
            parent.purpose,
        ):
            raise ValidationError("Evidence lineage must share its authorized context.")
        # Edges always point to an earlier immutable record, making cycles impossible.
        if child.pk is None or parent.pk is None or parent.pk >= child.pk:
            raise ValidationError("Evidence sources must precede their descendants.")
        self.full_clean()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Evidence lineage is retained.")


class ResourceLegalHold(GovernedRecord):
    """Preserve the complete subject/project lineage, not just a copied leaf."""

    public_id_prefix = "rhd"
    project = models.ForeignKey("projects.Project", on_delete=models.PROTECT)
    subject = models.ForeignKey(
        "verification_subjects.VerificationSubject", on_delete=models.PROTECT
    )
    reason_json = EncryptedJSONField(encryption_purpose="evidence.hold_reason")
    created_by_id_snapshot = models.CharField(max_length=64)
    expires_at = models.DateTimeField(null=True, blank=True)
    released_at = models.DateTimeField(null=True, blank=True)
    released_by_id_snapshot = models.CharField(max_length=64, blank=True)

    class Meta:
        indexes = [models.Index(fields=["tenant", "project", "subject", "released_at"])]


class AuthorizationReuse(models.Model):
    """An independently approved grant explicitly admits a named source purpose."""

    objects = RetainedQuerySet.as_manager()
    authorization = models.ForeignKey(
        PurposeAuthorization, on_delete=models.PROTECT, related_name="reuse_sources"
    )
    source_authorization = models.ForeignKey(
        PurposeAuthorization, on_delete=models.PROTECT, related_name="reuse_descendants"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["authorization", "source_authorization"],
                name="evidence_unique_authorized_reuse",
            ),
            models.CheckConstraint(
                condition=~models.Q(authorization=models.F("source_authorization")),
                name="evidence_no_self_reuse",
            ),
        ]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Purpose reuse is immutable.")
        target, source = self.authorization, self.source_authorization
        if (target.tenant_id, target.project_id, target.subject_id) != (
            source.tenant_id,
            source.project_id,
            source.subject_id,
        ) or source.pk >= target.pk:
            raise ValidationError(
                "Reuse must name an earlier authorization for the same subject and project."
            )
        self.full_clean()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Purpose reuse history is retained.")


class ResourceMaintenanceState(models.Model):
    """Durable scheduler fairness, including tenants with held or failed cleanup."""

    tenant = models.OneToOneField(
        "tenants.Tenant", on_delete=models.PROTECT, related_name="resource_maintenance"
    )
    last_examined_at = models.DateTimeField(null=True, blank=True, db_index=True)
    last_error_code = models.CharField(max_length=120, blank=True)


class SubjectResourceRestriction(GovernedRecord):
    """A destruction hold never silently reauthorizes reuse after erasure is requested."""

    public_id_prefix = "srr"
    subject = models.OneToOneField(
        "verification_subjects.VerificationSubject",
        on_delete=models.PROTECT,
        related_name="resource_restriction",
    )
    processing_revoked_at = models.DateTimeField()
    reason_code = models.CharField(max_length=120)
    requested_by_id_snapshot = models.CharField(max_length=64, blank=True)
