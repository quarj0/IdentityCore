from decimal import Decimal

from celery import shared_task
from django.utils import timezone

from apps.audit.services import record_audit_event
from apps.biometrics.models import (
    FaceMatchStatus,
    LivenessCheck,
    LivenessCheckStatus,
    SelfieCaptureStatus,
)
from apps.notifications.services import queue_verification_status_notifications
from apps.providers.ai_service import run_face_compare, run_liveness_check
from apps.providers.models import ProviderCheckStatus
from apps.risk.services import run_verification_risk_and_decision
from apps.uploads.services import promote_upload_to_media_by_storage_key
from apps.verifications.evidence import ensure_verification_evidence_report
from apps.webhooks.services import queue_webhook_events
from apps.verifications.models import (
    VerificationDecision,
    VerificationDecisionType,
    VerificationStatus,
)
from common.storage import (
    get_object_storage_media_bucket_name,
    get_object_storage_temp_bucket_name,
)


@shared_task(queue="ai_processing")
def process_verification_biometrics_task(liveness_check_id: str) -> str:
    liveness_check = LivenessCheck.objects.select_related(
        "verification", "selfie_capture", "tenant"
    ).get(public_id=liveness_check_id)
    verification = liveness_check.verification
    if verification.status in {
        VerificationStatus.CANCELLED,
        VerificationStatus.EXPIRED,
        VerificationStatus.FAILED,
        VerificationStatus.REJECTED,
        VerificationStatus.VERIFIED,
    }:
        return verification.status
    selfie_capture = liveness_check.selfie_capture
    face_match = (
        verification.face_matches.filter(selfie_capture=selfie_capture)
        .order_by("-matched_at")
        .first()
    )
    liveness_provider_check = verification.provider_checks.filter(
        public_id=liveness_check.provider_check_id
    ).first()
    face_provider_check = (
        verification.provider_checks.filter(
            public_id=face_match.provider_check_id
        ).first()
        if face_match is not None and face_match.provider_check_id
        else None
    )
    temp_bucket = get_object_storage_temp_bucket_name()
    media_bucket = get_object_storage_media_bucket_name()

    try:
        liveness_result = run_liveness_check(
            verification_id=verification.public_id,
            selfie_storage_key=selfie_capture.storage_key,
            liveness_type=liveness_check.liveness_type,
            selfie_storage_bucket=temp_bucket,
        )
        liveness_check.status = (
            LivenessCheckStatus.PASSED
            if liveness_result.get("passed")
            else LivenessCheckStatus.FAILED
        )
        liveness_check.score = Decimal(str(liveness_result.get("score", "0")))
        liveness_check.confidence_level = liveness_result.get("confidence_level", "")
        liveness_check.model_name = liveness_result.get("model_name", "")
        liveness_check.model_version = liveness_result.get("model_version", "")
        liveness_check.failure_reason = (
            "" if liveness_result.get("passed") else "ai_liveness_failed"
        )
        liveness_check.checked_at = timezone.now()
        liveness_check.save(
            update_fields=[
                "status",
                "score",
                "confidence_level",
                "model_name",
                "model_version",
                "failure_reason",
                "checked_at",
                "updated_at",
            ]
        )
        if liveness_provider_check is not None:
            liveness_provider_check.status = ProviderCheckStatus.COMPLETED
            liveness_provider_check.completed_at = timezone.now()
            liveness_provider_check.response_metadata_json = liveness_result
            liveness_provider_check.normalized_result_json = {
                "status": liveness_check.status,
                "score": (
                    float(liveness_check.score)
                    if liveness_check.score is not None
                    else None
                ),
                "confidence_level": liveness_check.confidence_level,
            }
            liveness_provider_check.save(
                update_fields=[
                    "status",
                    "completed_at",
                    "response_metadata_json",
                    "normalized_result_json",
                    "updated_at",
                ]
            )

        if face_match is not None:
            threshold = float(
                (verification.policy_snapshot_json or {}).get(
                    "face_match_threshold", 0.85
                )
            )
            source_document_capture = (
                face_match.document_capture
                if face_match.document_capture_id
                else face_match.identity_document.captures.order_by("created_at").first()
            )
            document_storage_key = source_document_capture.storage_key
            face_result = run_face_compare(
                verification_id=verification.public_id,
                selfie_storage_key=selfie_capture.storage_key,
                document_storage_key=document_storage_key,
                threshold=threshold,
                selfie_storage_bucket=temp_bucket,
                document_storage_bucket=(
                    media_bucket
                    if source_document_capture and source_document_capture.status != "uploaded"
                    else temp_bucket
                ),
            )
            face_match.status = (
                FaceMatchStatus.MATCHED
                if face_result.get("matched")
                else FaceMatchStatus.NOT_MATCHED
            )
            face_match.match_score = Decimal(str(face_result.get("match_score", "0")))
            face_match.confidence_level = face_result.get("confidence_level", "")
            face_match.threshold_used = Decimal(
                str(face_result.get("threshold_used", threshold))
            )
            face_match.model_name = face_result.get("model_name", "")
            face_match.model_version = face_result.get("model_version", "")
            face_match.matched_at = timezone.now()
            face_match.save(
                update_fields=[
                    "status",
                    "match_score",
                    "confidence_level",
                    "threshold_used",
                    "model_name",
                    "model_version",
                    "matched_at",
                    "updated_at",
                ]
            )
            if face_provider_check is not None:
                face_provider_check.status = ProviderCheckStatus.COMPLETED
                face_provider_check.completed_at = timezone.now()
                face_provider_check.response_metadata_json = face_result
                face_provider_check.normalized_result_json = {
                    "status": face_match.status,
                    "match_score": (
                        float(face_match.match_score)
                        if face_match.match_score is not None
                        else None
                    ),
                    "confidence_level": face_match.confidence_level,
                }
                face_provider_check.save(
                    update_fields=[
                        "status",
                        "completed_at",
                        "response_metadata_json",
                        "normalized_result_json",
                        "updated_at",
                    ]
                )

        verification.refresh_from_db(fields=["status"])
        if verification.status in {
            VerificationStatus.CANCELLED,
            VerificationStatus.EXPIRED,
            VerificationStatus.FAILED,
            VerificationStatus.REJECTED,
            VerificationStatus.VERIFIED,
        }:
            return verification.status

        selfie_capture.status = (
            SelfieCaptureStatus.VALIDATED
            if liveness_check.status == LivenessCheckStatus.PASSED
            else SelfieCaptureStatus.REJECTED
        )
        selfie_capture.save(update_fields=["status", "updated_at"])
        promote_upload_to_media_by_storage_key(selfie_capture.storage_key)

        record_audit_event(
            tenant=verification.tenant,
            actor=verification.verification_subject,
            action="liveness.completed",
            target_type="verification",
            target_id=verification.public_id,
            metadata={"liveness_check_id": liveness_check.public_id},
        )
        if face_match is not None:
            record_audit_event(
                tenant=verification.tenant,
                actor=verification.verification_subject,
                action="face_match.completed",
                target_type="verification",
                target_id=verification.public_id,
                metadata={"face_match_id": face_match.public_id},
            )

        risk_assessment, decision_record = run_verification_risk_and_decision(
            verification
        )
        if verification.metadata_json.get("workflow") == "administrator_onboarding":
            organization = verification.organization
            settings_json = dict(organization.settings_json or {})
            onboarding = dict(settings_json.get("onboarding") or {})
            admin_identity = dict(
                onboarding.get("administrator_identity_verification") or {}
            )
            admin_identity.update({
                "verification_id": verification.public_id,
                "status": decision_record.decision,
                "completed_at": timezone.now().isoformat(),
            })
            onboarding["administrator_identity_verification"] = admin_identity
            settings_json["onboarding"] = onboarding
            organization.settings_json = settings_json
            organization.save(update_fields=["settings_json", "updated_at"])
        record_audit_event(
            tenant=verification.tenant,
            actor=verification.verification_subject,
            action=f"verification.{decision_record.decision}",
            target_type="verification",
            target_id=verification.public_id,
            metadata={
                "decision_id": decision_record.public_id,
                "decision_type": decision_record.decision_type,
                "risk_assessment_id": risk_assessment.public_id,
            },
            sensitive_metadata={"reason_detail": decision_record.reason_detail},
        )
        queue_webhook_events(
            tenant=verification.tenant,
            event_type=f"verification.{decision_record.decision}",
            payload={
                "verification_id": verification.public_id,
                "external_reference": verification.external_reference,
                "status": verification.status,
            },
        )
        queue_verification_status_notifications(
            verification=verification,
            decision=decision_record.decision,
            risk_level=risk_assessment.risk_level,
        )
        ensure_verification_evidence_report(verification)
        return verification.status
    except Exception as exc:
        now = timezone.now()
        if liveness_provider_check is not None:
            liveness_provider_check.status = ProviderCheckStatus.FAILED
            liveness_provider_check.error_code = "provider_unavailable"
            liveness_provider_check.error_message = str(exc)
            liveness_provider_check.completed_at = now
            liveness_provider_check.save(
                update_fields=[
                    "status",
                    "error_code",
                    "error_message",
                    "completed_at",
                    "updated_at",
                ]
            )
        if face_provider_check is not None:
            face_provider_check.status = ProviderCheckStatus.FAILED
            face_provider_check.error_code = "provider_unavailable"
            face_provider_check.error_message = str(exc)
            face_provider_check.completed_at = now
            face_provider_check.save(
                update_fields=[
                    "status",
                    "error_code",
                    "error_message",
                    "completed_at",
                    "updated_at",
                ]
            )
        VerificationDecision.objects.update_or_create(
            verification=verification,
            defaults={
                "tenant": verification.tenant,
                "decision": VerificationStatus.FAILED,
                "decision_type": VerificationDecisionType.SYSTEM,
                "reason_code": "provider_unavailable",
                "reason_detail": "AI provider processing failed.",
                "evidence_summary_json": {"error": str(exc)},
                "decided_by": None,
                "decided_at": now,
            },
        )
        verification.status = VerificationStatus.FAILED
        verification.completed_at = now
        verification.save(update_fields=["status", "completed_at", "updated_at"])
        ensure_verification_evidence_report(verification)
        record_audit_event(
            tenant=verification.tenant,
            actor=verification.verification_subject,
            action="verification.failed",
            target_type="verification",
            target_id=verification.public_id,
            metadata={"reason_code": "provider_unavailable"},
            sensitive_metadata={"error": str(exc)},
        )
        return verification.status
