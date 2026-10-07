"""Explicit synthetic acceptance for processing fixtures, using real proof logic."""
from django.utils import timezone
from apps.consent.models import ConsentRecord


def accept_test_consent(case):
    return ConsentRecord.objects.create(tenant=case.tenant, verification=case,
        verification_subject=case.verification_subject, consent_text_snapshot="Synthetic consent for processing fixtures.",
        accepted=True, accepted_at=timezone.now())


def case_with_test_consent(case):
    accept_test_consent(case)
    return case
