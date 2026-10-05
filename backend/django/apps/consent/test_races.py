from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Event
from unittest import skipUnless
from unittest.mock import patch

from django.db import close_old_connections, connection
from django.test import TransactionTestCase
from django.utils import timezone

from apps.audit.services import lock_audit_chain, record_audit_event, verify_audit_chain
from apps.biometrics.models import LivenessCheck, SelfieCapture
from apps.biometrics.tasks import _finalize_unavailable_biometrics
from apps.consent.services import withdraw
from apps.consent.test_helpers import accept_test_consent
from apps.organizations.models import Organization
from apps.tenants.models import Tenant
from apps.verification_subjects.models import VerificationSubject
from apps.verifications.models import ProcessingJob, Verification


@skipUnless(connection.vendor == "postgresql", "Consent races require real row locks")
class ConsentWithdrawalRaceTests(TransactionTestCase):
    def test_withdrawal_and_biometric_finalization_do_not_invert_audit_locks(self):
        organization = Organization.objects.create(
            name="Synthetic", slug="consent-race"
        )
        tenant = Tenant.objects.create(
            organization=organization,
            name="Synthetic",
            slug="consent-race",
            status="active",
        )
        subject = VerificationSubject.objects.create(tenant=tenant)
        case = Verification.objects.create(
            tenant=tenant,
            organization=organization,
            verification_subject=subject,
            status="processing",
            purpose="Synthetic race",
            expires_at=timezone.now() + timedelta(hours=1),
        )
        record = accept_test_consent(case)
        capture = SelfieCapture.objects.create(
            tenant=tenant,
            verification=case,
            verification_subject=subject,
            storage_key="synthetic/race",
            captured_at=timezone.now(),
        )
        liveness = LivenessCheck.objects.create(
            tenant=tenant,
            verification=case,
            selfie_capture=capture,
            checked_at=timezone.now(),
        )
        job = ProcessingJob.objects.create(
            tenant=tenant,
            verification=case,
            job_type="biometrics",
            resource_public_id=liveness.public_id,
            status="processing",
            attempt_count=1,
            lease_expires_at=timezone.now() + timedelta(minutes=5),
        )
        before_audit = Event()
        withdrawal_attempted = Event()
        withdrawal_locked_audit = Event()

        def finalizer_audit(**kwargs):
            before_audit.set()
            if not withdrawal_attempted.wait(5):
                raise AssertionError("Withdrawal did not reach the audit lock")
            # With the old ordering withdrawal acquires audit while the finalizer
            # holds the case, reproducing the PostgreSQL deadlock cycle.
            withdrawal_locked_audit.wait(0.2)
            return record_audit_event(**kwargs)

        def withdrawal_audit(tenant_id):
            withdrawal_attempted.set()
            lock_audit_chain(tenant_id)
            withdrawal_locked_audit.set()

        def finalize():
            close_old_connections()
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SET statement_timeout = '5s'")
                return _finalize_unavailable_biometrics(
                    verification=case,
                    liveness_check=liveness,
                    face_match=None,
                    processing_job=job,
                    error=RuntimeError("Synthetic outage"),
                )
            finally:
                close_old_connections()

        def revoke():
            close_old_connections()
            try:
                if not before_audit.wait(5):
                    raise AssertionError("Finalization did not reach audit append")
                with connection.cursor() as cursor:
                    cursor.execute("SET statement_timeout = '5s'")
                return withdraw(record)
            finally:
                close_old_connections()

        with patch(
            "apps.biometrics.tasks.record_audit_event", side_effect=finalizer_audit
        ), patch(
            "apps.consent.services.lock_audit_chain", side_effect=withdrawal_audit
        ), patch("apps.biometrics.tasks.queue_webhook_events"), patch(
            "apps.biometrics.tasks.queue_verification_status_notifications"
        ), patch("apps.biometrics.tasks._schedule_evidence_report_after_commit"):
            with ThreadPoolExecutor(max_workers=2) as pool:
                finalized = pool.submit(finalize)
                revoked = pool.submit(revoke)
                finalized.result(timeout=15)
                revoked.result(timeout=15)
        case.refresh_from_db()
        record.refresh_from_db()
        self.assertEqual(case.status, "cancelled")
        self.assertIsNotNone(record.withdrawn_at)
        self.assertEqual(verify_audit_chain(tenant_id=tenant.pk), (True, ""))
