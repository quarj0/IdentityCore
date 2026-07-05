from decimal import Decimal

from celery import shared_task
from django.utils import timezone

from apps.audit.services import record_audit_event
from apps.document_captures.models import DocumentCaptureStatus
from apps.identity_documents.models import IdentityDocument, IdentityDocumentStatus
from apps.providers.ai_service import run_document_ocr, run_document_quality
from apps.providers.models import ProviderCheckStatus


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
        check_type="document_ocr",
    ).order_by("-created_at").first()

    latest_quality_status = DocumentCaptureStatus.VALIDATED
    lowest_quality_score: Decimal | None = None
    issues_found: list[str] = []

    try:
        for capture in captures:
            quality_result = run_document_quality(
                verification_id=verification.public_id,
                document_storage_key=capture.storage_key,
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

        primary_capture = captures[0]
        ocr_result = run_document_ocr(
            verification_id=verification.public_id,
            document_storage_key=primary_capture.storage_key,
            document_type=identity_document.document_type_id,
            country_code=identity_document.country_profile_id,
        )
        identity_document.extracted_data_json = ocr_result.get("extracted_fields", {})
        identity_document.status = (
            IdentityDocumentStatus.PROCESSED
            if latest_quality_status == DocumentCaptureStatus.VALIDATED
            else IdentityDocumentStatus.REJECTED
        )
        identity_document.save(update_fields=["extracted_data_json", "status", "updated_at"])

        if ocr_provider_check is not None:
            ocr_provider_check.status = ProviderCheckStatus.COMPLETED
            ocr_provider_check.completed_at = now
            ocr_provider_check.response_metadata_json = ocr_result
            ocr_provider_check.normalized_result_json = {
                "status": identity_document.status,
                "extracted_fields": identity_document.extracted_data_json,
                "quality_score": float(lowest_quality_score) if lowest_quality_score is not None else None,
                "issues": issues_found,
            }
            ocr_provider_check.save(
                update_fields=["status", "completed_at", "response_metadata_json", "normalized_result_json", "updated_at"]
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
        return identity_document.status
    except Exception as exc:
        identity_document.status = IdentityDocumentStatus.FAILED
        identity_document.save(update_fields=["status", "updated_at"])
        if ocr_provider_check is not None:
            ocr_provider_check.status = ProviderCheckStatus.FAILED
            ocr_provider_check.error_code = "provider_unavailable"
            ocr_provider_check.error_message = str(exc)
            ocr_provider_check.completed_at = now
            ocr_provider_check.save(
                update_fields=["status", "error_code", "error_message", "completed_at", "updated_at"]
            )
        record_audit_event(
            tenant=verification.tenant,
            actor=verification.verification_subject,
            action="document.processing_failed",
            target_type="verification",
            target_id=verification.public_id,
            metadata={"identity_document_id": identity_document.public_id},
            sensitive_metadata={"error": str(exc)},
        )
        return identity_document.status
