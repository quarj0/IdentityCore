from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.audit.services import record_audit_event
from apps.verification_subjects.models import VerificationSubject
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
