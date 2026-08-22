import logging

from django.db import transaction

from apps.verifications.evidence import ensure_verification_evidence_report
from apps.verifications.models import Verification

logger = logging.getLogger(__name__)


def schedule_verification_evidence_report_after_commit(
    verification: Verification,
) -> None:
    """Generate evidence only after the surrounding domain transaction commits."""
    verification_id = verification.public_id

    def generate_evidence_report() -> None:
        try:
            persisted_verification = Verification.objects.get(public_id=verification_id)
            ensure_verification_evidence_report(persisted_verification)
        except Exception:
            logger.exception(
                "Verification evidence report generation failed for %s.",
                verification_id,
            )

    transaction.on_commit(generate_evidence_report)
