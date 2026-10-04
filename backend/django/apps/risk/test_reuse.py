from copy import deepcopy
from datetime import timedelta

from django.test import TestCase, override_settings
from django.utils import timezone

from apps.biometrics.models import SelfieCapture
from apps.identity_documents.models import IdentityDocument
from apps.organizations.models import Organization
from apps.risk import tests as risk_tests
from apps.risk.models import ReuseFingerprint
from apps.risk.reuse import collect_reuse, validate_rules
from apps.risk.tasks import cleanup_reuse_fingerprints_task
from apps.tenants.models import Tenant
from apps.verification_subjects.models import VerificationSubject
from apps.verification_subjects.services import request_subject_deletion
from apps.verifications.models import Verification, VerificationSession

RULES = {
    "version": 1,
    "scope": "tenant",
    "retention_days": 7,
    "window_minutes": 60,
    "thresholds": {"document": 2, "portrait": 2, "device": 2, "network": 2},
    "action": "manual_review",
}


class ReuseSignalTests(TestCase):
    setUp = risk_tests.RiskDecisionTests.setUp

    def _case(self, tenant=None, scope="tenant", threshold=2):
        tenant = tenant or self.tenant
        subject = VerificationSubject.objects.create(
            tenant=tenant, full_name="Synthetic subject"
        )
        rules = deepcopy(RULES)
        rules["scope"] = scope
        rules["thresholds"] = {kind: threshold for kind in rules["thresholds"]}
        case = Verification.objects.create(
            tenant=tenant,
            organization=tenant.organization,
            verification_subject=subject,
            purpose="Synthetic reuse check",
            expires_at=timezone.now() + timedelta(hours=1),
            policy_snapshot_json={"reuse_rules": rules, "metadata_retention_days": 7},
        )
        IdentityDocument.objects.create(
            tenant=tenant,
            verification=case,
            verification_subject=subject,
            document_type_id="national_id",
            country_profile_id="GH",
            extracted_data_json={"document_number": "AB-12345"},
        )
        SelfieCapture.objects.create(
            tenant=tenant,
            verification=case,
            verification_subject=subject,
            storage_key="synthetic-portrait",
            capture_type="image",
            captured_at=timezone.now(),
            checksum_sha256="d" * 64,
        )
        session = VerificationSession(
            tenant=tenant,
            verification=case,
            expires_at=case.expires_at,
            device_fingerprint="synthetic-device",
            ip_address="203.0.113.29",
        )
        session.set_session_token(
            VerificationSession.generate_session_token(), generated=True
        )
        session.save()
        return case

    def _foreign(self):
        organization = Organization.objects.create(name="Foreign", slug="foreign")
        return Tenant.objects.create(
            organization=organization, name="Foreign", slug="foreign", status="active"
        )

    def test_default_is_disabled_and_persists_no_fingerprints(self):
        self.assertEqual(collect_reuse(self.verification)["status"], "disabled")
        self.assertFalse(ReuseFingerprint.objects.exists())

    def test_thresholds_flag_all_four_kinds_without_raw_identifiers(self):
        first, second = self._case(), self._case()
        self.assertEqual(collect_reuse(first)["signals"], [])
        evidence = collect_reuse(second)
        self.assertEqual(
            evidence["signals"],
            ["device_velocity", "document_reuse", "network_velocity", "portrait_reuse"],
        )
        self.assertEqual(evidence["recommended_action"], "manual_review")
        for secret in [
            "AB-12345",
            "synthetic-device",
            "203.0.113",
            "d" * 64,
            first.public_id,
        ]:
            self.assertNotIn(secret, str(evidence))
        rows = ReuseFingerprint.objects.filter(verification=second)
        self.assertEqual(rows.count(), 4)
        self.assertTrue(
            all(
                len(row.tenant_digest) == 64 and row.global_digest == "" for row in rows
            )
        )

    def test_case_retries_do_not_count_twice_or_extend_expiry(self):
        case = self._case()
        collect_reuse(case)
        expiry = list(
            ReuseFingerprint.objects.filter(verification=case).values_list(
                "expires_at", flat=True
            )
        )
        for _ in range(3):
            self.assertEqual(collect_reuse(case)["signals"], [])
        self.assertEqual(ReuseFingerprint.objects.filter(verification=case).count(), 4)
        self.assertEqual(
            expiry,
            list(
                ReuseFingerprint.objects.filter(verification=case).values_list(
                    "expires_at", flat=True
                )
            ),
        )

    def test_tenant_scope_does_not_correlate_foreign_cases(self):
        first, second = self._case(), self._case(self._foreign())
        collect_reuse(first)
        self.assertEqual(collect_reuse(second)["signals"], [])
        self.assertNotEqual(
            ReuseFingerprint.objects.filter(verification=first, kind="document")
            .get()
            .tenant_digest,
            ReuseFingerprint.objects.filter(verification=second, kind="document")
            .get()
            .tenant_digest,
        )

    @override_settings(GLOBAL_REUSE_SIGNALS_ENABLED=True)
    def test_global_scope_counts_only_mutually_opted_in_cases(self):
        first = self._case(scope="global", threshold=3)
        private = self._case(self._foreign(), threshold=3)
        second = self._case(private.tenant, scope="global", threshold=3)
        collect_reuse(first)
        collect_reuse(private)
        self.assertEqual(collect_reuse(second)["signals"], [])
        third = self._case(scope="global", threshold=3)
        evidence = collect_reuse(third)
        self.assertEqual(len(evidence["signals"]), 4)
        self.assertNotIn("counts", evidence)
        self.assertFalse(
            ReuseFingerprint.objects.filter(verification=private)
            .exclude(global_digest="")
            .exists()
        )

    def test_global_scope_is_unavailable_without_operator_enablement(self):
        case = self._case(scope="global")
        self.assertEqual(collect_reuse(case)["status"], "global_disabled")
        self.assertFalse(ReuseFingerprint.objects.exists())

    def test_velocity_window_excludes_old_cases_but_document_reuse_remains(self):
        old = self._case()
        old.created_at = timezone.now() - timedelta(hours=2)
        Verification.objects.filter(pk=old.pk).update(created_at=old.created_at)
        collect_reuse(old)
        evidence = collect_reuse(self._case())
        self.assertEqual(evidence["signals"], ["document_reuse", "portrait_reuse"])

    def test_expired_fingerprints_cannot_be_reintroduced_by_reevaluation(self):
        old = self._case()
        old.created_at = timezone.now() - timedelta(days=8)
        Verification.objects.filter(pk=old.pk).update(created_at=old.created_at)
        self.assertEqual(collect_reuse(old)["signals"], [])
        self.assertFalse(ReuseFingerprint.objects.exists())

    def test_expiry_cleanup_is_bounded(self):
        case = self._case()
        collect_reuse(case)
        ReuseFingerprint.objects.update(
            expires_at=timezone.now() - timedelta(seconds=1)
        )
        from unittest.mock import patch

        with patch(
            "apps.risk.tasks.cleanup_reuse_fingerprints_task.apply_async"
        ) as followup:
            self.assertEqual(cleanup_reuse_fingerprints_task(limit=2), 2)
            self.assertEqual(ReuseFingerprint.objects.count(), 2)
            followup.assert_called_once_with(
                kwargs={"limit": 2}, countdown=1, queue="retention"
            )
            self.assertEqual(cleanup_reuse_fingerprints_task(limit=2), 2)
            self.assertEqual(ReuseFingerprint.objects.count(), 0)
            self.assertEqual(followup.call_count, 1)

    def test_subject_erasure_removes_fingerprints_and_prevents_recreation(self):
        case = self._case()
        collect_reuse(case)
        report = request_subject_deletion(subject=case.verification_subject)
        self.assertEqual(report["status"], "completed")
        case.refresh_from_db()
        self.assertFalse(ReuseFingerprint.objects.exists())
        self.assertEqual(collect_reuse(case)["status"], "erased")
        self.assertFalse(ReuseFingerprint.objects.exists())

    def test_configuration_rejects_unsafe_limits_and_unknown_inputs(self):
        for field, value in [
            ("scope", "all"),
            ("retention_days", 0),
            ("retention_days", True),
            ("window_minutes", 20000),
            ("thresholds", {"document": 1}),
            ("thresholds", {"unknown": 2}),
            ("action", "reject"),
        ]:
            rules = deepcopy(RULES)
            rules[field] = value
            with self.assertRaises(ValueError):
                validate_rules(rules)
        self.verification.policy_snapshot_json = {"reuse_rules": {"bad": True}}
        self.assertEqual(
            collect_reuse(self.verification)["recommended_action"], "manual_review"
        )

    def test_matching_never_crosses_sandbox_and_production(self):
        from apps.accounts.models import PlatformUser
        from apps.projects.models import Project

        user = PlatformUser.objects.create_user(
            email="environment@example.test",
            password="SyntheticPassword123!",
            tenant=self.tenant,
        )
        project = Project.objects.create(
            tenant=self.tenant,
            name="Production",
            slug="production",
            environment="production",
            created_by=user,
        )
        first, second = self._case(), self._case()
        second.project = project
        second.save(update_fields=["project"])
        collect_reuse(first)
        self.assertEqual(collect_reuse(second)["signals"], [])

    def test_cached_subject_cannot_recreate_indexes_after_erasure(self):
        case = self._case()
        stale = Verification.objects.select_related("verification_subject").get(
            pk=case.pk
        )
        request_subject_deletion(subject=case.verification_subject)
        self.assertIsNone(stale.verification_subject.deleted_at)
        self.assertEqual(collect_reuse(stale)["status"], "erased")
        self.assertFalse(ReuseFingerprint.objects.exists())
