from datetime import timedelta

from django.test import TestCase, TransactionTestCase, override_settings
from django.db import connection
from unittest import skipUnless
from django.urls import reverse
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.test import APIClient

from apps.accounts.models import PlatformUser
from apps.organizations.models import Organization
from apps.projects.models import Project
from apps.tenants.models import Tenant
from apps.verification_subjects.models import VerificationSubject
from apps.verifications.models import (
    Verification,
    VerificationSession,
    SandboxSimulation,
    VerificationDecision,
)
from apps.verifications.result_contract import serialize_verification_result
from apps.verifications.simulator import SCENARIOS, simulate_verification
from apps.webhooks.models import WebhookEndpoint, WebhookEvent


class SandboxSimulatorTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            name="Synthetic simulator", slug="synthetic-simulator"
        )
        self.tenant = Tenant.objects.create(
            organization=self.organization,
            name="Synthetic tenant",
            slug="synthetic-tenant",
            status="active",
        )
        self.user = PlatformUser.objects.create_user(
            email="simulator@example.test",
            password="StrongPassword123!",
            tenant=self.tenant,
            status="active",
        )
        self.sandbox = Project.objects.create(
            tenant=self.tenant,
            name="Sandbox scenarios",
            slug="sandbox-scenarios",
            environment="sandbox",
            created_by=self.user,
        )
        self.production = Project.objects.create(
            tenant=self.tenant,
            name="Production",
            slug="production",
            environment="production",
            created_by=self.user,
        )
        self.subject = VerificationSubject.objects.create(
            tenant=self.tenant, full_name="Synthetic Subject"
        )

    def case(self, **overrides):
        values = dict(
            tenant=self.tenant,
            organization=self.organization,
            project=self.sandbox,
            verification_subject=self.subject,
            purpose="Synthetic scenario",
            status="pending_consent",
            expires_at=timezone.now() + timedelta(hours=1),
        )
        values.update(overrides)
        return Verification.objects.create(**values)

    def endpoint(self, project):
        return WebhookEndpoint.objects.create(
            tenant=self.tenant,
            project=project,
            url="https://webhooks.example.test/events",
            secret_hash="synthetic-hash",
            created_by=self.user,
            events_json=[
                "verification.verified",
                "verification.rejected",
                "verification.manual_review_required",
                "verification.failed",
            ],
        )

    def test_all_scenarios_use_normal_result_and_provider_contracts(self):
        self.endpoint(self.sandbox)
        production_endpoint = self.endpoint(self.production)
        for scenario, (
            expected,
            reason,
            check_state,
            normalized,
            _,
        ) in SCENARIOS.items():
            with self.subTest(scenario=scenario):
                case = self.case()
                result = simulate_verification(case, scenario, actor=self.user)
                from apps.verifications.serializers import serialize_verification

                detail = serialize_verification(case)
                self.assertEqual(
                    detail["simulation"], {"scenario": scenario, "version": 1}
                )
                self.assertEqual(result["schema_version"], "1")
                self.assertEqual(result["status"], expected)
                self.assertEqual(result["decision"]["reason_codes"], [reason])
                self.assertEqual(
                    result["simulation"], {"scenario": scenario, "version": 1}
                )
                self.assertEqual(result["check_provenance"][0]["status"], normalized)
                case.refresh_from_db()
                check = case.provider_checks.get()
                self.assertEqual(check.status, check_state)
                self.assertEqual(check.duration_ms, 0)
                self.assertEqual(check.provider.code, "sandbox-simulator-v1")
                self.assertFalse(case.processing_jobs.exists())
                event = WebhookEvent.objects.order_by("-created_at").first()
                self.assertEqual(event.event_type, "verification." + expected)
                self.assertEqual(
                    event.payload_json["data"]["simulation"]["scenario"], scenario
                )
        self.assertFalse(
            WebhookEvent.objects.filter(webhook_endpoint=production_endpoint).exists()
        )
        self.assertEqual(WebhookEvent.objects.count(), 5)

    def test_replay_is_idempotent_and_different_scenario_conflicts(self):
        self.endpoint(self.sandbox)
        case = self.case()
        first = simulate_verification(case, "approved", actor=self.user)
        self.assertEqual(
            simulate_verification(case, "approved", actor=self.user), first
        )
        self.assertEqual(WebhookEvent.objects.count(), 1)
        self.assertEqual(VerificationDecision.objects.count(), 1)
        with self.assertRaises(ValidationError):
            simulate_verification(case, "declined", actor=self.user)

    @override_settings(DEBUG=True)
    def test_production_is_denied_even_with_debug_and_forged_metadata(self):
        case = self.case(
            project=self.production,
            metadata_json={
                "sandbox_scenario": "approved",
                "_sandbox_simulation": {"scenario": "approved"},
            },
        )
        with self.assertRaises(PermissionDenied):
            simulate_verification(case, "approved", actor=self.user)
        self.assertFalse(SandboxSimulation.objects.exists())
        self.assertNotIn("simulation", serialize_verification_result(case))

    def test_platform_owned_cases_and_non_pristine_cases_are_denied(self):
        with self.assertRaises(PermissionDenied):
            simulate_verification(
                self.case(review_owner="platform"), "approved", actor=self.user
            )
        for status in [
            "processing",
            "in_progress",
            "verified",
            "manual_review_required",
        ]:
            with self.subTest(status=status), self.assertRaises(ValidationError):
                simulate_verification(
                    self.case(status=status), "approved", actor=self.user
                )
        with self.assertRaises(ValidationError):
            simulate_verification(
                self.case(expires_at=timezone.now()), "approved", actor=self.user
            )

    def test_capture_sessions_are_closed_and_cannot_be_reissued(self):
        case = self.case()
        token = VerificationSession.generate_session_token()
        session = VerificationSession(
            verification=case, tenant=self.tenant, expires_at=case.expires_at
        )
        session.set_session_token(token, generated=True)
        session.save()
        simulate_verification(case, "review", actor=self.user)
        session.refresh_from_db()
        self.assertEqual(session.status, "revoked")
        client = APIClient()
        self.assertEqual(
            client.get(
                reverse(
                    "verification-session-detail",
                    kwargs={"session_id": session.public_id},
                ),
                HTTP_AUTHORIZATION="Bearer " + token,
            ).status_code,
            401,
        )
        client.force_authenticate(self.user)
        self.assertEqual(
            client.post(
                reverse(
                    "verification-resend-link",
                    kwargs={"verification_id": case.public_id},
                ),
                {"channel": "email"},
                format="json",
            ).status_code,
            400,
        )

    def test_inactive_workspace_and_unknown_scenario_fail_without_writes(self):
        case = self.case()
        with self.assertRaises(ValidationError):
            simulate_verification(case, "unknown", actor=self.user)
        self.tenant.status = "suspended"
        self.tenant.save(update_fields=["status"])
        with self.assertRaises(PermissionDenied):
            simulate_verification(case, "approved", actor=self.user)
        self.assertFalse(SandboxSimulation.objects.exists())

    def test_api_client_scope_and_environment_are_enforced(self):
        from apps.api_clients.models import APIClient as ClientCredential

        case = self.case()
        url = reverse(
            "verification-simulate", kwargs={"verification_id": case.public_id}
        )
        credential = ClientCredential(
            tenant=self.tenant,
            project=self.sandbox,
            name="Simulator credential",
            created_by=self.user,
            scopes_json=["verifications:read"],
        )
        credential.set_client_secret("synthetic-simulator-secret")
        credential.save()
        client = APIClient()
        headers = {
            "HTTP_X_CLIENT_ID": credential.client_id,
            "HTTP_AUTHORIZATION": "Bearer synthetic-simulator-secret",
        }
        self.assertEqual(
            client.post(
                url, {"scenario": "approved"}, format="json", **headers
            ).status_code,
            403,
        )
        credential.scopes_json = ["verifications:create"]
        credential.save(update_fields=["scopes_json"])
        response = client.post(url, {"scenario": "approved"}, format="json", **headers)
        self.assertEqual(response.status_code, 200, response.data)
        other = self.case()
        credential.project = self.production
        credential.save(update_fields=["project"])
        denied = client.post(
            reverse(
                "verification-simulate", kwargs={"verification_id": other.public_id}
            ),
            {"scenario": "approved"},
            format="json",
            **headers
        )
        self.assertIn(denied.status_code, [403, 404])
        self.assertFalse(SandboxSimulation.objects.filter(verification=other).exists())

    def test_api_requires_auth_and_tenant_ownership(self):
        case = self.case()
        url = reverse(
            "verification-simulate", kwargs={"verification_id": case.public_id}
        )
        client = APIClient()
        self.assertEqual(
            client.post(url, {"scenario": "approved"}, format="json").status_code, 401
        )
        other_org = Organization.objects.create(name="Other", slug="other")
        other_tenant = Tenant.objects.create(
            organization=other_org, name="Other", slug="other", status="active"
        )
        other = PlatformUser.objects.create_user(
            email="other@example.test",
            password="StrongPassword123!",
            tenant=other_tenant,
            status="active",
        )
        client.force_authenticate(other)
        self.assertEqual(
            client.post(url, {"scenario": "approved"}, format="json").status_code, 404
        )
        client.force_authenticate(self.user)
        response = client.post(url, {"scenario": "approved"}, format="json")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["data"]["status"], "verified")


class SandboxSimulatorRaceTests(TransactionTestCase):
    setUp = SandboxSimulatorTests.setUp
    case = SandboxSimulatorTests.case
    endpoint = SandboxSimulatorTests.endpoint

    @skipUnless(connection.vendor == "postgresql", "Requires PostgreSQL row locks")
    def test_concurrent_same_scenario_commits_one_result_and_one_event(self):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier
        from django.db import close_old_connections

        case = self.case()
        self.endpoint(self.sandbox)
        ready = Barrier(2)

        def simulate(_):
            close_old_connections()
            try:
                current = Verification.objects.get(pk=case.pk)
                actor = PlatformUser.objects.get(pk=self.user.pk)
                ready.wait(timeout=15)
                return simulate_verification(current, "approved", actor=actor)
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(simulate, range(2)))
        self.assertEqual(results[0], results[1])
        self.assertEqual(SandboxSimulation.objects.count(), 1)
        self.assertEqual(VerificationDecision.objects.count(), 1)
        self.assertEqual(case.provider_checks.count(), 1)
        self.assertEqual(WebhookEvent.objects.count(), 1)
