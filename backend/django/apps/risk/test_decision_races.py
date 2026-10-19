from apps.access_control.test_helpers import grant_review_permission
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Event
from unittest import skipUnless

from django.db import connection, close_old_connections, transaction
from django.test import TransactionTestCase
from django.utils import timezone
from apps.accounts.models import PlatformUser
from apps.audit.models import AuditEvent
from apps.organizations.models import Organization
from apps.tenants.models import Tenant
from apps.verification_subjects.models import VerificationSubject
from apps.verifications.models import Verification, VerificationDecision
from apps.verifications.serializers import ManualReviewDecisionSerializer
from apps.risk.models import RiskAssessment
from apps.risk.services import apply_automatic_decision


@skipUnless(connection.vendor == "postgresql", "Decision races require real row locks")
class DecisionRaceTests(TransactionTestCase):
    def setUp(self):
        organization = Organization.objects.create(
            name="Synthetic", slug="decision-race"
        )
        self.tenant = Tenant.objects.create(
            organization=organization, name="Synthetic", slug="decision-race", status="active"
        )
        self.reviewer = PlatformUser.objects.create_user(
            email="synthetic-reviewer@example.invalid",
            password="SyntheticRace123!",
            tenant=self.tenant,
            status="active",
        )
        grant_review_permission(self.reviewer)
        subject = VerificationSubject.objects.create(tenant=self.tenant)
        self.verification = Verification.objects.create(
            tenant=self.tenant,
            organization=organization,
            verification_subject=subject,
            status="manual_review_required",
            expires_at=timezone.now() + timedelta(hours=1),
        )
        self.routing = VerificationDecision.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            decision="manual_review_required",
            decision_type="automatic",
            reason_code="risk_rules_manual_review",
            decided_at=timezone.now(),
            input_snapshot_json={"synthetic_automatic_evidence": True},
        )
        self.risk = RiskAssessment.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            risk_score=68,
            risk_level="medium",
            recommendation="approve",
        )

    def _race_review_against_late_worker(self, maker_checker):
        self.verification.policy_snapshot_json = {
            "maker_checker_required": maker_checker
        }
        self.verification.save(update_fields=["policy_snapshot_json"])
        stale = Verification.objects.get(pk=self.verification.pk)
        review_written, worker_started, commit_review = Event(), Event(), Event()

        def review():
            close_old_connections()
            try:
                with transaction.atomic():
                    serializer = ManualReviewDecisionSerializer(
                        data={
                            "decision": "rejected",
                            "reason_code": "synthetic_review_decline",
                            "reason_detail": "Synthetic reviewed evidence",
                        }
                    )
                    serializer.is_valid(raise_exception=True)
                    serializer.save(
                        verification=Verification.objects.get(pk=stale.pk),
                        decided_by=PlatformUser.objects.get(pk=self.reviewer.pk),
                    )
                    review_written.set()
                    if not commit_review.wait(10):
                        raise RuntimeError("Race synchronization timed out")
            finally:
                close_old_connections()

        def worker():
            close_old_connections()
            try:
                if not review_written.wait(10):
                    raise RuntimeError("Reviewer did not write")
                worker_started.set()
                return apply_automatic_decision(
                    stale, RiskAssessment.objects.get(pk=self.risk.pk)
                )
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            review_future = pool.submit(review)
            worker_future = pool.submit(worker)
            self.assertTrue(worker_started.wait(10))
            commit_review.set()
            review_future.result(timeout=10)
            result = worker_future.result(timeout=10)
        decision = VerificationDecision.objects.get(pk=self.routing.pk)
        self.verification.refresh_from_db()
        self.assertEqual(decision.decision_type, "manual")
        self.assertEqual(decision.decided_by_id, self.reviewer.pk)
        self.assertEqual(decision.reason_code, "synthetic_review_decline")
        self.assertEqual(decision.decision, "rejected")
        self.assertEqual(result.pk, decision.pk)
        self.assertEqual(self.verification.decision_revision, 1)
        self.assertEqual(
            self.verification.status,
            "manual_review_required" if maker_checker else "rejected",
        )
        self.assertEqual(
            decision.approval_status, "pending" if maker_checker else "not_required"
        )
        self.assertEqual(
            decision.evidence_summary_json["automatic_review"]["input_snapshot"],
            {"synthetic_automatic_evidence": True},
        )
        self.assertEqual(
            AuditEvent.objects.filter(
                action="verification.automatic_decision_conflict"
            ).count(),
            1,
        )

    def test_late_worker_preserves_committed_human_terminal_decision(self):
        self._race_review_against_late_worker(False)

    def test_late_worker_preserves_pending_human_proposal(self):
        self._race_review_against_late_worker(True)

    def test_system_review_route_can_be_consumed_by_human(self):
        self.routing.decision_type = "system"
        self.routing.save(update_fields=["decision_type"])
        self._race_review_against_late_worker(False)

    def test_provider_exhaustion_preserves_pending_human_decision(self):
        from apps.consent.test_helpers import accept_test_consent
        accept_test_consent(self.verification)
        from apps.providers.services import _apply_route_final_action

        self.verification.policy_snapshot_json = {"maker_checker_required": True}
        self.verification.save(update_fields=["policy_snapshot_json"])
        serializer = ManualReviewDecisionSerializer(
            data={"decision": "rejected", "reason_code": "synthetic_review_decline"}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(verification=self.verification, decided_by=self.reviewer)
        result = _apply_route_final_action(
            verification=self.verification,
            route=None,
            check_type="face_match",
            attempts=[],
        )
        self.routing.refresh_from_db()
        self.assertEqual(result, "manual_review")
        self.assertEqual(self.routing.decision_type, "manual")
        self.assertEqual(self.routing.approval_status, "pending")
        self.assertEqual(self.routing.reason_code, "synthetic_review_decline")


@skipUnless(connection.vendor == "postgresql", "Audit races require real row locks")
class AuditChainRaceTests(TransactionTestCase):
    def test_concurrent_appends_preserve_one_tenant_chain(self):
        from threading import Barrier
        from apps.audit.services import record_audit_event, verify_audit_chain

        organization = Organization.objects.create(
            name="Synthetic audit", slug="audit-race"
        )
        tenant = Tenant.objects.create(
            organization=organization, name="Synthetic audit", slug="audit-race"
        )
        start = Barrier(8)

        def append(number):
            close_old_connections()
            try:
                start.wait(timeout=10)
                for offset in range(10):
                    record_audit_event(
                        tenant_id=tenant.pk,
                        action="synthetic.race",
                        target_type="synthetic",
                        target_id=str(number),
                        metadata={"offset": offset},
                    )
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=8) as pool:
            list(pool.map(append, range(8)))
        self.assertEqual(AuditEvent.objects.filter(tenant=tenant).count(), 80)
        self.assertEqual(verify_audit_chain(tenant_id=tenant.pk), (True, ""))
