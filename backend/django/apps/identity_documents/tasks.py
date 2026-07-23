import logging
from decimal import Decimal

from celery import shared_task
from django.utils import timezone

from apps.audit.services import record_audit_event
from apps.document_captures.models import DocumentCaptureStatus
from apps.identity_documents.models import IdentityDocument, IdentityDocumentStatus
from apps.providers.ai_service import (
    AIServiceUnavailable,
    run_document_classification,
    run_document_ocr,
    run_document_quality,
)
from apps.providers.models import ProviderCheckStatus, ProviderCheckType
from apps.uploads.services import promote_upload_to_media_by_storage_key
from apps.verifications.models import VerificationStatus
from common.storage import get_object_storage_temp_bucket_name

logger = logging.getLogger(__name__)


def _classification_requests_manual_review(result: dict) -> bool:
    manual_review = result.get("manual_review") or {}
    return bool(
        result.get("provider_error")
        or result.get("requires_manual_review")
        or result.get("workflow_action") == "continue_with_review"
        or manual_review.get("required")
    )


def _quality_result_requires_review(result: dict) -> bool:
    issues = set(result.get("issues") or [])
    return "document_media_missing" in issues


def _quality_result_requires_rejection(result: dict) -> bool:
    issues = set(result.get("issues") or [])
    return bool(issues) and not _quality_result_requires_review(result)


def _manual_review_classification_result(*, expected_document_type: str) -> dict:
    return {
        "status": "completed",
        "classification_status": "unknown",
        "predicted_document_type": "unknown",
        "predicted_country_code": None,
        "expected_document_type": expected_document_type,
        "matched_expected_document_type": None,
        "confidence_score": 0.0,
        "evidence_score": 0.0,
        "classification_margin": 0.0,
        "workflow_action": "continue_with_review",
        "requires_manual_review": True,
        "manual_review": {
            "required": True,
            "priority": "high",
            "reason_codes": ["document_classification_unavailable"],
            "review_category": "document_classification",
        },
        "issues": ["document_classification_unavailable"],
        "ocr": {"average_confidence": 0.0, "line_count": 0},
        "evidence": [],
        "candidates": [],
        "raw_text_lines": [],
        "score_components": {},
        "classifier": {
            "name": "ocr-evidence-document-classifier",
            "version": "v2",
            "score_type": "uncalibrated_evidence_score",
        },
        "ocr_model": {
            "name": "paddleocr",
            "version": "PP-OCRv5",
        },
        "recommendation": "continue_with_review",
    }


def _latest_provider_check_for_document(
    verification, *, identity_document_id: str, check_type: str
):
    """Resolve metadata after field-level decryption instead of querying ciphertext."""
    candidates = verification.provider_checks.filter(check_type=check_type).order_by(
        "-created_at"
    )
    return next(
        (
            check
            for check in candidates
            if (check.request_metadata_json or {}).get("identity_document_id")
            == identity_document_id
        ),
        None,
    )


@shared_task(
    queue="ai_processing",
    autoretry_for=(AIServiceUnavailable,),
    retry_backoff=15,
    retry_backoff_max=120,
    retry_jitter=True,
    retry_kwargs={"max_retries": 3},
)
def process_identity_document_task(identity_document_id: str) -> str:
    identity_document = (
        IdentityDocument.objects.select_related("verification", "verification_subject", "tenant")
        .prefetch_related("captures")
        .get(public_id=identity_document_id)
    )
    verification = identity_document.verification
    captures = list(identity_document.captures.order_by("created_at"))
    if not captures:
        identity_document.status = IdentityDocumentStatus.FAILED
        identity_document.save(update_fields=["status", "updated_at"])
        return identity_document.status

    now = timezone.now()
    ocr_provider_check = _latest_provider_check_for_document(
        verification,
        identity_document_id=identity_document.public_id,
        check_type=ProviderCheckType.DOCUMENT_OCR,
    )
    classification_provider_check = _latest_provider_check_for_document(
        verification,
        identity_document_id=identity_document.public_id,
        check_type=ProviderCheckType.DOCUMENT_CLASSIFICATION,
    )
    quality_provider_check = _latest_provider_check_for_document(
        verification,
        identity_document_id=identity_document.public_id,
        check_type=ProviderCheckType.DOCUMENT_QUALITY,
    )

    latest_quality_status = DocumentCaptureStatus.VALIDATED
    lowest_quality_score: Decimal | None = None
    issues_found: list[str] = []
    capture_quality_results: list[dict] = []
    temp_bucket = get_object_storage_temp_bucket_name()

    try:
        for capture in captures:
            quality_result = run_document_quality(
                verification_id=verification.public_id,
                document_storage_key=capture.storage_key,
                document_storage_bucket=temp_bucket,
            )
            capture.quality_score = Decimal(str(quality_result.get("quality_score", "0")))
            capture.status = (
                DocumentCaptureStatus.REJECTED
                if _quality_result_requires_rejection(quality_result)
                else DocumentCaptureStatus.VALIDATED
            )
            capture.save(update_fields=["quality_score", "status", "updated_at"])
            capture_quality_results.append(
                {
                    "capture_id": capture.public_id,
                    "status": capture.status,
                    "quality_score": float(capture.quality_score),
                    "issues": list(quality_result.get("issues") or []),
                    "metrics": quality_result.get("metrics") or {},
                    "model_name": quality_result.get("model_name", ""),
                    "model_version": quality_result.get("model_version", ""),
                }
            )
            if lowest_quality_score is None or capture.quality_score < lowest_quality_score:
                lowest_quality_score = capture.quality_score
            if quality_result.get("issues"):
                if _quality_result_requires_rejection(quality_result):
                    latest_quality_status = DocumentCaptureStatus.REJECTED
                issues_found.extend(quality_result["issues"])

        if quality_provider_check is not None:
            quality_provider_check.status = ProviderCheckStatus.COMPLETED
            quality_provider_check.completed_at = now
            quality_provider_check.response_metadata_json = {
                "capture_results": [
                    {
                        "capture_id": capture.public_id,
                        "status": capture.status,
                        "quality_score": (
                            float(capture.quality_score)
                            if capture.quality_score is not None
                            else None
                        ),
                    }
                    for capture in captures
                ],
                "issues": issues_found,
            }
            quality_provider_check.normalized_result_json = {
                "status": latest_quality_status,
                "quality_score": float(lowest_quality_score)
                if lowest_quality_score is not None
                else None,
                "issues": issues_found,
            }
            quality_provider_check.save(
                update_fields=[
                    "status",
                    "completed_at",
                    "response_metadata_json",
                    "normalized_result_json",
                    "updated_at",
                ]
            )

        primary_capture = captures[0]
        classification_result = None
        ocr_result = None
        manual_review_required = False

        try:
            classification_result = run_document_classification(
                verification_id=verification.public_id,
                document_storage_key=primary_capture.storage_key,
                document_type=identity_document.document_type_id,
                country_code=identity_document.country_profile_id,
                document_storage_bucket=temp_bucket,
            )
        except AIServiceUnavailable as exc:
            manual_review_required = True
            classification_result = _manual_review_classification_result(
                expected_document_type=identity_document.document_type_id,
            )
            classification_result["provider_error"] = str(exc)
            classification_result["issues"] = ["document_classification_unavailable"]
            classification_result["manual_review"]["reason_codes"] = [
                "document_classification_unavailable"
            ]
            classification_result["manual_review"]["priority"] = "high"
            logger.warning(
                "Document classification unavailable for verification %s: %s",
                verification.public_id,
                exc,
            )
        if classification_result is not None and _classification_requests_manual_review(
            classification_result
        ):
            manual_review_required = True

        try:
            ocr_result = run_document_ocr(
                verification_id=verification.public_id,
                document_storage_key=primary_capture.storage_key,
                document_type=identity_document.document_type_id,
                country_code=identity_document.country_profile_id,
                document_storage_bucket=temp_bucket,
            )
        except AIServiceUnavailable as exc:
            manual_review_required = True
            ocr_result = {
                "status": "completed",
                "confidence_score": 0.0,
                "extracted_fields": {},
                "raw_text_lines": [],
                "model_name": "paddleocr",
                "model_version": "PP-OCRv5",
                "provider_error": str(exc),
            }
            if classification_result is not None:
                classification_result["manual_review"]["reason_codes"] = list(
                    dict.fromkeys(
                        [
                            *classification_result["manual_review"]["reason_codes"],
                            "document_ocr_unavailable",
                        ]
                    )
                )
                classification_result["issues"] = list(
                    dict.fromkeys(
                        [
                            *classification_result.get("issues", []),
                            "document_ocr_unavailable",
                        ]
                    )
                )
            logger.warning(
                "Document OCR unavailable for verification %s: %s",
                verification.public_id,
                exc,
            )
        if ocr_result is not None and (
            ocr_result.get("requires_manual_review")
            or ocr_result.get("provider_error")
            or "document_media_missing" in set(ocr_result.get("issues") or [])
        ):
            manual_review_required = True

        identity_document.extracted_data_json = {
            **ocr_result.get("extracted_fields", {}),
            "document_classification": classification_result,
            "document_quality": {
                "status": latest_quality_status,
                "quality_score": (
                    float(lowest_quality_score)
                    if lowest_quality_score is not None
                    else None
                ),
                "issues": list(dict.fromkeys(issues_found)),
                "requires_recapture": (
                    latest_quality_status == DocumentCaptureStatus.REJECTED
                ),
                "capture_results": capture_quality_results,
            },
        }
        identity_document.status = (
            IdentityDocumentStatus.PROCESSED
            if latest_quality_status == DocumentCaptureStatus.VALIDATED
            else IdentityDocumentStatus.REJECTED
        )
        identity_document.save(update_fields=["extracted_data_json", "status", "updated_at"])

        # A document review signal is not a final verification decision. Continue
        # collecting selfie, liveness, and face-match evidence so a reviewer has
        # the complete case. The risk engine consumes the persisted classification
        # result and applies manual-review routing after biometrics finish.
        verification.status = (
            VerificationStatus.AWAITING_SELFIE
            if identity_document.status == IdentityDocumentStatus.PROCESSED
            else VerificationStatus.AWAITING_DOCUMENT
        )
        verification.save(update_fields=["status", "updated_at"])

        if classification_provider_check is not None:
            classification_provider_check.status = (
                ProviderCheckStatus.FAILED
                if classification_result.get("provider_error")
                else ProviderCheckStatus.COMPLETED
            )
            classification_provider_check.completed_at = now
            classification_provider_check.response_metadata_json = classification_result
            classification_provider_check.normalized_result_json = classification_result
            classification_provider_check.error_code = (
                "provider_unavailable"
                if classification_result.get("provider_error")
                else ""
            )
            classification_provider_check.error_message = classification_result.get(
                "provider_error", ""
            )
            classification_provider_check.save(
                update_fields=[
                    "status",
                    "error_code",
                    "error_message",
                    "completed_at",
                    "response_metadata_json",
                    "normalized_result_json",
                    "updated_at",
                ]
            )

        if ocr_provider_check is not None:
            ocr_provider_check.status = (
                ProviderCheckStatus.FAILED
                if ocr_result.get("provider_error")
                else ProviderCheckStatus.COMPLETED
            )
            ocr_provider_check.completed_at = now
            ocr_provider_check.response_metadata_json = ocr_result
            ocr_provider_check.normalized_result_json = {
                "status": identity_document.status,
                "extracted_fields": identity_document.extracted_data_json,
            }
            ocr_provider_check.error_code = (
                "provider_unavailable" if ocr_result.get("provider_error") else ""
            )
            ocr_provider_check.error_message = ocr_result.get("provider_error", "")
            ocr_provider_check.save(
                update_fields=[
                    "status",
                    "error_code",
                    "error_message",
                    "completed_at",
                    "response_metadata_json",
                    "normalized_result_json",
                    "updated_at",
                ]
            )

        for capture in captures:
            try:
                promote_upload_to_media_by_storage_key(capture.storage_key)
            except Exception as exc:
                logger.warning(
                    "Failed to promote document upload %s for verification %s: %s",
                    capture.storage_key,
                    verification.public_id,
                    exc,
                )
                record_audit_event(
                    tenant=verification.tenant,
                    actor=verification.verification_subject,
                    action="document.promotion_failed",
                    target_type="verification",
                    target_id=verification.public_id,
                    metadata={
                        "identity_document_id": identity_document.public_id,
                        "storage_key": capture.storage_key,
                    },
                    sensitive_metadata={
                        "error": str(exc),
                        "error_class": exc.__class__.__name__,
                    },
                )

        record_audit_event(
            tenant=verification.tenant,
            actor=verification.verification_subject,
            action="document.processed",
            target_type="verification",
            target_id=verification.public_id,
            metadata={
                "identity_document_id": identity_document.public_id,
                "document_status": identity_document.status,
            },
        )
        if manual_review_required:
            record_audit_event(
                tenant=verification.tenant,
                actor=verification.verification_subject,
                action="document.review_flagged",
                target_type="verification",
                target_id=verification.public_id,
                metadata={
                    "identity_document_id": identity_document.public_id,
                    "reason_codes": classification_result.get("issues", []),
                },
            )
        return identity_document.status
    except AIServiceUnavailable:
        # Infrastructure timeouts are retryable and are not evidence that the
        # submitted identity document is invalid.
        raise
    except Exception as exc:
        logger.exception(
            "Document processing failed for document %s and verification %s",
            identity_document.public_id,
            verification.public_id,
        )
        error_code = getattr(exc, "error_code", "provider_unavailable")
        provider_check_status = getattr(
            exc, "provider_check_status", ProviderCheckStatus.FAILED
        )
        internal_reason = getattr(exc, "reason", str(exc))
        identity_document.status = IdentityDocumentStatus.FAILED
        identity_document.save(update_fields=["status", "updated_at"])
        verification.status = VerificationStatus.AWAITING_DOCUMENT
        verification.save(update_fields=["status", "updated_at"])
        for provider_check in (
            quality_provider_check,
            classification_provider_check,
            ocr_provider_check,
        ):
            if provider_check is None:
                continue
            provider_check.status = provider_check_status
            provider_check.error_code = error_code
            provider_check.error_message = str(exc)
            provider_check.completed_at = now
            provider_check.save(
                update_fields=["status", "error_code", "error_message", "completed_at", "updated_at"]
            )
        record_audit_event(
            tenant=verification.tenant,
            actor=verification.verification_subject,
            action="document.processing_failed",
            target_type="verification",
            target_id=verification.public_id,
            metadata={"identity_document_id": identity_document.public_id},
            sensitive_metadata={
                "error": str(exc),
                "reason": internal_reason,
                "error_class": exc.__class__.__name__,
            },
        )
        return identity_document.status
