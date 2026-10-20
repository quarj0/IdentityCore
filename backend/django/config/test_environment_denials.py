from datetime import timedelta
from unittest.mock import patch

from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITransactionTestCase

from apps.accounts.models import PlatformUser
from apps.api_clients.models import APIClient
from apps.audit.models import AuditEvent
from apps.audit.services import verify_audit_chain
from apps.organizations.models import Organization
from apps.projects.models import Project
from apps.tenants.models import Tenant
from apps.verification_policies.models import VerificationPolicy
from apps.verification_subjects.models import VerificationSubject
from apps.verifications.models import Verification


class EnvironmentDenialAuditTests(APITransactionTestCase):
    def setUp(self):
        org = Organization.objects.create(
            name="Synthetic", slug="denial", status="active"
        )
        self.tenant = Tenant.objects.create(
            organization=org, name="Synthetic", slug="denial", status="active"
        )
        user = PlatformUser.objects.create_user(
            email="denial@example.test",
            password="synthetic-password",
            tenant=self.tenant,
            status="active",
        )
        project = Project.objects.create(
            tenant=self.tenant,
            name="Production",
            slug="production",
            environment="production",
            created_by=user,
        )
        self.policy = VerificationPolicy.objects.create(
            tenant=self.tenant,
            project=project,
            name="Private production policy",
            status="active",
            created_by=user,
        )
        subject = VerificationSubject.objects.create(tenant=self.tenant)
        self.case = Verification.objects.create(
            tenant=self.tenant,
            organization=org,
            project=project,
            verification_subject=subject,
            purpose="Synthetic",
            expires_at=timezone.now() + timedelta(hours=1),
            status="pending_consent",
        )
        self.api_client = APIClient(
            tenant=self.tenant,
            name="Sandbox",
            scopes_json=["policies:read", "verifications:read", "verifications:create"],
            created_by=user,
        )
        self.api_client.set_client_secret("synthetic-denial-secret")
        self.api_client.save()
        self.client.credentials(
            HTTP_X_CLIENT_ID=self.api_client.client_id,
            HTTP_AUTHORIZATION="Bearer synthetic-denial-secret",
        )

    def _assert_denied(self, name, method, identifier, key, payload=None):
        before = AuditEvent.objects.filter(action="environment_scope.denied").count()
        response = getattr(self.client, method)(
            reverse(name, kwargs={key: identifier}), payload or {}, format="json"
        )
        missing = getattr(self.client, method)(
            reverse(name, kwargs={key: "missing"}), payload or {}, format="json"
        )
        self.assertEqual(response.status_code, 404, response.data)
        self.assertEqual(response.data["error"], missing.data["error"])
        events = AuditEvent.objects.filter(action="environment_scope.denied")
        self.assertEqual(events.count(), before + 1)
        event = events.latest("created_at")
        self.assertEqual(event.tenant_id, self.tenant.pk)
        self.assertEqual(event.actor_id, self.api_client.public_id)
        self.assertEqual(event.target_id, identifier)
        self.assertEqual(
            event.metadata_json,
            {"reason": "environment_mismatch", "method": method.upper()},
        )
        self.assertEqual(verify_audit_chain(tenant_id=self.tenant.pk), (True, ""))

    def test_policy_and_all_verification_environment_filtered_routes_are_audited(self):
        self._assert_denied(
            "verification-policy-detail", "get", self.policy.public_id, "policy_id"
        )
        routes = [
            ("verification-detail", "get", {}),
            ("verification-result", "get", {}),
            ("verification-evidence-report", "get", {}),
            ("verification-evidence-report-download", "get", {}),
            ("verification-evidence-report-pdf-download", "get", {}),
            ("verification-cancel", "post", {}),
            ("verification-resend-link", "post", {"channel": "email"}),
            ("verification-simulate", "post", {"scenario": "approved"}),
        ]
        with patch(
            "apps.verifications.views.ensure_verification_evidence_report"
        ) as report:
            for name, method, payload in routes:
                with self.subTest(route=name):
                    self._assert_denied(
                        name, method, self.case.public_id, "verification_id", payload
                    )
            report.assert_not_called()
        self.case.refresh_from_db()
        self.assertEqual(self.case.status, "pending_consent")

    def test_foreign_tenant_and_unknown_ids_do_not_create_environment_events(self):
        org = Organization.objects.create(
            name="Foreign", slug="foreign-denial", status="active"
        )
        foreign = Tenant.objects.create(
            organization=org, name="Foreign", slug="foreign-denial", status="active"
        )
        self.policy.tenant = foreign
        self.policy.save(update_fields=["tenant"])
        response = self.client.get(
            reverse(
                "verification-policy-detail",
                kwargs={"policy_id": self.policy.public_id},
            )
        )
        missing = self.client.get(
            reverse("verification-policy-detail", kwargs={"policy_id": "missing"})
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["error"], missing.data["error"])
        self.assertFalse(
            AuditEvent.objects.filter(action="environment_scope.denied").exists()
        )

    def test_matching_environment_read_and_list_do_not_emit_denials(self):
        self.api_client.project = self.case.project
        self.api_client.save(update_fields=["project"])
        response = self.client.get(
            reverse(
                "verification-detail", kwargs={"verification_id": self.case.public_id}
            )
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(
            self.client.get(reverse("verification-list-create")).status_code, 200
        )
        self.assertFalse(
            AuditEvent.objects.filter(action="environment_scope.denied").exists()
        )
