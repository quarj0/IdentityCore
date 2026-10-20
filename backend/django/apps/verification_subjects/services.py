import secrets
from datetime import timedelta

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.audit.services import lock_audit_chain, record_audit_event
from apps.verification_subjects.models import (
    VerificationSubject,
    VerificationSubjectExport,
)
from apps.verifications.models import RetentionLegalHold


def _privacy_actor(subject, actor):
    if actor is None:
        return (
            None  # Trusted internal maintenance; HTTP callers always supply an actor.
        )
    from apps.accounts.models import PlatformUser
    from common.authorization import AuthorizationAction, decide_user_access
    from rest_framework.exceptions import PermissionDenied

    actor = (
        PlatformUser.objects.select_for_update(no_key=True).filter(pk=actor.pk).first()
    )
    if (
        actor is None
        or not decide_user_access(
            actor,
            action=AuthorizationAction.TENANT_ACCESS,
            tenant=subject,
            permission_code="manage_subject_privacy",
        ).allowed
    ):
        raise PermissionDenied("Subject privacy permission is required.")
    return actor


def request_subject_deletion(
    *, subject: VerificationSubject, actor=None, request=None
) -> dict:
    now = timezone.now()
    with transaction.atomic():
        lock_audit_chain(subject.tenant_id)
        actor = _privacy_actor(subject, actor)
        # Match processing finalizers: audit -> cases -> sessions/jobs -> subject.
        cases = list(
            subject.verifications.select_for_update(of=("self",), no_key=True).order_by(
                "pk"
            )
        )
        subject = VerificationSubject.objects.select_for_update(no_key=True).get(
            pk=subject.pk
        )
        active_holds = list(
            RetentionLegalHold.objects.filter(
                verification__verification_subject_id=subject.id,
                released_at__isnull=True,
            ).filter(Q(expires_at__isnull=True) | Q(expires_at__gt=now))
        )
        active_holds += list(
            RetentionLegalHold.objects.filter(
                tenant_id=subject.tenant_id,
                verification__isnull=True,
                released_at__isnull=True,
            ).filter(Q(expires_at__isnull=True) | Q(expires_at__gt=now))
        )
        if active_holds:
            report = {
                "status": "deferred",
                "subject_id": subject.public_id,
                "retained_categories": [
                    "subject_profile",
                    "verification_records",
                    "evidence",
                ],
                "reasons": [hold.reason for hold in active_holds],
            }
            record_audit_event(
                tenant=subject.tenant,
                actor=actor,
                request=request,
                action="privacy.subject_deletion_deferred",
                target_type="verification_subject",
                target_id=subject.public_id,
                metadata={"hold_count": len(active_holds)},
            )
            return report

        from apps.verifications.models import (
            ProcessingJob,
            ProcessingJobStatus,
            VerificationSessionStatus,
            VerificationStatus,
        )
        from apps.verifications.transitions import (
            TERMINAL_STATUSES,
            transition_verification,
        )

        for case in cases:
            case.sessions.update(
                status=VerificationSessionStatus.REVOKED, updated_at=now
            )
            ProcessingJob.objects.filter(
                verification=case,
                status__in=[ProcessingJobStatus.QUEUED, ProcessingJobStatus.PROCESSING],
            ).update(
                status=ProcessingJobStatus.EXHAUSTED,
                error_code="subject_deleted",
                completed_at=now,
                heartbeat_at=now,
                lease_expires_at=now,
                updated_at=now,
            )
            cancelled = case.status not in TERMINAL_STATUSES
            if cancelled:
                transition_verification(
                    case, VerificationStatus.CANCELLED, completed_at=now
                )
            # Opaque report references remain tracked until retention removes them.
            metadata = (
                case.metadata_json if isinstance(case.metadata_json, dict) else {}
            )
            case.metadata_json = {
                key: value
                for key, value in metadata.items()
                if key
                in {
                    "evidence_report_storage_key",
                    "evidence_report_pdf_storage_key",
                    "evidence_report_encrypted",
                    "evidence_report_pdf_encrypted",
                    "evidence_reports_retired_at",
                    "evidence_report_pending_cleanup_keys",
                }
            }
            case.external_reference = ""
            case.save(
                update_fields=["metadata_json", "external_reference", "updated_at"]
            )
            if cancelled:
                from apps.webhooks.services import queue_webhook_events

                queue_webhook_events(
                    tenant=case.tenant,
                    event_type="verification.cancelled",
                    payload={
                        "verification_id": case.public_id,
                        "external_reference": "",
                        "status": "cancelled",
                    },
                )
            for check in case.provider_checks.select_related("tenant", "verification"):
                check.response_metadata_json = {}
                check.normalized_result_json = {}
                check.error_message = ""
                check.save(
                    update_fields=[
                        "response_metadata_json",
                        "normalized_result_json",
                        "error_message",
                        "updated_at",
                    ]
                )
        # Previously generated subject exports contain their own profile copies.
        for export in VerificationSubjectExport.objects.filter(
            subject=subject
        ).select_related("tenant"):
            export.payload_json = {}
            export.download_token_hash = ""
            export.expires_at = now
            export.save(
                update_fields=[
                    "payload_json",
                    "download_token_hash",
                    "expires_at",
                    "updated_at",
                ]
            )

        from apps.notifications.privacy import scrub_subject_notifications

        notifications_anonymized = scrub_subject_notifications(subject)

        subject.full_name = "Deleted subject"
        subject.external_reference = ""
        subject.email = ""
        subject.phone_number = ""
        subject.date_of_birth = None
        subject.metadata_json = {}
        subject.deleted_at = now
        subject.save(
            update_fields=[
                "full_name",
                "external_reference",
                "email",
                "phone_number",
                "date_of_birth",
                "metadata_json",
                "deleted_at",
                "updated_at",
            ]
        )

        document_count = 0
        for document in subject.identity_documents.select_related("tenant").all():
            document.document_number_hash = ""
            document.local_document_name = ""
            document.issuing_authority = ""
            document.extracted_data_json = {}
            document.save(
                update_fields=[
                    "document_number_hash",
                    "local_document_name",
                    "issuing_authority",
                    "extracted_data_json",
                    "updated_at",
                ]
            )
            document_count += 1
        verification_count = len(cases)
        decision_count = 0
        for decision in subject.verifications.select_related("decision_record").all():
            if hasattr(decision, "decision_record"):
                decision.decision_record.input_snapshot_json = {}
                decision.decision_record.save(
                    update_fields=["input_snapshot_json", "updated_at"]
                )
                decision_count += 1

        from apps.risk.models import ReuseFingerprint
        from apps.risk.reuse import lock_subject_fingerprints

        lock_subject_fingerprints(subject.pk)
        ReuseFingerprint.objects.filter(
            tenant=subject.tenant, verification__verification_subject=subject
        ).delete()

        report = {
            "status": "completed",
            "subject_id": subject.public_id,
            "anonymized_categories": [
                "subject_profile",
                "document_metadata",
                "verification_metadata",
                "decision_inputs",
                "provider_result_copies",
                "subject_exports",
                "subject_notifications",
            ],
            "retained_categories": [
                "audit_facts",
                "verification_outcomes",
                "raw_evidence_until_retention_due",
            ],
            "retained_reasons": {
                "audit_facts": "Required security and compliance audit trail; subject identifiers remain pseudonymous.",
                "verification_outcomes": "Operational verification history remains without subject profile data.",
                "raw_evidence_until_retention_due": "The configured evidence retention policy is enforced by the retention worker.",
            },
            "documents_anonymized": document_count,
            "verifications_anonymized": verification_count,
            "decision_inputs_anonymized": decision_count,
            "notifications_anonymized": notifications_anonymized,
        }
        record_audit_event(
            tenant=subject.tenant,
            actor=actor,
            request=request,
            action="privacy.subject_deletion_completed",
            target_type="verification_subject",
            target_id=subject.public_id,
            metadata={
                "documents_anonymized": document_count,
                "verifications_anonymized": verification_count,
                "decision_inputs_anonymized": decision_count,
            },
        )
        return report


@transaction.atomic
def create_subject_export(
    *, subject: VerificationSubject, actor=None, request=None
) -> dict:
    lock_audit_chain(subject.tenant_id)
    actor = _privacy_actor(subject, actor)
    subject = VerificationSubject.objects.select_for_update(no_key=True).get(
        pk=subject.pk
    )
    if subject.deleted_at is not None:
        from rest_framework.exceptions import NotFound

        raise NotFound("This subject is no longer available.")
    raw_token = secrets.token_urlsafe(32)
    verifications = []
    for verification in subject.verifications.order_by("created_at"):
        verifications.append(
            {
                "id": verification.public_id,
                "status": verification.status,
                "purpose": verification.purpose,
                "created_at": verification.created_at.isoformat(),
                "completed_at": (
                    verification.completed_at.isoformat()
                    if verification.completed_at
                    else None
                ),
                "decision": (
                    verification.decision_record.decision
                    if hasattr(verification, "decision_record")
                    else None
                ),
            }
        )
    payload = {
        "subject": {
            "id": subject.public_id,
            "external_reference": subject.external_reference,
            "full_name": subject.full_name,
            "email": subject.email,
            "phone_number": subject.phone_number,
            "date_of_birth": (
                subject.date_of_birth.isoformat() if subject.date_of_birth else None
            ),
            "metadata": {
                key: value
                for key, value in (subject.metadata_json or {}).items()
                if not any(
                    marker in key.lower() for marker in ("internal", "note", "secret")
                )
            },
        },
        "verifications": verifications,
        "redactions": [
            "document numbers and biometric templates",
            "raw document/selfie media",
            "provider credentials and internal notes",
            "network and device fingerprints",
        ],
    }
    export = VerificationSubjectExport(
        tenant=subject.tenant,
        subject=subject,
        payload_json=payload,
        expires_at=timezone.now() + timedelta(hours=1),
    )
    export.set_download_token(raw_token)
    export.save()
    record_audit_event(
        tenant=subject.tenant,
        actor=actor,
        request=request,
        action="privacy.subject_export_created",
        target_type="verification_subject",
        target_id=subject.public_id,
        metadata={
            "export_id": export.public_id,
            "expires_at": export.expires_at.isoformat(),
        },
    )
    return {
        "export_id": export.public_id,
        "download_token": raw_token,
        "expires_at": export.expires_at.isoformat(),
        "redactions": payload["redactions"],
    }


def download_subject_export(
    *, export: VerificationSubjectExport, raw_token: str, request=None
) -> dict:
    if export.is_expired or not export.matches_download_token(raw_token):
        raise ValueError("Export token is invalid or expired.")
    export.downloaded_at = timezone.now()
    export.save(update_fields=["downloaded_at", "updated_at"])
    record_audit_event(
        tenant=export.tenant,
        request=request,
        action="privacy.subject_export_downloaded",
        target_type="verification_subject",
        target_id=export.subject.public_id,
        metadata={"export_id": export.public_id},
    )
    return export.payload_json
