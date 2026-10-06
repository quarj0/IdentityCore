from apps.providers.models import ProviderCheck


DECISION_CONTRACT_VERSION = "1"


def system_decision_contract_fields(verification, reason_code: str) -> dict:
    """Replace the contract alongside a system decision, including on updates."""
    from apps.verification_subjects.models import VerificationSubject

    subject_active = VerificationSubject.objects.filter(
        pk=verification.verification_subject_id, deleted_at__isnull=True
    ).exists()
    return {
        "contract_version": DECISION_CONTRACT_VERSION,
        "reason_codes_json": [reason_code],
        "input_snapshot_json": build_decision_input_snapshot(verification)
        if subject_active and not verification.deleted_at
        else {},
    }


def build_decision_input_snapshot(verification, *, risk_assessment=None) -> dict:
    provider_checks = ProviderCheck.objects.filter(verification=verification).order_by(
        "created_at"
    )
    return {
        "contract_version": DECISION_CONTRACT_VERSION,
        "policy_snapshot": verification.policy_snapshot_json or {},
        "workflow_snapshot": verification.workflow_snapshot_json or {},
        "risk_signals": (risk_assessment.signals_json if risk_assessment else {}),
        "provider_checks": [
            {
                "check_type": check.check_type,
                "status": check.status,
                "normalized_result": check.normalized_result_json or {},
            }
            for check in provider_checks
        ],
    }
