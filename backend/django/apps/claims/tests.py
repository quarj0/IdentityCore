from datetime import timedelta
from unittest.mock import patch

from django.db import connection
from django.test import TestCase
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from apps.access_control.models import Permission, Role, RolePermission
from apps.api_clients.models import APIClient
from apps.audit.services import verify_audit_chain
from apps.claims.disclosure import (
    approve_policy,
    evaluate_claim,
    issue_disclosure,
    propose_policy,
    redeem_disclosure,
)
from apps.claims.models import Claim, ClaimDisclosure
from apps.claims.services import create_claim, read_claim, resolve_conflict
from apps.evidence.services import (
    approve_authorization,
    create_schema,
    revoke_authorization,
)
from apps.evidence.tests import EvidenceServiceTests


class ClaimsTests(TestCase):
    propose = EvidenceServiceTests.propose
    create_evidence = EvidenceServiceTests.create

    def setUp(self):
        EvidenceServiceTests.setUp(self)
        role = Role.objects.get(tenant=self.tenant, name="Evidence officer")
        for code in (
            "read_claims",
            "manage_claims",
            "disclose_claims",
            "review_verification",
        ):
            permission, _ = Permission.objects.get_or_create(
                code=code, defaults={"name": code}
            )
            RolePermission.objects.get_or_create(role=role, permission=permission)
        self.claim_auth = self.propose(
            operations=[
                "evidence:read",
                "evidence:write",
                "claims:read",
                "claims:write",
                "claims:disclose",
            ]
        )
        approve_authorization(
            tenant_id=self.tenant.pk,
            actor=self.checker,
            authorization_id=self.claim_auth.public_id,
        )
        self.claim_schema = create_schema(
            tenant_id=self.tenant.pk,
            actor=self.maker,
            name="name-claim",
            version=1,
            kind="claim",
            definition={
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"],
                "additionalProperties": False,
            },
            disclosure_fields=["name"],
        )
        self.evidence = self.create_evidence()
        self.audience = APIClient(
            tenant=self.tenant,
            project=self.project,
            name="Recipient",
            created_by=self.maker,
            scopes_json=["claims:read"],
        )
        self.audience.set_client_secret("synthetic-recipient-secret")
        self.audience.save()

    def claim(self, **overrides):
        return create_claim(
            **{
                **dict(
                    tenant_id=self.tenant.pk,
                    actor=self.maker,
                    project_id=self.project.public_id,
                    subject_id=self.subject.public_id,
                    authorization_id=self.claim_auth.public_id,
                    schema_id=self.claim_schema.public_id,
                    observed_at=self.now,
                    valid_from=self.now,
                    valid_until=self.now + timedelta(hours=1),
                    delete_after=self.now + timedelta(days=2),
                    evidence_ids=[self.evidence.public_id],
                    value={"name": "Synthetic applicant"},
                ),
                **overrides,
            }
        )

    def normalized(self, **overrides):
        return self.claim(
            value=None,
            rule_name="field",
            rule_parameters={"field": "name", "output_field": "name"},
            **overrides,
        )

    def read(self, record, **overrides):
        return read_claim(
            **{
                **dict(
                    tenant_id=self.tenant.pk,
                    actor=self.maker,
                    project_id=self.project.public_id,
                    claim_id=record.public_id,
                    purpose="eligibility",
                    include_value=True,
                ),
                **overrides,
            }
        )

    def policy(self, **overrides):
        policy = propose_policy(
            **{
                **dict(
                    tenant_id=self.tenant.pk,
                    actor=self.maker,
                    project_id=self.project.public_id,
                    schema_id=self.claim_schema.public_id,
                    name="name-disclosure",
                    version=1,
                    purposes=["eligibility"],
                    accepted_classes=["normalized"],
                    fields=["name"],
                    max_age_seconds=3600,
                ),
                **overrides,
            }
        )
        return approve_policy(
            tenant_id=self.tenant.pk,
            actor=self.checker,
            project_id=self.project.public_id,
            policy_id=policy.public_id,
        )

    def issue(self, claim, policy, **overrides):
        return issue_disclosure(
            **{
                **dict(
                    tenant_id=self.tenant.pk,
                    actor=self.maker,
                    project_id=self.project.public_id,
                    authorization_id=self.claim_auth.public_id,
                    audience_id=self.audience.public_id,
                    selections=[
                        {
                            "claim_id": claim.public_id,
                            "policy_id": policy.public_id,
                            "fields": ["name"],
                        }
                    ],
                ),
                **overrides,
            }
        )

    def redeem(self, disclosure, token, **overrides):
        return redeem_disclosure(
            **{
                **dict(
                    tenant_id=self.tenant.pk,
                    actor=self.audience,
                    project_id=self.project.public_id,
                    disclosure_id=disclosure.public_id,
                    token=token,
                    request_key="first-redemption",
                ),
                **overrides,
            }
        )

    def test_claim_values_are_encrypted_and_default_metadata_omits_values(self):
        claim = self.claim()
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT value_json FROM claims_claim WHERE id=%s", [claim.pk]
            )
            self.assertNotIn("Synthetic applicant", str(cursor.fetchone()))
        self.assertNotIn("value", self.read(claim, include_value=False))
        self.assertEqual(self.read(claim)["value"], {"name": "Synthetic applicant"})
        self.assertTrue(verify_audit_chain(tenant_id=self.tenant.pk)[0])

    def test_conflicts_do_not_choose_highest_confidence_and_need_an_independent_reviewer(
        self,
    ):
        first = self.claim(value={"name": "First"}, confidence="0.10")
        second = self.claim(value={"name": "Second"}, confidence="0.99")
        self.assertEqual(self.read(first)["status"], "disputed")
        self.assertEqual(self.read(second)["status"], "disputed")
        args = dict(
            tenant_id=self.tenant.pk,
            project_id=self.project.public_id,
            claim_id=first.public_id,
            purpose="eligibility",
            selected_claim_id=first.public_id,
            outcome="selected",
            reason={"basis": "independent synthetic review"},
        )
        with self.assertRaises(PermissionDenied):
            resolve_conflict(actor=self.maker, **args)
        resolve_conflict(actor=self.checker, **args)
        self.assertEqual(self.read(first)["status"], "active")
        self.assertEqual(self.read(first)["claim_class"], "reviewed")
        self.assertEqual(self.read(second)["status"], "disputed")

    def test_new_conflict_invalidates_resolution_and_prevents_laundering_through_derivation(
        self,
    ):
        first = self.claim(value={"name": "First"})
        self.claim(value={"name": "Second"})
        resolve_conflict(
            tenant_id=self.tenant.pk,
            actor=self.checker,
            project_id=self.project.public_id,
            claim_id=first.public_id,
            purpose="eligibility",
            selected_claim_id=first.public_id,
            outcome="selected",
            reason={"basis": "review"},
        )
        other_schema = create_schema(
            tenant_id=self.tenant.pk,
            actor=self.maker,
            name="derived-name",
            version=1,
            kind="claim",
            definition={
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"],
            },
            disclosure_fields=["name"],
        )
        child = self.claim(
            schema_id=other_schema.public_id,
            evidence_ids=[],
            claim_ids=[first.public_id],
            value=None,
            rule_name="copy",
        )
        self.assertEqual(self.read(child)["status"], "active")
        self.claim(value={"name": "Third"})
        self.assertEqual(self.read(first)["status"], "disputed")
        self.assertEqual(self.read(child)["status"], "disputed")
        with self.assertRaises(PermissionDenied):
            self.claim(
                schema_id=other_schema.public_id,
                evidence_ids=[],
                claim_ids=[first.public_id],
                value=None,
                rule_name="copy",
            )

    def test_a_single_candidate_can_be_independently_reviewed(self):
        claim = self.claim()
        resolve_conflict(
            tenant_id=self.tenant.pk,
            actor=self.checker,
            project_id=self.project.public_id,
            claim_id=claim.public_id,
            purpose="eligibility",
            selected_claim_id=claim.public_id,
            outcome="selected",
            reason={"basis": "reviewed evidence"},
        )
        self.assertEqual(self.read(claim)["claim_class"], "reviewed")

    def test_cross_purpose_reuse_requires_explicit_source_grant_and_current_approval(
        self,
    ):
        no_reuse = self.propose(
            purpose="second-workload", operations=["claims:read", "claims:write"]
        )
        approve_authorization(
            tenant_id=self.tenant.pk,
            actor=self.checker,
            authorization_id=no_reuse.public_id,
        )
        with self.assertRaises(PermissionDenied):
            self.claim(authorization_id=no_reuse.public_id)
        allowed = self.propose(
            purpose="second-workload",
            operations=["claims:read", "claims:write"],
            reuse_from_ids=[self.authorization.public_id],
        )
        with self.assertRaises(PermissionDenied):
            self.claim(authorization_id=allowed.public_id)
        approve_authorization(
            tenant_id=self.tenant.pk,
            actor=self.checker,
            authorization_id=allowed.public_id,
        )
        claim = self.claim(authorization_id=allowed.public_id)
        self.assertEqual(
            self.read(claim, purpose="second-workload")["value"]["name"],
            "Synthetic applicant",
        )
        revoke_authorization(
            tenant_id=self.tenant.pk,
            actor=self.maker,
            authorization_id=self.authorization.public_id,
            reason="source_withdrawn",
        )
        with self.assertRaises(PermissionDenied):
            self.read(claim, purpose="second-workload")

    def test_automatic_corroboration_rejects_unverified_duplicate_caller_roots(self):
        second = self.create_evidence()
        with self.assertRaises(ValidationError):
            self.claim(
                evidence_ids=[self.evidence.public_id, second.public_id],
                value=None,
                rule_name="exact_corroboration",
            )
        self.assertFalse(Claim.objects.exists())

    def test_policy_approval_is_independent_and_candidate_is_not_implicitly_verified(
        self,
    ):
        candidate = self.claim()
        policy = self.policy()
        result = evaluate_claim(
            tenant_id=self.tenant.pk,
            actor=self.maker,
            project_id=self.project.public_id,
            claim_id=candidate.public_id,
            purpose="eligibility",
            policy_id=policy.public_id,
        )
        self.assertFalse(result["satisfied"])
        self.assertIn("claim_class_not_accepted", result["reason_codes"])
        with self.assertRaises(PermissionDenied):
            self.issue(candidate, policy)

    def test_disclosure_is_bound_to_authenticated_audience_and_contains_only_selected_fields(
        self,
    ):
        claim = self.normalized()
        disclosure, token = self.issue(claim, self.policy())
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT token_sha256, selections_json FROM claims_claimdisclosure WHERE id=%s",
                [disclosure.pk],
            )
            self.assertNotIn(token, str(cursor.fetchone()))
        with self.assertRaises(PermissionDenied):
            self.redeem(disclosure, token, actor=self.maker)
        other = APIClient(
            tenant=self.tenant,
            project=self.project,
            name="Different audience",
            created_by=self.maker,
            scopes_json=["claims:read"],
        )
        other.set_client_secret("synthetic-other-recipient")
        other.save()
        with self.assertRaises(NotFound):
            self.redeem(disclosure, token, actor=other)
        with self.assertRaises(NotFound):
            self.redeem(disclosure, token + "x")
        payload = self.redeem(disclosure, token)
        self.assertEqual(payload["claims"][0]["value"], {"name": "Synthetic applicant"})
        self.assertNotIn("provenance", payload["claims"][0])
        self.assertTrue(verify_audit_chain(tenant_id=self.tenant.pk)[0])

    def test_redemption_is_idempotent_but_each_replay_rechecks_source_authorization(
        self,
    ):
        disclosure, token = self.issue(self.normalized(), self.policy())
        first = self.redeem(disclosure, token)
        second = self.redeem(disclosure, token)
        self.assertEqual(first, second)
        disclosure.refresh_from_db()
        self.assertEqual(disclosure.redemption_count, 1)
        self.assertEqual(disclosure.redemptions.count(), 1)
        with self.assertRaises(PermissionDenied):
            self.redeem(disclosure, token, request_key="second-distinct-redemption")
        revoke_authorization(
            tenant_id=self.tenant.pk,
            actor=self.maker,
            authorization_id=self.authorization.public_id,
            reason="evidence_use_ended",
        )
        with self.assertRaises(PermissionDenied):
            self.redeem(disclosure, token)

    def test_short_lived_disclosure_cannot_be_redeemed_after_expiry(self):
        disclosure, token = self.issue(
            self.normalized(), self.policy(), lifetime_seconds=10
        )
        with patch(
            "apps.claims.disclosure.timezone.now",
            return_value=self.now + timedelta(seconds=20),
        ):
            with self.assertRaises(PermissionDenied):
                self.redeem(disclosure, token)

    def test_copying_old_evidence_does_not_refresh_its_age(self):
        old = self.create_evidence(observed_at=self.now - timedelta(minutes=5))
        claim = self.normalized(evidence_ids=[old.public_id])
        policy = self.policy(max_age_seconds=30)
        result = evaluate_claim(
            tenant_id=self.tenant.pk,
            actor=self.maker,
            project_id=self.project.public_id,
            claim_id=claim.public_id,
            purpose="eligibility",
            policy_id=policy.public_id,
        )
        self.assertFalse(result["satisfied"])
        self.assertIn("source_not_fresh", result["reason_codes"])
        with self.assertRaises(PermissionDenied):
            self.issue(claim, policy)

    def test_selective_disclosure_rejects_fields_outside_the_approved_policy(self):
        claim = self.normalized()
        policy = self.policy()
        with self.assertRaises(PermissionDenied):
            self.issue(
                claim,
                policy,
                selections=[
                    {
                        "claim_id": claim.public_id,
                        "policy_id": policy.public_id,
                        "fields": ["date_of_birth"],
                    }
                ],
            )
        self.assertFalse(ClaimDisclosure.objects.exists())
