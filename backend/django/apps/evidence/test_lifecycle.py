from datetime import timedelta
from unittest.mock import patch

from django.db import transaction
from django.test import TestCase
from rest_framework.exceptions import NotFound, PermissionDenied

from apps.claims import tests as claim_fixtures
from apps.evidence.lifecycle import (
    create_legal_hold,
    release_legal_hold,
    retire_expired_resources,
)
from apps.evidence.models import ResourceMaintenanceState, SubjectResourceRestriction
from apps.evidence.services import (
    approve_authorization,
    revoke_authorization,
    revoke_evidence,
)
from apps.evidence.tasks import retire_governed_resources_task
from apps.verification_subjects.services import request_subject_deletion


class GovernedLifecycleTests(TestCase):
    propose = claim_fixtures.ClaimsTests.propose
    create_evidence = claim_fixtures.ClaimsTests.create_evidence
    claim = claim_fixtures.ClaimsTests.claim
    normalized = claim_fixtures.ClaimsTests.normalized
    policy = claim_fixtures.ClaimsTests.policy
    issue = claim_fixtures.ClaimsTests.issue
    redeem = claim_fixtures.ClaimsTests.redeem
    read = claim_fixtures.ClaimsTests.read

    def setUp(self):
        claim_fixtures.ClaimsTests.setUp(self)

    def hold(self):
        return create_legal_hold(
            tenant_id=self.tenant.pk,
            actor=self.checker,
            project_id=self.project.public_id,
            subject_id=self.subject.public_id,
            reason={"case": "synthetic preservation request"},
        )

    def test_evidence_revocation_updates_claims_and_descendants_and_denies_disclosure(
        self,
    ):
        claim = self.normalized()
        disclosure, token = self.issue(claim, self.policy())
        revoke_evidence(
            tenant_id=self.tenant.pk,
            actor=self.maker,
            project_id=self.project.public_id,
            evidence_id=self.evidence.public_id,
            purpose="eligibility",
            reason="source_withdrawn",
        )
        claim.refresh_from_db()
        self.assertEqual(claim.status, "revoked")
        with self.assertRaises(PermissionDenied):
            self.redeem(disclosure, token)

    def test_source_grant_revoked_after_proposal_prevents_reuse_approval(self):
        target = self.propose(
            purpose="secondary",
            operations=["claims:write", "claims:read"],
            reuse_from_ids=[self.authorization.public_id],
        )
        revoke_authorization(
            tenant_id=self.tenant.pk,
            actor=self.maker,
            authorization_id=self.authorization.public_id,
            reason="source_ended",
        )
        with self.assertRaises(PermissionDenied):
            approve_authorization(
                tenant_id=self.tenant.pk,
                actor=self.checker,
                authorization_id=target.public_id,
            )
        target.refresh_from_db()
        self.assertIsNone(target.approved_at)

    def test_claim_only_grant_can_authorize_explicit_secondary_reuse(self):
        source = self.propose(operations=["claims:read", "claims:write"])
        approve_authorization(
            tenant_id=self.tenant.pk,
            actor=self.checker,
            authorization_id=source.public_id,
        )
        target = self.propose(
            purpose="secondary",
            operations=["claims:write", "claims:read"],
            reuse_from_ids=[source.public_id],
        )
        approve_authorization(
            tenant_id=self.tenant.pk,
            actor=self.checker,
            authorization_id=target.public_id,
        )
        target.refresh_from_db()
        self.assertIsNotNone(target.approved_at)

    def test_hold_preserves_content_but_deletion_request_stops_all_resource_use(self):
        claim = self.normalized()
        disclosure, token = self.issue(claim, self.policy())
        hold = self.hold()
        report = request_subject_deletion(subject=self.subject, actor=self.checker)
        self.assertEqual(report["status"], "deferred")
        self.evidence.refresh_from_db()
        claim.refresh_from_db()
        self.assertEqual(self.evidence.payload_json["name"], "Synthetic applicant")
        self.assertEqual(claim.value_json["name"], "Synthetic applicant")
        self.assertEqual(claim.status, "revoked")
        self.assertTrue(
            SubjectResourceRestriction.objects.filter(subject=self.subject).exists()
        )
        with self.assertRaises((PermissionDenied, NotFound)):
            self.redeem(disclosure, token)
        with self.assertRaises(NotFound):
            self.propose()
        release_legal_hold(
            tenant_id=self.tenant.pk, actor=self.checker, hold_id=hold.public_id
        )
        report = request_subject_deletion(subject=self.subject, actor=self.checker)
        self.assertEqual(report["status"], "completed")
        for record in (self.evidence, claim):
            record.refresh_from_db()
            self.assertEqual(record.status, "deleted")
        self.assertEqual(self.evidence.payload_json, {})
        self.assertEqual(self.evidence.provenance_json, {})
        self.assertEqual(claim.value_json, {})
        self.assertEqual(claim.rule_parameters_json, {})
        self.claim_auth.refresh_from_db()
        self.assertEqual(self.claim_auth.justification_json, {})

    def test_retention_preserves_held_records_then_scrubs_after_release(self):
        claim = self.normalized()
        hold = self.hold()
        future = self.now + timedelta(days=3)
        with patch("apps.evidence.lifecycle.timezone.now", return_value=future):
            result = retire_expired_resources(tenant_id=self.tenant.pk, limit=100)
        self.assertEqual(sum(result.values()), 0)
        self.evidence.refresh_from_db()
        self.assertIsNone(self.evidence.deleted_at)
        release_legal_hold(
            tenant_id=self.tenant.pk, actor=self.checker, hold_id=hold.public_id
        )
        with patch("apps.evidence.lifecycle.timezone.now", return_value=future):
            result = retire_expired_resources(tenant_id=self.tenant.pk, limit=100)
        self.assertEqual(result["evidence"], 1)
        self.assertEqual(result["claims"], 1)
        self.evidence.refresh_from_db()
        claim.refresh_from_db()
        self.assertEqual(self.evidence.payload_json, {})
        self.assertEqual(claim.value_json, {})

    def test_retention_limit_applies_across_classes_by_deadline(self):
        claim = self.normalized(delete_after=self.now + timedelta(hours=2))
        with patch(
            "apps.evidence.lifecycle.timezone.now",
            return_value=self.now + timedelta(days=3),
        ):
            result = retire_expired_resources(tenant_id=self.tenant.pk, limit=1)
        self.assertEqual(result["claims"], 1)
        self.assertEqual(
            sum(value for key, value in result.items() if key != "held"), 1
        )
        claim.refresh_from_db()
        self.evidence.refresh_from_db()
        self.assertEqual(claim.value_json, {})
        self.assertIsNone(self.evidence.deleted_at)

    def test_scheduler_persists_sanitized_failure_and_continues_on_next_run(self):
        with patch(
            "apps.evidence.tasks.timezone.now",
            return_value=self.now + timedelta(days=3),
        ):
            with patch(
                "apps.evidence.tasks.retire_expired_resources",
                side_effect=ValueError("subject data must not persist"),
            ):
                result = retire_governed_resources_task(limit=1, tenant_limit=1)
            self.assertEqual(result["failed"], 1)
            state = ResourceMaintenanceState.objects.get(tenant=self.tenant)
            self.assertEqual(state.last_error_code, "ValueError")
            result = retire_governed_resources_task(limit=1, tenant_limit=1)
        self.assertEqual(result["failed"], 0)
        self.assertEqual(result["retired"], 1)
        state.refresh_from_db()
        self.assertEqual(state.last_error_code, "")

    def test_internal_scrubbing_rechecks_hold_before_erasing(self):
        from apps.evidence.lifecycle import scrub_subject_resources

        self.hold()
        from rest_framework.exceptions import ValidationError

        with transaction.atomic(), self.assertRaises(ValidationError):
            scrub_subject_resources(self.subject, actor=self.checker)
