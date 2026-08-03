from apps.providers.models import ProviderCheck


DECISION_CONTRACT_VERSION = "1"


def build_decision_input_snapshot(verification, *, risk_assessment=None) -> dict:
    provider_checks = ProviderCheck.objects.filter(
        verification=verification
    ).order_by("created_at")
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
