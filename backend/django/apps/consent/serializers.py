from apps.consent.models import ConsentRecord, ConsentTemplate


def serialize_consent_template(template: ConsentTemplate) -> dict:
    return {
        "id": template.public_id,
        "name": template.name,
        "version": template.version,
        "language": template.language,
        "content": template.content,
        "evidence_scope": (
            template.evidence_scope_json
            if template.evidence_scope_json is not None
            else ["document", "biometrics"]
        ),
        "status": template.status,
        "created_at": template.created_at.isoformat(),
        "updated_at": template.updated_at.isoformat(),
    }


def serialize_consent_record(record: ConsentRecord) -> dict:
    try:
        proof = record.proof_json or {}
    except ValueError:
        proof = {}
    # Migration 0002 assigned en to records whose original locale was not retained.
    # A mutable template cannot establish the language shown at acceptance time.
    locale_recorded = bool(record.consent_locale) and bool(
        proof or record.consent_content_hash or record.consent_locale != "en"
    )
    return {
        "id": record.public_id,
        "verification_id": record.verification.public_id,
        "verification_subject_id": record.verification_subject.public_id,
        "consent_template_id": (
            record.consent_template.public_id if record.consent_template else None
        ),
        "notice_version": proof.get("notice_version"),
        "purpose": proof.get("purpose"),
        "environment": proof.get("environment"),
        "evidence_scope": proof.get("evidence_scope"),
        "binding_source": proof.get("binding_source"),
        "consent_locale": record.consent_locale if locale_recorded else None,
        "consent_locale_status": (
            "recorded" if locale_recorded else "unavailable_legacy"
        ),
        "consent_content_hash": record.consent_content_hash,
        "accepted": record.accepted,
        "accepted_at": record.accepted_at.isoformat(),
        "withdrawn_at": (
            record.withdrawn_at.isoformat() if record.withdrawn_at else None
        ),
        "created_at": record.created_at.isoformat(),
    }
