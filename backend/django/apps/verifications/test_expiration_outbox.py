from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from apps.organizations.models import Organization
from apps.tenants.models import Tenant
from apps.verification_subjects.models import VerificationSubject
from apps.verifications.models import Verification, VerificationStatus
from apps.verifications.tasks import _expire_pending_verification


class VerificationExpirationOutboxTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            name="Expiration Outbox",
            slug="expiration-outbox",
        )
        self.tenant = Tenant.objects.create(
            organization=self.organization,
            name="Expiration Outbox Tenant",
            slug="expiration-outbox-tenant",
            status="active",
        )
        self.subject = VerificationSubject.objects.create(
            tenant=self.tenant,
            full_name="Expiration Subject",
        )
        self.verification = Verification.objects.create(
            tenant=self.tenant,
            organization=self.organization,
            verification_subject=self.subject,
            purpose="Expiration outbox test",
            status=VerificationStatus.PENDING_CONSENT,
            expires_at=timezone.now() - timedelta(minutes=1),
        )

    @patch(
        "apps.verifications.evidence_commit.ensure_verification_evidence_report"
    )
    @patch("apps.verifications.tasks.queue_webhook_events")
    def test_outbox_failure_rolls_back_without_evidence_write(
        self,
        mock_queue_webhooks,
        mock_evidence_report,
    ):
        mock_queue_webhooks.side_effect = RuntimeError("outbox insert failed")

        with self.captureOnCommitCallbacks(execute=True) as callbacks:
            with self.assertRaisesRegex(RuntimeError, "outbox insert failed"):
                _expire_pending_verification(self.verification.pk, timezone.now())

        self.verification.refresh_from_db()
        self.assertEqual(
            self.verification.status,
            VerificationStatus.PENDING_CONSENT,
        )
        self.assertIsNone(self.verification.completed_at)
        self.assertEqual(callbacks, [])
        mock_evidence_report.assert_not_called()

    @patch(
        "apps.verifications.evidence_commit.ensure_verification_evidence_report"
    )
    @patch("apps.verifications.tasks.queue_webhook_events")
    def test_evidence_is_generated_from_committed_expired_verification(
        self,
        mock_queue_webhooks,
        mock_evidence_report,
    ):
        with self.captureOnCommitCallbacks(execute=True) as callbacks:
            changed = _expire_pending_verification(
                self.verification.pk,
                timezone.now(),
            )

        self.assertTrue(changed)
        self.assertEqual(len(callbacks), 1)
        mock_queue_webhooks.assert_called_once()
        mock_evidence_report.assert_called_once()
        persisted_verification = mock_evidence_report.call_args.args[0]
        self.assertEqual(persisted_verification.pk, self.verification.pk)
        self.assertEqual(persisted_verification.status, VerificationStatus.EXPIRED)
        self.assertIsNotNone(persisted_verification.completed_at)
