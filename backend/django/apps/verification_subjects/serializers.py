from apps.verification_subjects.models import VerificationSubject


def serialize_verification_subject(subject: VerificationSubject) -> dict:
    return {
        "id": subject.public_id,
        "external_reference": subject.external_reference,
        "full_name": subject.full_name,
        "email": subject.email,
        "phone_number": subject.phone_number,
        "date_of_birth": subject.date_of_birth.isoformat()
        if subject.date_of_birth
        else None,
        "metadata": subject.metadata_json,
        "created_at": subject.created_at.isoformat(),
        "updated_at": subject.updated_at.isoformat(),
    }
