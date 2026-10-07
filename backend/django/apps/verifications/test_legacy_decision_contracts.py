from importlib import import_module

from django.apps import apps
from django.test import TestCase
from django.utils import timezone

from apps.organizations.models import Organization
from apps.tenants.models import Tenant
from apps.verifications.models import Verification, VerificationDecision


class LegacyDecisionContractRepairTests(TestCase):
    def test_repair_preserves_payloads_and_complete_contracts_and_is_idempotent(self):
        organization = Organization.objects.create(name="Fixture", slug="fixture")
        tenant = Tenant.objects.create(
            organization=organization, name="Fixture", slug="fixture"
        )
        cases = (
            ({}, [], "1", "legacy"),
            ({}, ["historical_result"], "1", "legacy"),
            ({"status": "verified"}, [], "1", "legacy"),
            ({"status": "verified"}, ["historical_result"], "1", "1"),
            ({}, ["historical_result"], "legacy", "legacy"),
        )
        decisions = []
        for snapshot, reasons, version, expected in cases:
            verification = Verification.objects.create(
                tenant=tenant,
                organization=organization,
                verification_subject=tenant.verification_subjects.create(
                    full_name="Fixture"
                ),
                purpose="Migration fixture",
                expires_at=timezone.now(),
                status="verified",
            )
            decision = VerificationDecision.objects.create(
                tenant=tenant,
                verification=verification,
                decision="verified",
                decision_type="automatic",
                reason_code="historical_result",
                contract_version=version,
                reason_codes_json=reasons,
                input_snapshot_json=snapshot,
                decided_at=timezone.now(),
            )
            decisions.append((decision, snapshot, reasons, expected))
        migration = import_module(
            "apps.verifications.migrations.0024_repair_incomplete_decision_contracts"
        )
        for _ in range(2):
            migration.repair_incomplete_decision_contracts(apps, None)
            for decision, snapshot, reasons, expected in decisions:
                with self.subTest(decision=decision.pk, iteration=_):
                    decision.refresh_from_db()
                    self.assertEqual(decision.contract_version, expected)
                    self.assertEqual(decision.input_snapshot_json, snapshot)
                    self.assertEqual(decision.reason_codes_json, reasons)
