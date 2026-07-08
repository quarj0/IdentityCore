from __future__ import annotations

from django.core.validators import validate_email
from django.db import transaction

from apps.accounts.models import ContactInquiry


@transaction.atomic
def submit_contact_inquiry(
    *,
    full_name: str,
    business_email: str,
    organization_name: str = "",
    interest: str = "",
    message: str,
) -> ContactInquiry:
    validate_email(business_email)
    return ContactInquiry.objects.create(
        full_name=full_name.strip(),
        business_email=business_email.strip().lower(),
        organization_name=organization_name.strip(),
        interest=interest.strip(),
        message=message.strip(),
    )
