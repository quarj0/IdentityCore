"""External risk v1 produces bounded evidence and can only escalate local policy."""

import re
from decimal import Decimal, InvalidOperation

from django.db import DatabaseError

from apps.providers.adapters import ProviderContractError
from apps.providers.models import ProviderCheckType
from apps.providers.services import (
    execute_provider_route,
    invoke_selected_provider_operation,
)

SIGNALS = {"document_risk", "velocity_risk", "network_risk", "inconsistent_evidence"}
RESULT_KEYS = {
    "contract_version",
    "capability",
    "status",
    "risk_version",
    "provider_version",
    "risk_score",
    "signals",
}


def normalize_external_risk(result):
    def invalid():
        raise ProviderContractError(
            "External risk response does not match evidence contract v1."
        )

    if (
        not isinstance(result, dict)
        or set(result) != RESULT_KEYS
        or result["contract_version"] != "1"
        or result["risk_version"] != "1"
        or result["capability"] != "risk_check"
        or result["status"] not in {"completed", "inconclusive"}
    ):
        invalid()
    if not isinstance(result["provider_version"], str) or not re.fullmatch(
        r"[A-Za-z0-9_.-]{1,64}", result["provider_version"]
    ):
        invalid()
    signals = result["signals"]
    if (
        not isinstance(signals, list)
        or len(signals) > len(SIGNALS)
        or any(
            not isinstance(signal, str) or signal not in SIGNALS for signal in signals
        )
        or len(set(signals)) != len(signals)
    ):
        invalid()
    score = result["risk_score"]
    if result["status"] == "inconclusive":
        if score is not None:
            invalid()
    else:
        if type(score) not in {int, float}:
            invalid()
        score = Decimal(str(score))
        if not score.is_finite() or not 0 <= score <= 100:
            invalid()
        score = float(score)
    return {**result, "risk_score": score, "signals": sorted(signals)}


def collect_external_risk(verification, local_signals):
    policy = verification.policy_snapshot_json or {}
    if policy.get("external_risk_enabled") is not True:
        return None
    # Explicit allowlist: no IDs, names, contact fields, OCR, media or raw device data.
    inputs = {
        "input_version": "1",
        "document_submitted": bool(local_signals["document_submitted"]),
        "document_requires_manual_review": bool(
            local_signals["document_requires_manual_review"]
        ),
        "selfie_submitted": bool(local_signals["selfie_submitted"]),
        "liveness_status": local_signals["liveness_status"],
        "face_match_status": local_signals["face_match_status"],
    }

    def unavailable(**kwargs):
        raise ProviderContractError("A configured external risk provider is required.")

    try:
        execution = execute_provider_route(
            verification=verification,
            check_type=ProviderCheckType.RISK_CHECK,
            operation=lambda provider, timeout: normalize_external_risk(
                invoke_selected_provider_operation(
                    provider=provider,
                    check_type=ProviderCheckType.RISK_CHECK,
                    environment=(
                        verification.project.environment
                        if verification.project_id
                        else "sandbox"
                    ),
                    timeout_seconds=timeout,
                    operation_kwargs=inputs,
                    built_in_operation=unavailable,
                )
            ),
            request_metadata={"risk_input_version": "1"},
            finalize_exhaustion=False,
        )
        return {
            **execution.result,
            "provider_check_id": execution.provider_check.public_id,
        }
    except DatabaseError:
        raise
    except Exception:
        # Provider/runtime errors have already been persisted by the orchestration boundary.
        return {
            "risk_version": "1",
            "status": "unavailable",
            "risk_score": None,
            "signals": [],
        }


def apply_external_risk(policy, evidence, *, score, level, recommendation):
    from apps.risk.models import RiskLevel, RiskRecommendation

    if evidence is None:
        return score, level, recommendation
    try:
        threshold = Decimal(str(policy.get("external_risk_review_threshold", 70)))
        if not threshold.is_finite() or not 0 <= threshold <= 100:
            raise ValueError()
        failure_action = policy.get("external_risk_failure_action", "manual_review")
        if failure_action not in {"manual_review", "ignore"}:
            raise ValueError()
    except (ValueError, InvalidOperation):
        threshold, failure_action = Decimal("0"), "manual_review"
    review = evidence["status"] != "completed" and failure_action == "manual_review"
    if evidence["status"] == "completed":
        external_score = Decimal(str(evidence["risk_score"]))
        score = max(score, external_score)
        review = external_score >= threshold or bool(evidence["signals"])
        if score >= 90:
            level = RiskLevel.CRITICAL
        elif score >= 70:
            level = RiskLevel.HIGH
        elif score >= 40:
            level = RiskLevel.MEDIUM
    if review and recommendation != RiskRecommendation.REJECT:
        recommendation = RiskRecommendation.MANUAL_REVIEW
    return score, level, recommendation
