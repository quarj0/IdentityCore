import re
from typing import Any

from apps.verifications.models import Verification


VERIFICATION_RESULT_SCHEMA_VERSION = "1"

SAFE_EVIDENCE_FIELDS = (
    "confidence_score",
    "score",
    "match_score",
    "quality_score",
    "threshold_used",
)
SAFE_PROVENANCE_TOKEN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/+-]{0,119}$")
SAFE_CHECK_STATUSES = frozenset(
    {
        "cancelled",
        "completed",
        "failed",
        "inconclusive",
        "matched",
        "not_matched",
        "passed",
        "pending",
        "processing",
        "rejected",
        "timeout",
        "validated",
    }
)
SAFE_ISSUE_CODES = frozenset(
    {
        "blur_detected",
        "document_blurry",
        "document_classification_unavailable",
        "document_media_missing",
        "document_ocr_unavailable",
        "document_type_mismatch",
        "document_type_not_determined",
        "glare_detected",
        "low_contrast",
        "mrz_checksum_invalid",
        "mrz_country_mismatch",
    }
)
SAFE_DECISION_REASON_CODES = frozenset(
    {
        "biometric_provider_unavailable",
        "evidence_confirmed",
        "local_failed",
        "local_manual_review_required",
        "local_rejected",
        "local_verified",
        "manual_review_rejected",
        "manual_review_verified",
        "processing_retries_exhausted",
        "provider_route_exhausted",
        "risk_rules_approved",
        "risk_rules_rejected",
        "risk_rules_review",
    }
)
SAFE_PROVIDER_ERROR_CODES = frozenset(
    {
        "provider_circuit_open",
        "provider_contract_version_unsupported",
        "provider_invalid_content_type",
        "provider_invalid_json",
        "provider_invalid_response",
        "provider_network_error",
        "provider_redirect_blocked",
        "provider_response_too_large",
        "provider_route_exhausted",
        "provider_timeout",
    }
)


def _safe_number(value: Any) -> int | float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return value
    return None


def _safe_token(value: Any) -> str | None:
    if isinstance(value, str) and SAFE_PROVENANCE_TOKEN.fullmatch(value):
        return value
    return None


def _safe_evidence_summary(provider_check) -> dict:
    normalized = provider_check.normalized_result_json or {}
    response = provider_check.response_metadata_json or {}
    summary = {}
    for field in SAFE_EVIDENCE_FIELDS:
        value = _safe_number(normalized.get(field, response.get(field)))
        if value is not None:
            summary[field] = value
    risk_score = _safe_number(normalized.get("risk_score", response.get("risk_score")))
    if "score" not in summary and risk_score is not None:
        summary["score"] = risk_score

    confidence_level = _safe_token(
        normalized.get("confidence_level", response.get("confidence_level"))
    )
    if confidence_level is not None:
        summary["confidence_level"] = confidence_level

    model_name = _safe_token(normalized.get("model_name", response.get("model_name")))
    model_version = _safe_token(
        normalized.get("model_version", response.get("model_version"))
    )
    if model_name is not None:
        summary["model"] = {
            "name": model_name,
            "version": model_version or "",
        }

    issues = normalized.get("issues", response.get("issues"))
    if isinstance(issues, list):
        safe_issues = [item for item in issues if item in SAFE_ISSUE_CODES]
        if safe_issues:
            summary["issues"] = safe_issues
    return summary


def _serialize_check_provenance(provider_check) -> dict:
    normalized = provider_check.normalized_result_json or {}
    response = provider_check.response_metadata_json or {}
    contract_version = _safe_token(
        normalized.get("contract_version", response.get("contract_version"))
    )
    normalized_status = normalized.get("status")
    public_status = (
        normalized_status
        if normalized_status in SAFE_CHECK_STATUSES
        else provider_check.status
    )
    return {
        "check_id": provider_check.public_id,
        "capability": provider_check.check_type,
        "status": public_status,
        "provider": {
            "provider_id": provider_check.provider.public_id,
            "code": _safe_token(provider_check.provider.code) or "unavailable",
            "type": provider_check.provider.provider_type,
        },
        "capability_contract_version": (contract_version),
        "evidence": _safe_evidence_summary(provider_check),
        "error_code": (
            provider_check.error_code
            if provider_check.error_code in SAFE_PROVIDER_ERROR_CODES
            or (
                provider_check.error_code.startswith("provider_http_")
                and provider_check.error_code.removeprefix("provider_http_").isdigit()
            )
            else None
        ),
        "started_at": provider_check.started_at.isoformat(),
        "completed_at": (
            provider_check.completed_at.isoformat()
            if provider_check.completed_at
            else None
        ),
        "duration_ms": provider_check.duration_ms,
    }


def serialize_verification_result(verification: Verification) -> dict:
    """Build the stable public result without raw evidence or applicant data."""
    decision = getattr(verification, "decision_record", None)
    reason_codes = []
    if decision is not None:
        reason_codes = [
            value
            for value in (decision.reason_codes_json or [])
            if value in SAFE_DECISION_REASON_CODES
        ]
        fallback_reason = (
            decision.reason_code
            if decision.reason_code in SAFE_DECISION_REASON_CODES
            else None
        )
        if not reason_codes and fallback_reason is not None:
            reason_codes = [fallback_reason]

    policy_snapshot = verification.policy_snapshot_json or {}
    workflow_snapshot = verification.workflow_snapshot_json or {}
    checks = verification.provider_checks.select_related("provider").order_by(
        "started_at", "public_id"
    )
    return {
        "schema_version": VERIFICATION_RESULT_SCHEMA_VERSION,
        "verification_id": verification.public_id,
        "status": verification.status,
        "decision": (
            {
                "outcome": decision.decision,
                "type": decision.decision_type,
                "reason_codes": reason_codes,
                "approval_status": decision.approval_status,
                "contract_version": _safe_token(decision.contract_version) or "",
                "decided_at": decision.decided_at.isoformat(),
            }
            if decision is not None
            else None
        ),
        "policy": {
            "policy_id": policy_snapshot.get("id")
            or verification.policy_public_id
            or None,
            "version": policy_snapshot.get("version"),
        },
        "workflow": {
            "workflow_id": workflow_snapshot.get("workflow_id"),
            "version_id": workflow_snapshot.get("id"),
            "version": workflow_snapshot.get("version"),
        },
        "check_provenance": [_serialize_check_provenance(check) for check in checks],
        "timestamps": {
            "created_at": verification.created_at.isoformat(),
            "updated_at": verification.updated_at.isoformat(),
            "completed_at": (
                verification.completed_at.isoformat()
                if verification.completed_at
                else None
            ),
            "expires_at": verification.expires_at.isoformat(),
        },
    }
