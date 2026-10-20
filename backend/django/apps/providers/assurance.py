"""Scoped conformance receipts and independent provider-assurance decisions.

An uploaded report is an assertion backed by referenced artifacts. Approval records
an accountable officer's review; it never manufactures third-party certification.
"""

import re
from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from apps.audit.services import lock_audit_chain
from apps.evidence.access import current_actor, identity, protected_value
from apps.evidence.services import _audit, _transition
from apps.evidence.validation import canonical_json, digest
from apps.providers.configuration import configuration_digest
from apps.providers.models import (
    ProviderCertification,
    ProviderEnvironmentConfiguration,
)
from apps.tenants.models import Tenant

SUITE_VERSION = "provider-assurance/v1"
SYNC_CASES = {
    "success",
    "malformed",
    "timeout",
    "replay",
    "version_negotiation",
    "capability_binding",
    "environment_binding",
    "deletion",
    "redaction",
}
ASYNC_CASES = {
    "pending",
    "callback_authentication",
    "polling",
    "duplicate_completion",
    "conflicting_completion",
    "late_completion",
    "cancellation",
    "lease_binding",
}


def _config(tenant_id, actor, public_id, permission):
    lock_audit_chain(tenant_id)
    tenant = Tenant.objects.get(pk=tenant_id)
    principal = current_actor(actor, tenant, permission)
    config = (
        ProviderEnvironmentConfiguration.objects.select_related(
            "provider__tenant", "provider__tenant__organization"
        )
        .filter(provider__tenant=tenant, public_id=public_id)
        .first()
    )
    if config is None:
        raise NotFound()
    return principal, config


def _current_configuration(config):
    if (
        config.deleted_at
        or config.status != "active"
        or config.provider.deleted_at
        or config.provider.status != "active"
        or config.manifest_snapshot_json != config.provider.manifest_json
    ):
        raise PermissionDenied("The provider configuration is unavailable.")


def report_scope(config, capability):
    _current_configuration(config)
    if capability not in config.manifest_snapshot_json.get("capabilities", {}):
        raise ValidationError("The configuration does not declare this capability.")
    return {
        "configuration_id": config.public_id,
        "environment": config.environment,
        "capability": capability,
        "contract_version": "1",
        "operation_contract": config.public_configuration_json.get(
            "operation_contract", "sync"
        ),
        "configuration_digest": configuration_digest(config),
        "manifest_sha256": digest(config.manifest_snapshot_json),
        "suite_version": SUITE_VERSION,
    }


def _validate_report(config, capability, report, level):
    canonical_json(report, maximum=64 * 1024)
    if not isinstance(report, dict):
        raise ValidationError("An exact scoped assurance report is required.")
    scope = report_scope(config, capability)
    if set(report) != set(scope) | {"cases", "artifact_sha256", "assurance_references"}:
        raise ValidationError("The assurance report fields are unsupported.")
    if any(report[key] != value for key, value in scope.items()):
        raise ValidationError(
            "The report does not match the current configuration scope."
        )
    required = SYNC_CASES | (
        ASYNC_CASES if scope["operation_contract"] != "sync" else set()
    )
    cases = report["cases"]
    if (
        not isinstance(cases, dict)
        or set(cases) != required
        or any(value != "passed" for value in cases.values())
    ):
        raise ValidationError("Every required conformance case must pass.")
    if (
        not isinstance(report["artifact_sha256"], str)
        or re.fullmatch(r"[0-9a-f]{64}", report["artifact_sha256"]) is None
    ):
        raise ValidationError("Reference the SHA-256 of the retained test artifacts.")
    references = report["assurance_references"]
    if (
        not isinstance(references, list)
        or len(references) > 16
        or any(
            not isinstance(value, str) or not 1 <= len(value) <= 1024
            for value in references
        )
    ):
        raise ValidationError("Choose bounded independent-assurance references.")
    if level not in {"conformance", "assured"} or (
        level == "assured" and not references
    ):
        raise ValidationError("Independent assurance requires supporting references.")
    return scope


@transaction.atomic
def propose_certification(
    *,
    tenant_id,
    actor,
    configuration_id,
    capability,
    report,
    assurance_level,
    valid_until,
    delete_after,
    request=None,
):
    actor, config = _config(tenant_id, actor, configuration_id, "providers:assurance")
    scope = _validate_report(config, capability, report, assurance_level)
    now = timezone.now()
    if (
        timezone.is_naive(valid_until)
        or timezone.is_naive(delete_after)
        or not now < valid_until <= now + timedelta(days=366)
        or delete_after < valid_until
    ):
        raise ValidationError(
            "Choose an expiry within one year and covering retention."
        )
    record = ProviderCertification.objects.create(
        tenant_id=tenant_id,
        configuration=config,
        capability=capability,
        environment=config.environment,
        contract_version="1",
        operation_contract=scope["operation_contract"],
        suite_version=SUITE_VERSION,
        configuration_digest=scope["configuration_digest"],
        manifest_sha256=scope["manifest_sha256"],
        report_sha256=digest(report),
        report_json=report,
        assurance_level=assurance_level,
        proposed_by_id_snapshot=identity(actor),
        valid_until=valid_until,
        delete_after=delete_after,
    )
    _audit(
        record,
        actor,
        "provider.certification_proposed",
        request,
        capability=capability,
        assurance_level=assurance_level,
    )
    return record


def _record(tenant_id, actor, certification_id, permission):
    lock_audit_chain(tenant_id)
    tenant = Tenant.objects.get(pk=tenant_id)
    actor = current_actor(actor, tenant, permission)
    record = (
        ProviderCertification.objects.select_related(
            "tenant",
            "configuration__provider__tenant",
            "configuration__provider__tenant__organization",
        )
        .filter(tenant=tenant, public_id=certification_id)
        .first()
    )
    if record is None:
        raise NotFound()
    return actor, record


@transaction.atomic
def approve_certification(*, tenant_id, actor, certification_id, request=None):
    actor, record = _record(
        tenant_id, actor, certification_id, "providers:assurance:approve"
    )
    current_actor(actor, record.tenant, "providers:assurance")
    if identity(actor) == record.proposed_by_id_snapshot:
        raise PermissionDenied("A different assurance officer must review this report.")
    if record.deleted_at or record.revoked_at or record.valid_until <= timezone.now():
        raise PermissionDenied("The certification is unavailable.")
    report = protected_value(record, "report_json")
    _validate_report(
        record.configuration, record.capability, report, record.assurance_level
    )
    if digest(report) != record.report_sha256:
        raise PermissionDenied("The assurance report failed its integrity check.")
    if not record.approved_at:
        _transition(
            record, approved_at=timezone.now(), approved_by_id_snapshot=identity(actor)
        )
        _audit(record, actor, "provider.certification_approved", request)
    return record


@transaction.atomic
def revoke_certification(*, tenant_id, actor, certification_id, reason, request=None):
    actor, record = _record(tenant_id, actor, certification_id, "providers:assurance")
    if (
        not isinstance(reason, str)
        or re.fullmatch(r"[a-z][a-z0-9_]{0,119}", reason) is None
    ):
        raise ValidationError("Choose a bounded revocation reason code.")
    if record.revoked_at is None:
        _transition(record, revoked_at=timezone.now(), revocation_reason=reason)
        _audit(record, actor, "provider.certification_revoked", request, reason=reason)
    return record


def require_certification(config, capability, *, minimum_level="conformance"):
    """Readiness always binds current config/manifest, approval and expiry."""
    scope = report_scope(config, capability)
    records = ProviderCertification.objects.filter(
        tenant_id=config.provider.tenant_id,
        configuration=config,
        capability=capability,
        approved_at__isnull=False,
        revoked_at__isnull=True,
        deleted_at__isnull=True,
        valid_until__gt=timezone.now(),
        delete_after__gt=timezone.now(),
        configuration_digest=scope["configuration_digest"],
        manifest_sha256=scope["manifest_sha256"],
        suite_version=SUITE_VERSION,
        contract_version="1",
        operation_contract=scope["operation_contract"],
    )
    if minimum_level not in {"conformance", "assured"}:
        raise ValueError("Unsupported assurance level")
    if minimum_level == "assured":
        records = records.filter(assurance_level="assured")
    record = records.order_by("-approved_at", "-pk").first()
    if record is None:
        raise PermissionDenied("Current scoped provider assurance is required.")
    return record


def summary(record):
    return {
        "id": record.public_id,
        "configuration_id": record.configuration.public_id,
        "environment": record.environment,
        "capability": record.capability,
        "contract_version": record.contract_version,
        "operation_contract": record.operation_contract,
        "suite_version": record.suite_version,
        "report_sha256": record.report_sha256,
        "assurance_level": record.assurance_level,
        "approved_at": record.approved_at.isoformat() if record.approved_at else None,
        "valid_until": record.valid_until.isoformat(),
        "delete_after": record.delete_after.isoformat(),
        "proposed_by_id": record.proposed_by_id_snapshot,
        "approved_by_id": record.approved_by_id_snapshot or None,
        "revoked": record.revoked_at is not None,
    }
