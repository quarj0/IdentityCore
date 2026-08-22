import logging
from decimal import Decimal

from celery import shared_task
from django.db import transaction
from django.utils import timezone

from apps.audit.services import record_audit_event
from apps.biometrics.models import (
    FaceMatchStatus,
    LivenessCheck,
    LivenessCheckStatus,
    SelfieCaptureStatus,
)
from apps.notifications.services import queue_verification_status_notifications
from apps.providers.adapters import run_face_compare, run_liveness_check
from apps.providers.models import ProviderCheckStatus, ProviderCheckType
from apps.providers.services import (
    ProviderRouteExhausted,
    execute_provider_route,
    invoke_selected_provider_operation,
    preserve_provider_result_envelope,
)
from apps.risk.services import run_verification_risk_and_decision
from apps.uploads.services import promote_upload_to_media_by_storage_key
from apps.verifications.evidence import ensure_verification_evidence_report
from apps.webhooks.services import queue_webhook_events
from apps.verifications.models import (
    ProcessingJobType,
    Verification,
    VerificationDecision,
    VerificationDecisionType,
    VerificationStatus,
)
from apps.verifications.processing_jobs import (
    ProcessingJobOwnershipLost,
    acquire_processing_job,
    complete_processing_job,
    heartbeat_processing_job,
)
from apps.verifications.transitions import TERMINAL_STATUSES, transition_verification
from common.storage import (
    get_object_storage_media_bucket_name,
    get_object_storage_temp_bucket_name,
)
from common.authorization import ServicePrincipal, require_service_access

logger = logging.getLogger(__name__)

BIOMETRICS_WORKER = ServicePrincipal(
    name="biometrics-worker", allowed_actions=frozenset({"biometrics.process"})
)


def _schedule_evidence_report_after_commit(verification: Verification) -> None:
    verification_id = verification.public_id

    def generate_evidence_report() -> None:
        try:
            persisted_verification = Verification.objects.get(public_id=verification_id)
            ensure_verification_evidence_report(persisted_verification)
        except Exception:
            logger.exception(
                "Verification evidence report generation failed for %s.",
                verification_id,
            )

    transaction.on_commit(generate_evidence_report)


def _completed_provider_result(provider_check) -> dict | None:
    """Reuse a committed provider result after a worker/finalization retry."""
    if (
        provider_check is None
        or provider_check.status != ProviderCheckStatus.COMPLETED
        or not provider_check.normalized_result_json
    ):
        return None
    result = dict(provider_check.normalized_result_json)
    result.pop("workflow_result", None)
    return result


BIOMETRIC_FINAL_VERIFICATION_STATUSES = frozenset(
    {*TERMINAL_STATUSES, VerificationStatus.MANUAL_REVIEW_REQUIRED}
)


@transaction.atomic
def _finalize_biometric_decision(
    *, verification, liveness_check, face_match, selfie_capture, processing_job
) -> str:
    # Keep the domain result, audit trail, decision, outbox, notification rows, and
    # durable processing completion in one transaction. Provider calls are kept
    # outside this transaction and their committed normalized results are reused
    # on retry rather than invoking an external provider twice.
    selfie_capture.status = (
        SelfieCaptureStatus.VALIDATED
        if liveness_check.status == LivenessCheckStatus.PASSED
        else SelfieCaptureStatus.REJECTED
    )
    selfie_capture.save(update_fields=["status", "updated_at"])

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

    risk_assessment, decision_record = run_verification_risk_and_decision(verification)
    if verification.metadata_json.get("workflow") == "administrator_onboarding":
        organization = verification.organization
        settings_json = dict(organization.settings_json or {})
        onboarding = dict(settings_json.get("onboarding") or {})
        admin_identity = dict(
            onboarding.get("administrator_identity_verification") or {}
        )
        admin_identity.update(
            {
                "verification_id": verification.public_id,
                "status": decision_record.decision,
                "completed_at": timezone.now().isoformat(),
            }
        )
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
    complete_processing_job(processing_job)
    _schedule_evidence_report_after_commit(verification)
    return verification.status


@transaction.atomic
def _finalize_unavailable_biometrics(
    *, verification, liveness_check, face_match, processing_job, error
) -> str:
    now = timezone.now()
    decision_record, _ = VerificationDecision.objects.update_or_create(
        verification=verification,
        defaults={
            "tenant": verification.tenant,
            "decision": VerificationStatus.MANUAL_REVIEW_REQUIRED,
            "decision_type": VerificationDecisionType.SYSTEM,
            "reason_code": "biometric_provider_unavailable",
            "reason_detail": (
                "Biometric processing was unavailable. The submitted evidence "
                "requires human review."
            ),
            "evidence_summary_json": {
                "provider_error": str(error),
                "liveness_status": liveness_check.status,
                "face_match_status": (
                    face_match.status if face_match is not None else "missing"
                ),
            },
            "decided_by": None,
            "decided_at": now,
        },
    )
    transition_verification(
        verification,
        VerificationStatus.MANUAL_REVIEW_REQUIRED,
        clear_completed_at=True,
    )
    record_audit_event(
        tenant=verification.tenant,
        actor=verification.verification_subject,
        action="verification.manual_review_required",
        target_type="verification",
        target_id=verification.public_id,
        metadata={
            "decision_id": decision_record.public_id,
            "reason_code": "biometric_provider_unavailable",
        },
        sensitive_metadata={"error": str(error)},
    )
    queue_webhook_events(
        tenant=verification.tenant,
        event_type="verification.manual_review_required",
        payload={
            "verification_id": verification.public_id,
            "external_reference": verification.external_reference,
            "status": verification.status,
            "reason_code": "biometric_provider_unavailable",
        },
    )
    queue_verification_status_notifications(
        verification=verification,
        decision=verification.status,
        risk_level="high",
    )
    complete_processing_job(processing_job)
    _schedule_evidence_report_after_commit(verification)
    return verification.status


@shared_task(queue="ai_processing")
def process_verification_biometrics_task(liveness_check_id: str) -> str:
    liveness_check = LivenessCheck.objects.select_related(
        "verification", "selfie_capture", "tenant", "challenge"
    ).get(public_id=liveness_check_id)
    require_service_access(
        BIOMETRICS_WORKER,
        action="biometrics.process",
        resource=liveness_check,
    )
    verification = liveness_check.verification
    processing_job = acquire_processing_job(
        job_type=ProcessingJobType.BIOMETRICS,
        resource=liveness_check,
    )
    if processing_job is None:
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

    if verification.status in BIOMETRIC_FINAL_VERIFICATION_STATUSES:
        complete_processing_job(processing_job)
        return verification.status

    if liveness_check.status == LivenessCheckStatus.ERROR:
        return _finalize_unavailable_biometrics(
            verification=verification,
            liveness_check=liveness_check,
            face_match=face_match,
            processing_job=processing_job,
            error=RuntimeError(
                liveness_check.failure_reason or "Biometric provider unavailable."
            ),
        )
    if face_match is not None and face_match.status == FaceMatchStatus.ERROR:
        return _finalize_unavailable_biometrics(
            verification=verification,
            liveness_check=liveness_check,
            face_match=face_match,
            processing_job=processing_job,
            error=RuntimeError("Face-match provider unavailable."),
        )
    if (
        liveness_check.status != LivenessCheckStatus.INCONCLUSIVE
        and (face_match is None or face_match.status != FaceMatchStatus.INCONCLUSIVE)
    ):
        promote_upload_to_media_by_storage_key(selfie_capture.storage_key)
        return _finalize_biometric_decision(
            verification=verification,
            liveness_check=liveness_check,
            face_match=face_match,
            selfie_capture=selfie_capture,
            processing_job=processing_job,
        )

    temp_bucket = get_object_storage_temp_bucket_name()
    media_bucket = get_object_storage_media_bucket_name()
    processing_stage = "liveness"

    try:
        if liveness_check.status == LivenessCheckStatus.INCONCLUSIVE:
            liveness_result = _completed_provider_result(liveness_provider_check)
            if liveness_result is None:
                liveness_operation_kwargs = {
                    "verification_id": verification.public_id,
                    "selfie_storage_key": selfie_capture.storage_key,
                    "liveness_type": liveness_check.liveness_type,
                    "selfie_storage_bucket": temp_bucket,
                    "selfie_mime_type": selfie_capture.mime_type,
                    "challenge_actions": (
                        liveness_check.challenge.actions
                        if liveness_check.challenge_id
                        else None
                    ),
                }
                liveness_execution = execute_provider_route(
                    verification=verification,
                    check_type=ProviderCheckType.LIVENESS,
                    operation=lambda provider, timeout: invoke_selected_provider_operation(
                        provider=provider,
                        check_type=ProviderCheckType.LIVENESS,
                        timeout_seconds=timeout,
                        operation_kwargs=liveness_operation_kwargs,
                        built_in_operation=run_liveness_check,
                    ),
                    request_metadata={"liveness_check_id": liveness_check.public_id},
                    initial_provider_check=liveness_provider_check,
                    processing_job=processing_job,
                )
                liveness_result = liveness_execution.result
                liveness_provider_check = liveness_execution.provider_check
                liveness_check.provider_check_id = liveness_provider_check.public_id

            metrics = liveness_result.get("metrics") or {}
            face_count = metrics.get("face_count")
            detection_confidence = metrics.get("avg_detection_confidence")
            model_name = liveness_result.get("model_name")
            model_version = liveness_result.get("model_version")
            if (
                isinstance(face_count, bool)
                or not isinstance(face_count, int)
                or face_count < 0
                or detection_confidence is None
                or not model_name
                or not model_version
            ):
                raise ValueError(
                    "Liveness provider omitted required face detection evidence."
                )

            selfie_capture.face_count = face_count
            selfie_capture.face_detection_confidence = Decimal(
                str(detection_confidence)
            )
            selfie_capture.face_detection_model_name = model_name
            selfie_capture.face_detection_model_version = model_version
            selfie_capture.save(
                update_fields=[
                    "face_count",
                    "face_detection_confidence",
                    "face_detection_model_name",
                    "face_detection_model_version",
                    "updated_at",
                ]
            )
            liveness_check.status = (
                LivenessCheckStatus.PASSED
                if liveness_result.get("passed") and face_count == 1
                else LivenessCheckStatus.FAILED
            )
            liveness_check.score = Decimal(str(liveness_result.get("score", "0")))
            liveness_check.confidence_level = liveness_result.get(
                "confidence_level", ""
            )
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
                    "provider_check_id",
                    "checked_at",
                    "updated_at",
                ]
            )
            heartbeat_processing_job(processing_job)
            if liveness_provider_check is not None:
                liveness_provider_check.status = ProviderCheckStatus.COMPLETED
                liveness_provider_check.completed_at = timezone.now()
                liveness_provider_check.response_metadata_json = liveness_result
                liveness_provider_check.normalized_result_json = (
                    preserve_provider_result_envelope(
                        liveness_provider_check,
                        workflow_result={
                            "status": liveness_check.status,
                            "score": (
                                float(liveness_check.score)
                                if liveness_check.score is not None
                                else None
                            ),
                            "confidence_level": liveness_check.confidence_level,
                        },
                    )
                )
                liveness_provider_check.save(
                    update_fields=[
                        "status",
                        "completed_at",
                        "response_metadata_json",
                        "normalized_result_json",
                        "updated_at",
                    ]
                )

        if face_match is not None and face_match.status == FaceMatchStatus.INCONCLUSIVE:
            threshold = float(
                (verification.policy_snapshot_json or {}).get(
                    "face_match_threshold", 0.85
                )
            )
            source_document_capture = (
                face_match.document_capture
                if face_match.document_capture_id
                else face_match.identity_document.captures.order_by(
                    "created_at"
                ).first()
            )
            document_storage_key = source_document_capture.storage_key
            processing_stage = "face_match"
            face_result = _completed_provider_result(face_provider_check)
            if face_result is None:
                face_operation_kwargs = {
                    "verification_id": verification.public_id,
                    "selfie_storage_key": selfie_capture.storage_key,
                    "document_storage_key": document_storage_key,
                    "threshold": threshold,
                    "selfie_storage_bucket": temp_bucket,
                    "selfie_mime_type": selfie_capture.mime_type,
                    "document_storage_bucket": (
                        media_bucket
                        if source_document_capture
                        and source_document_capture.status != "uploaded"
                        else temp_bucket
                    ),
                }
                face_execution = execute_provider_route(
                    verification=verification,
                    check_type=ProviderCheckType.FACE_MATCH,
                    operation=lambda provider, timeout: invoke_selected_provider_operation(
                        provider=provider,
                        check_type=ProviderCheckType.FACE_MATCH,
                        timeout_seconds=timeout,
                        operation_kwargs=face_operation_kwargs,
                        built_in_operation=run_face_compare,
                    ),
                    request_metadata={"face_match_id": face_match.public_id},
                    initial_provider_check=face_provider_check,
                    processing_job=processing_job,
                )
                face_result = face_execution.result
                face_provider_check = face_execution.provider_check
                face_match.provider_check_id = face_provider_check.public_id

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
                    "provider_check_id",
                    "matched_at",
                    "updated_at",
                ]
            )
            heartbeat_processing_job(processing_job)
            if face_provider_check is not None:
                face_provider_check.status = ProviderCheckStatus.COMPLETED
                face_provider_check.completed_at = timezone.now()
                face_provider_check.response_metadata_json = face_result
                face_provider_check.normalized_result_json = (
                    preserve_provider_result_envelope(
                        face_provider_check,
                        workflow_result={
                            "status": face_match.status,
                            "match_score": (
                                float(face_match.match_score)
                                if face_match.match_score is not None
                                else None
                            ),
                            "confidence_level": face_match.confidence_level,
                        },
                    )
                )
                face_provider_check.save(
                    update_fields=[
                        "status",
                        "completed_at",
                        "response_metadata_json",
                        "normalized_result_json",
                        "updated_at",
                    ]
                )
    except ProcessingJobOwnershipLost:
        raise
    except ProviderRouteExhausted:
        now = timezone.now()
        if processing_stage == "liveness":
            liveness_check.status = LivenessCheckStatus.ERROR
            liveness_check.failure_reason = "provider_route_exhausted"
            liveness_check.checked_at = now
            liveness_check.save(
                update_fields=[
                    "status",
                    "failure_reason",
                    "checked_at",
                    "updated_at",
                ]
            )
        elif face_match is not None:
            face_match.status = FaceMatchStatus.ERROR
            face_match.matched_at = now
            face_match.save(update_fields=["status", "matched_at", "updated_at"])
        complete_processing_job(processing_job)
        verification.refresh_from_db(fields=["status"])
        return verification.status
    except Exception as exc:
        now = timezone.now()
        if processing_stage == "liveness" and liveness_provider_check is not None:
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
        if processing_stage == "face_match" and face_provider_check is not None:
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
        if processing_stage == "liveness":
            liveness_check.status = LivenessCheckStatus.ERROR
            liveness_check.failure_reason = "provider_unavailable"
            liveness_check.checked_at = now
            liveness_check.save(
                update_fields=[
                    "status",
                    "failure_reason",
                    "checked_at",
                    "updated_at",
                ]
            )
        elif face_match is not None:
            face_match.status = FaceMatchStatus.ERROR
            face_match.matched_at = now
            face_match.save(update_fields=["status", "matched_at", "updated_at"])

        return _finalize_unavailable_biometrics(
            verification=verification,
            liveness_check=liveness_check,
            face_match=face_match,
            processing_job=processing_job,
            error=exc,
        )

    promote_upload_to_media_by_storage_key(selfie_capture.storage_key)
    return _finalize_biometric_decision(
        verification=verification,
        liveness_check=liveness_check,
        face_match=face_match,
        selfie_capture=selfie_capture,
        processing_job=processing_job,
    )
