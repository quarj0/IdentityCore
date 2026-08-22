from datetime import timedelta
from unittest.mock import patch

from django.db import transaction
from django.test import TransactionTestCase
from django.utils import timezone

from apps.organizations.models import Organization
from apps.tenants.models import Tenant
from apps.verification_subjects.models import VerificationSubject
from apps.verifications.evidence_commit import (
    schedule_verification_evidence_report_after_commit,
)
from apps.verifications.models import Verification, VerificationStatus


class VerificationEvidenceCommitTests(TransactionTestCase):
    def setUp(self):
        organization = Organization.objects.create(
            name="Evidence Commit",
            slug="evidence-commit",
        )
        tenant = Tenant.objects.create(
            organization=organization,
            name="Evidence Commit Tenant",
            slug="evidence-commit-tenant",
            status="active",
        )
        subject = VerificationSubject.objects.create(
            tenant=tenant,
            full_name="Evidence Subject",
        )
        self.verification = Verification.objects.create(
            tenant=tenant,
            organization=organization,
            verification_subject=subject,
            purpose="Evidence commit test",
            status=VerificationStatus.PENDING_CONSENT,
            expires_at=timezone.now() + timedelta(hours=1),
        )

    @patch(
        "apps.verifications.evidence_commit.ensure_verification_evidence_report"
    )
    def test_rollback_discards_evidence_callback(self, mock_evidence_report):
        with self.assertRaisesRegex(RuntimeError, "force rollback"):
            with transaction.atomic():
                schedule_verification_evidence_report_after_commit(self.verification)
                raise RuntimeError("force rollback")

        mock_evidence_report.assert_not_called()

    @patch(
        "apps.verifications.evidence_commit.ensure_verification_evidence_report"
    )
    def test_commit_reloads_persisted_verification_before_evidence_generation(
        self,
        mock_evidence_report,
    ):
        with transaction.atomic():
            self.verification.status = VerificationStatus.CANCELLED
            self.verification.completed_at = timezone.now()
            self.verification.save(
                update_fields=["status", "completed_at", "updated_at"]
            )
            schedule_verification_evidence_report_after_commit(self.verification)

        mock_evidence_report.assert_called_once()
        persisted_verification = mock_evidence_report.call_args.args[0]
        self.assertEqual(persisted_verification.pk, self.verification.pk)
        self.assertEqual(persisted_verification.status, VerificationStatus.CANCELLED)
        self.assertIsNotNone(persisted_verification.completed_at)
