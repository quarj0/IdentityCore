"""Fixed artificial outcomes for pristine, explicitly sandbox-owned cases."""

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.audit.services import lock_audit_chain, record_audit_event
from apps.projects.models import Project
from apps.providers.models import ProviderCheck, ProviderCheckType
from apps.providers.services import get_or_create_system_provider
from apps.tenants.models import Tenant
from apps.verification_subjects.models import VerificationSubject
from apps.verifications.decision_contract import (
    build_decision_input_snapshot,
    DECISION_CONTRACT_VERSION,
)
from apps.verifications.models import (
    Verification,
    VerificationDecision,
    VerificationSessionStatus,
    SandboxSimulation,
)
from apps.verifications.result_contract import serialize_verification_result
from apps.verifications.transitions import transition_verification
from apps.webhooks.services import queue_webhook_events

SCENARIOS = {
    "approved": ("verified", "risk_rules_approved", "completed", "passed", ""),
    "declined": ("rejected", "risk_rules_rejected", "completed", "rejected", ""),
    "review": (
        "manual_review_required",
        "risk_rules_review",
        "completed",
        "inconclusive",
        "",
    ),
    "timeout": ("failed", "provider_timeout", "timeout", "timeout", "provider_timeout"),
    "provider_error": (
        "failed",
        "provider_unavailable",
        "failed",
        "failed",
        "provider_unavailable",
    ),
}


@transaction.atomic
def simulate_verification(verification, scenario, *, actor, request=None):
    if scenario not in SCENARIOS:
        raise ValidationError({"scenario": "Choose a supported sandbox scenario."})
    lock_audit_chain(verification.tenant_id)
    tenant = (
        Tenant.objects.select_for_update()
        .select_related("organization")
        .get(pk=verification.tenant_id)
    )
    if (
        tenant.status != "active"
        or tenant.deleted_at is not None
        or tenant.organization.deleted_at is not None
        or tenant.organization.status in {"suspended", "closed"}
    ):
        raise PermissionDenied("The workspace is not active.")
    project = (
        Project.objects.select_for_update()
        .filter(
            pk=verification.project_id,
            tenant=tenant,
            environment="sandbox",
            status="active",
            deleted_at__isnull=True,
        )
        .first()
    )
    if project is None:
        raise PermissionDenied("Simulation requires an active sandbox project.")
    subject = VerificationSubject.objects.select_for_update().get(
        pk=verification.verification_subject_id
    )
    case = Verification.objects.select_for_update().get(pk=verification.pk)
    if (
        case.project_id != project.pk
        or case.tenant_id != tenant.pk
        or case.organization_id != tenant.organization_id
        or subject.tenant_id != tenant.pk
        or case.verification_subject_id != subject.pk
        or case.deleted_at is not None
        or subject.deleted_at is not None
        or case.review_owner != "tenant"
    ):
        raise PermissionDenied("This case is not eligible for sandbox simulation.")
    previous = SandboxSimulation.objects.filter(verification=case).first()
    if previous:
        if previous.scenario != scenario:
            raise ValidationError(
                {"scenario": "This case already has a different simulation."}
            )
        return serialize_verification_result(case)
    if (
        case.status != "pending_consent"
        or case.expires_at <= timezone.now()
        or case.consent_records.exists()
        or case.uploads.exists()
        or case.identity_documents.exists()
        or case.provider_checks.exists()
        or case.processing_jobs.exists()
        or VerificationDecision.objects.filter(verification=case).exists()
    ):
        raise ValidationError({"scenario": "Only a pristine case can be simulated."})
    SandboxSimulation.objects.create(verification=case, scenario=scenario)
    # Simulation reads no consent/evidence and invokes no provider. These are
    # the normal state edges, explicitly marked artificial by the separate row.
    transition_verification(case, "in_progress")
    transition_verification(case, "processing")
    now = timezone.now()
    outcome, reason, check_state, normalized_state, error = SCENARIOS[scenario]
    provider = get_or_create_system_provider("sandbox_simulation")
    ProviderCheck.objects.create(
        tenant=tenant,
        verification=case,
        provider=provider,
        check_type=ProviderCheckType.RISK_CHECK,
        status=check_state,
        error_code=error,
        started_at=now,
        completed_at=now,
        duration_ms=0,
        normalized_result_json={
            "contract_version": "1",
            "status": normalized_state,
            "model_name": "sandbox-simulator",
            "model_version": "1",
            "synthetic": True,
        },
        response_metadata_json={
            "synthetic": True,
            "scenario": scenario,
            "model_name": "sandbox-simulator",
            "model_version": "1",
        },
    )
    VerificationDecision.objects.create(
        tenant=tenant,
        verification=case,
        decision=outcome,
        decision_type="system",
        reason_code=reason,
        reason_codes_json=[reason],
        contract_version=DECISION_CONTRACT_VERSION,
        input_snapshot_json=build_decision_input_snapshot(case),
        evidence_summary_json={
            "synthetic": True,
            "scenario": scenario,
            "simulator_version": "1",
        },
        decided_at=now,
    )
    case.decision_revision += 1
    case.save(update_fields=["decision_revision", "updated_at"])
    transition_verification(case, outcome, completed_at=now)
    case.sessions.filter(status__in=["created", "active"]).update(
        status=VerificationSessionStatus.REVOKED
    )
    record_audit_event(
        tenant=tenant,
        actor=actor,
        request=request,
        action="verification.sandbox_simulated",
        target_type="verification",
        target_id=case.public_id,
        metadata={"scenario": scenario, "simulator_version": "1"},
    )
    queue_webhook_events(
        tenant=tenant,
        event_type=f"verification.{outcome}",
        payload={
            "verification_id": case.public_id,
            "external_reference": case.external_reference,
            "status": outcome,
            "simulation": {"scenario": scenario, "version": 1},
        },
    )
    return serialize_verification_result(case)
