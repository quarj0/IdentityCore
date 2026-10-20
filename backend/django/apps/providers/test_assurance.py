from copy import deepcopy
from datetime import timedelta
from unittest.mock import patch

from django.db import connection
from django.test import TestCase
from django.utils import timezone
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.test import APIClient

from apps.access_control.models import Permission, Role, RolePermission
from apps.providers import assurance, test_configuration as fixtures
from apps.providers.models import ProviderCertification


class ProviderAssuranceTests(TestCase):
    create = fixtures.ConfigurationTests.create
    connection_checked = fixtures.ConfigurationTests.connection_checked
    sandbox = fixtures.ConfigurationTests.sandbox

    def setUp(self):
        fixtures.ConfigurationTests.setUp(self)
        for user in (self.requester, self.approver):
            user.status = "active"
            user.save(update_fields=["status"])
        self.config = self.sandbox()
        role = Role.objects.get(tenant=self.tenant, name="Provider manager")
        for code in ("manage_provider_assurance", "approve_provider_assurance"):
            permission, _ = Permission.objects.get_or_create(
                code=code, defaults={"name": code}
            )
            RolePermission.objects.create(role=role, permission=permission)

    def report(self, **overrides):
        return {
            **assurance.report_scope(self.config, "document_ocr"),
            "cases": {case: "passed" for case in assurance.SYNC_CASES},
            "artifact_sha256": "0" * 64,
            "assurance_references": [
                "Synthetic independent review reference; not real certification"
            ],
            **overrides,
        }

    def propose(self, **overrides):
        return assurance.propose_certification(
            **{
                "tenant_id": self.tenant.pk,
                "actor": self.requester,
                "configuration_id": self.config.public_id,
                "capability": "document_ocr",
                "report": self.report(),
                "assurance_level": "assured",
                "valid_until": timezone.now() + timedelta(days=30),
                "delete_after": timezone.now() + timedelta(days=60),
                **overrides,
            }
        )

    def approve(self, record, **overrides):
        return assurance.approve_certification(
            **{
                "tenant_id": self.tenant.pk,
                "actor": self.approver,
                "certification_id": record.public_id,
                **overrides,
            }
        )

    def test_report_is_encrypted_and_independent_approval_is_required_for_readiness(
        self,
    ):
        record = self.propose()
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT report_json FROM providers_providercertification WHERE id=%s",
                [record.pk],
            )
            self.assertNotIn("Synthetic independent review", str(cursor.fetchone()))
        with self.assertRaises(PermissionDenied):
            assurance.require_certification(self.config, "document_ocr")
        with self.assertRaises(PermissionDenied):
            self.approve(record, actor=self.requester)
        self.approve(record)
        self.assertEqual(
            assurance.require_certification(
                self.config, "document_ocr", minimum_level="assured"
            ).pk,
            record.pk,
        )
        self.assertNotIn("report", assurance.summary(record))

    def test_route_assignment_requires_current_approved_assurance_at_required_level(
        self,
    ):
        from apps.providers.configuration import assign_configuration
        from apps.providers.models import ProviderRoute

        self.public = {**self.public, "required_assurance": "assured"}
        self.config = self.sandbox()

        def assign():
            return assign_configuration(
                config=self.config,
                user=self.requester,
                capability="document_ocr",
                countries=["GH"],
                document_types=["passport"],
            )

        with self.assertRaises(PermissionDenied):
            assign()
        pending = self.propose()
        with self.assertRaises(PermissionDenied):
            assign()
        conformance = self.approve(self.propose(assurance_level="conformance"))
        with self.assertRaises(PermissionDenied):
            assign()
        self.assertFalse(ProviderRoute.objects.filter(tenant=self.tenant).exists())
        self.approve(pending)
        route = assign()
        self.assertEqual(route.status, "active")
        assurance.revoke_certification(
            tenant_id=self.tenant.pk,
            actor=self.approver,
            certification_id=pending.public_id,
            reason="synthetic_revocation",
        )
        with self.assertRaises(PermissionDenied):
            assign()
        self.assertEqual(ProviderRoute.objects.filter(tenant=self.tenant).count(), 1)
        self.assertIsNotNone(conformance.approved_at)

    def test_scope_and_all_required_cases_cannot_be_forged_or_omitted(self):
        for overrides in (
            {"environment": "production"},
            {"configuration_digest": "f" * 64},
            {"manifest_sha256": "f" * 64},
            {"contract_version": "2"},
            {"cases": {"success": "passed"}},
            {"assurance_references": []},
        ):
            with self.subTest(overrides=overrides), self.assertRaises(ValidationError):
                self.propose(report=self.report(**overrides))
        self.assertFalse(ProviderCertification.objects.exists())

    def test_configuration_or_manifest_changes_expiry_and_revocation_invalidate_readiness(
        self,
    ):
        record = self.approve(self.propose())
        with patch(
            "apps.providers.assurance.timezone.now", return_value=record.valid_until
        ):
            with self.assertRaises(PermissionDenied):
                assurance.require_certification(self.config, "document_ocr")
        changed = deepcopy(self.provider.manifest_json)
        changed["transfer_notes"] = "Changed processing conditions require a new review"
        self.provider.manifest_json = changed
        self.provider.save()
        self.config.refresh_from_db()
        with self.assertRaises(PermissionDenied):
            assurance.require_certification(self.config, "document_ocr")
        self.provider.manifest_json = self.config.manifest_snapshot_json
        self.provider.save()
        self.config.refresh_from_db()
        assurance.revoke_certification(
            tenant_id=self.tenant.pk,
            actor=self.approver,
            certification_id=record.public_id,
            reason="assurance_withdrawn",
        )
        with self.assertRaises(PermissionDenied):
            assurance.require_certification(self.config, "document_ocr")

    def test_conformance_does_not_implicitly_satisfy_independent_assurance(self):
        self.approve(self.propose(assurance_level="conformance"))
        assurance.require_certification(self.config, "document_ocr")
        with self.assertRaises(PermissionDenied):
            assurance.require_certification(
                self.config, "document_ocr", minimum_level="assured"
            )

    def test_current_permissions_are_checked_for_approval_and_http_replay(self):
        record = self.propose()
        client = APIClient()
        client.force_authenticate(self.approver)
        path = f"/api/v1/providers/certifications/{record.public_id}/approve"
        response = client.post(
            path, {}, format="json", HTTP_IDEMPOTENCY_KEY="assurance-approve"
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.approver.status = "inactive"
        self.approver.save(update_fields=["status"])
        response = client.post(
            path, {}, format="json", HTTP_IDEMPOTENCY_KEY="assurance-approve"
        )
        self.assertEqual(response.status_code, 403, response.data)

    def test_foreign_and_unknown_receipts_fail_with_identical_unavailability(self):
        with self.assertRaises(NotFound):
            self.approve(type("Receipt", (), {"public_id": "pct_unknown"})())
        self.requester.status = "inactive"
        self.requester.save(update_fields=["status"])
        with self.assertRaises(PermissionDenied):
            self.propose()
