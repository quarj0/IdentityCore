from decimal import Decimal

from celery import shared_task
from django.utils import timezone

from apps.audit.services import record_audit_event
from apps.document_captures.models import DocumentCaptureStatus
from apps.identity_documents.models import IdentityDocument, IdentityDocumentStatus
from apps.providers.ai_service import (
    run_document_classification,
    run_document_ocr,
    run_document_quality,
)
from apps.providers.models import ProviderCheckStatus, ProviderCheckType
from apps.uploads.services import promote_upload_to_media_by_storage_key
from apps.verifications.models import VerificationStatus
from common.storage import get_object_storage_temp_bucket_name


@shared_task(queue="ai_processing")
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
    ocr_provider_check = verification.provider_checks.filter(
        request_metadata_json__identity_document_id=identity_document.public_id,
        check_type=ProviderCheckType.DOCUMENT_OCR,
    ).order_by("-created_at").first()
    classification_provider_check = verification.provider_checks.filter(
        request_metadata_json__identity_document_id=identity_document.public_id,
        check_type=ProviderCheckType.DOCUMENT_CLASSIFICATION,
    ).order_by("-created_at").first()
    quality_provider_check = verification.provider_checks.filter(
        request_metadata_json__identity_document_id=identity_document.public_id,
        check_type=ProviderCheckType.DOCUMENT_QUALITY,
    ).order_by("-created_at").first()

    latest_quality_status = DocumentCaptureStatus.VALIDATED
    lowest_quality_score: Decimal | None = None
    issues_found: list[str] = []
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
                DocumentCaptureStatus.VALIDATED
                if not quality_result.get("issues")
                else DocumentCaptureStatus.REJECTED
            )
            capture.save(update_fields=["quality_score", "status", "updated_at"])
            if lowest_quality_score is None or capture.quality_score < lowest_quality_score:
                lowest_quality_score = capture.quality_score
            if quality_result.get("issues"):
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
        classification_result = run_document_classification(
            verification_id=verification.public_id,
            document_storage_key=primary_capture.storage_key,
            document_type=identity_document.document_type_id,
            country_code=identity_document.country_profile_id,
            document_storage_bucket=temp_bucket,
        )
        ocr_result = run_document_ocr(
            verification_id=verification.public_id,
            document_storage_key=primary_capture.storage_key,
            document_type=identity_document.document_type_id,
            country_code=identity_document.country_profile_id,
            document_storage_bucket=temp_bucket,
        )
        identity_document.extracted_data_json = {
            **ocr_result.get("extracted_fields", {}),
            "document_classification": classification_result,
        }
        classification_valid = bool(
            classification_result.get("matched_expected_document_type")
        ) and not classification_result.get("issues")
        identity_document.status = (
            IdentityDocumentStatus.PROCESSED
            if latest_quality_status == DocumentCaptureStatus.VALIDATED
            and classification_valid
            else IdentityDocumentStatus.REJECTED
        )
        identity_document.save(update_fields=["extracted_data_json", "status", "updated_at"])

        verification.status = (
            VerificationStatus.AWAITING_SELFIE
            if identity_document.status == IdentityDocumentStatus.PROCESSED
            else VerificationStatus.AWAITING_DOCUMENT
        )
        verification.save(update_fields=["status", "updated_at"])

        if classification_provider_check is not None:
            classification_provider_check.status = ProviderCheckStatus.COMPLETED
            classification_provider_check.completed_at = now
            classification_provider_check.response_metadata_json = classification_result
            classification_provider_check.normalized_result_json = classification_result
            classification_provider_check.save(
                update_fields=[
                    "status",
                    "completed_at",
                    "response_metadata_json",
                    "normalized_result_json",
                    "updated_at",
                ]
            )

        if ocr_provider_check is not None:
            ocr_provider_check.status = ProviderCheckStatus.COMPLETED
            ocr_provider_check.completed_at = now
            ocr_provider_check.response_metadata_json = ocr_result
            ocr_provider_check.normalized_result_json = {
                "status": identity_document.status,
                "extracted_fields": identity_document.extracted_data_json,
            }
            ocr_provider_check.save(
                update_fields=["status", "completed_at", "response_metadata_json", "normalized_result_json", "updated_at"]
            )

        for capture in captures:
            promote_upload_to_media_by_storage_key(capture.storage_key)

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
        return identity_document.status
    except Exception as exc:
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
