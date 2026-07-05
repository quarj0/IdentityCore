from apps.consent.models import ConsentRecord, ConsentTemplate


def serialize_consent_template(template: ConsentTemplate) -> dict:
    return {
        "id": template.public_id,
        "name": template.name,
        "version": template.version,
        "language": template.language,
        "content": template.content,
        "status": template.status,
        "created_at": template.created_at.isoformat(),
        "updated_at": template.updated_at.isoformat(),
    }


def serialize_consent_record(record: ConsentRecord) -> dict:
    return {
        "id": record.public_id,
        "verification_id": record.verification.public_id,
        "verification_subject_id": record.verification_subject.public_id,
        "consent_template_id": (
            record.consent_template.public_id if record.consent_template else None
        ),
        "accepted": record.accepted,
        "accepted_at": record.accepted_at.isoformat(),
        "withdrawn_at": (
            record.withdrawn_at.isoformat() if record.withdrawn_at else None
        ),
        "created_at": record.created_at.isoformat(),
    }
