import json

from apps.verifications.models import Verification
from common.storage import (
    build_signed_download_url,
    get_object_storage_evidence_bucket_name,
    put_object_bytes,
)


TERMINAL_EVIDENCE_STATUSES = {"verified", "rejected", "cancelled", "expired", "failed"}


def build_verification_evidence_storage_key(verification: Verification) -> str:
    return (
        f"organizations/{verification.organization.public_id}"
        f"/verifications/{verification.public_id}"
        f"/reports/verification-report.json"
    )


def build_verification_evidence_download_url(verification: Verification) -> str | None:
    storage_key = (verification.metadata_json or {}).get("evidence_report_storage_key", "")
    if not storage_key:
        return None
    bucket_name = get_object_storage_evidence_bucket_name()
    if not bucket_name:
        return None
    return build_signed_download_url(
        storage_key=storage_key,
        filename=f"{verification.public_id}-verification-report.json",
        bucket_name=bucket_name,
    )


def serialize_verification_evidence_report(verification: Verification) -> dict:
    latest_liveness = verification.liveness_checks.order_by("-checked_at").first()
    latest_face_match = verification.face_matches.order_by("-matched_at").first()
    risk_assessment = getattr(verification, "risk_assessment", None)
    decision_record = getattr(verification, "decision_record", None)

    return {
        "verification_id": verification.public_id,
        "organization_id": verification.organization.public_id,
        "tenant_id": verification.tenant.public_id,
        "status": verification.status,
        "purpose": verification.purpose,
        "external_reference": verification.external_reference,
        "verification_subject": {
            "id": verification.verification_subject.public_id,
            "full_name": verification.verification_subject.full_name,
            "email": verification.verification_subject.email,
            "phone_number": verification.verification_subject.phone_number,
        },
        "document_captures": [
            {
                "id": capture.public_id,
                "side": capture.side,
                "storage_key": capture.storage_key,
                "status": capture.status,
                "quality_score": float(capture.quality_score) if capture.quality_score is not None else None,
            }
            for identity_document in verification.identity_documents.prefetch_related("captures")
            for capture in identity_document.captures.all()
        ],
        "selfie_captures": [
            {
                "id": selfie.public_id,
                "storage_key": selfie.storage_key,
                "status": selfie.status,
                "capture_type": selfie.capture_type,
            }
            for selfie in verification.selfie_captures.all()
        ],
        "checks": {
            "liveness": (
                {
                    "status": latest_liveness.status,
                    "score": float(latest_liveness.score) if latest_liveness.score is not None else None,
                    "confidence_level": latest_liveness.confidence_level,
                    "model_name": latest_liveness.model_name,
                    "model_version": latest_liveness.model_version,
                }
                if latest_liveness is not None
                else None
            ),
            "face_match": (
                {
                    "status": latest_face_match.status,
                    "match_score": (
                        float(latest_face_match.match_score)
                        if latest_face_match.match_score is not None
                        else None
                    ),
                    "confidence_level": latest_face_match.confidence_level,
                    "model_name": latest_face_match.model_name,
                    "model_version": latest_face_match.model_version,
                }
                if latest_face_match is not None
                else None
            ),
        },
        "risk_assessment": (
            {
                "id": risk_assessment.public_id,
                "risk_level": risk_assessment.risk_level,
                "risk_score": float(risk_assessment.risk_score),
                "recommendation": risk_assessment.recommendation,
            }
            if risk_assessment is not None
            else None
        ),
        "decision": (
            {
                "id": decision_record.public_id,
                "decision": decision_record.decision,
                "decision_type": decision_record.decision_type,
                "reason_code": decision_record.reason_code,
                "reason_detail": decision_record.reason_detail,
                "decided_at": decision_record.decided_at.isoformat(),
            }
            if decision_record is not None
            else None
        ),
        "policy_snapshot": verification.policy_snapshot_json,
        "created_at": verification.created_at.isoformat(),
        "completed_at": verification.completed_at.isoformat() if verification.completed_at else None,
    }


def ensure_verification_evidence_report(verification: Verification) -> str | None:
    if verification.status not in TERMINAL_EVIDENCE_STATUSES:
        return None
    bucket_name = get_object_storage_evidence_bucket_name()
    if not bucket_name:
        return None

    storage_key = build_verification_evidence_storage_key(verification)
    payload = serialize_verification_evidence_report(verification)
    put_object_bytes(
        bucket_name=bucket_name,
        key=storage_key,
        content=json.dumps(payload, indent=2, sort_keys=True).encode("utf-8"),
        content_type="application/json",
    )
    metadata_json = dict(verification.metadata_json or {})
    metadata_json["evidence_report_storage_key"] = storage_key
    verification.metadata_json = metadata_json
    verification.save(update_fields=["metadata_json", "updated_at"])
    return storage_key
