import secrets
from datetime import timedelta

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.audit.services import record_audit_event
from apps.verification_subjects.models import VerificationSubject, VerificationSubjectExport
from apps.verifications.models import RetentionLegalHold


def request_subject_deletion(*, subject: VerificationSubject, actor=None, request=None) -> dict:
    now = timezone.now()
    with transaction.atomic():
        active_holds = list(
            RetentionLegalHold.objects.filter(
                tenant_id=subject.tenant_id,
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
                "retained_categories": ["subject_profile", "verification_records", "evidence"],
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

        documents = subject.identity_documents.all()
        document_count = documents.update(
            document_number_hash="",
            local_document_name="",
            issuing_authority="",
            extracted_data_json={},
        )
        verifications = subject.verifications.all()
        verification_count = verifications.update(metadata_json={})
        decision_count = 0
        for decision in subject.verifications.select_related("decision_record").all():
            if hasattr(decision, "decision_record"):
                decision.decision_record.input_snapshot_json = {}
                decision.decision_record.save(update_fields=["input_snapshot_json", "updated_at"])
                decision_count += 1

        report = {
            "status": "completed",
            "subject_id": subject.public_id,
            "anonymized_categories": ["subject_profile", "document_metadata", "verification_metadata", "decision_inputs"],
            "retained_categories": ["audit_facts", "verification_outcomes", "raw_evidence_until_retention_due"],
            "retained_reasons": {
                "audit_facts": "Required security and compliance audit trail; subject identifiers remain pseudonymous.",
                "verification_outcomes": "Operational verification history remains without subject profile data.",
                "raw_evidence_until_retention_due": "The configured evidence retention policy is enforced by the retention worker.",
            },
            "documents_anonymized": document_count,
            "verifications_anonymized": verification_count,
            "decision_inputs_anonymized": decision_count,
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


def create_subject_export(*, subject: VerificationSubject, actor=None, request=None) -> dict:
    raw_token = secrets.token_urlsafe(32)
    verifications = []
    for verification in subject.verifications.order_by("created_at"):
        verifications.append(
            {
                "id": verification.public_id,
                "status": verification.status,
                "purpose": verification.purpose,
                "created_at": verification.created_at.isoformat(),
                "completed_at": verification.completed_at.isoformat()
                if verification.completed_at
                else None,
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
            "date_of_birth": subject.date_of_birth.isoformat()
            if subject.date_of_birth
            else None,
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
        metadata={"export_id": export.public_id, "expires_at": export.expires_at.isoformat()},
    )
    return {
        "export_id": export.public_id,
        "download_token": raw_token,
        "expires_at": export.expires_at.isoformat(),
        "redactions": payload["redactions"],
    }


def download_subject_export(*, export: VerificationSubjectExport, raw_token: str, request=None) -> dict:
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
