from datetime import timedelta
from unittest.mock import patch

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import PlatformUser, PlatformUserStatus
from apps.audit.models import AuditEvent
from apps.organizations.models import Organization
from apps.tenants.models import Tenant
from apps.verifications.models import Verification, VerificationStatus
from apps.verification_subjects.models import VerificationSubject
from apps.webhooks.models import WebhookDeliveryAttempt, WebhookEndpoint, WebhookEvent, WebhookEventStatus
from apps.webhooks.services import _build_signature, deliver_webhook_event, process_pending_webhook_events


class WebhookEndpointTests(APITestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name="Acme", slug="acme")
        self.tenant = Tenant.objects.create(
            organization=self.organization,
            name="Acme Tenant",
            slug="acme-tenant",
            status="active",
        )
        self.user = PlatformUser.objects.create_user(
            email="owner@example.com",
            password="StrongPassword123!",
            status=PlatformUserStatus.ACTIVE,
            tenant=self.tenant,
        )
        self.client.force_authenticate(self.user)

    def test_create_webhook_endpoint_returns_secret_once(self):
        response = self.client.post(
            reverse("webhook-endpoint-list-create"),
            {
                "url": "https://example.com/webhooks/identitycore",
                "events": ["verification.verified", "verification.rejected"],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        endpoint = WebhookEndpoint.objects.get(public_id=response.data["data"]["id"])
        self.assertEqual(endpoint.status, "active")
        self.assertTrue(response.data["data"]["secret"])
        self.assertTrue(
            AuditEvent.objects.filter(
                tenant=self.tenant,
                action="webhook_endpoint.created",
                target_id=endpoint.public_id,
            ).exists()
        )

    def test_list_webhook_endpoints_is_tenant_scoped(self):
        WebhookEndpoint.objects.create(
            tenant=self.tenant,
            url="https://example.com/webhooks/identitycore",
            events_json=["verification.verified"],
            created_by=self.user,
            secret_hash="placeholder",
        )
        other_org = Organization.objects.create(name="Beta", slug="beta")
        other_tenant = Tenant.objects.create(
            organization=other_org,
            name="Beta Tenant",
            slug="beta-tenant",
            status="active",
        )
        other_user = PlatformUser.objects.create_user(
            email="other@example.com",
            password="StrongPassword123!",
            status=PlatformUserStatus.ACTIVE,
            tenant=other_tenant,
        )
        WebhookEndpoint.objects.create(
            tenant=other_tenant,
            url="https://beta.example.com/webhooks/identitycore",
            events_json=["verification.rejected"],
            created_by=other_user,
            secret_hash="placeholder",
        )

        response = self.client.get(reverse("webhook-endpoint-list-create"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["data"]["results"]), 1)

    def test_test_webhook_queues_webhook_event(self):
        endpoint = WebhookEndpoint(
            tenant=self.tenant,
            url="https://example.com/webhooks/identitycore",
            events_json=["verification.verified"],
            created_by=self.user,
        )
        endpoint.set_secret("secret")
        endpoint.save()

        response = self.client.post(
            reverse("webhook-endpoint-test", kwargs={"webhook_id": endpoint.public_id}),
            {},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["data"]["queued"])
        self.assertTrue(
            WebhookEvent.objects.filter(
                tenant=self.tenant,
                webhook_endpoint=endpoint,
                event_type="webhook.test",
            ).exists()
        )

    def test_verification_created_queues_matching_webhook_event(self):
        endpoint = WebhookEndpoint(
            tenant=self.tenant,
            url="https://example.com/webhooks/identitycore",
            events_json=["verification.created"],
            created_by=self.user,
        )
        endpoint.set_secret("secret")
        endpoint.save()

        api_client_user = PlatformUser.objects.create_user(
            email="api@example.com",
            password="StrongPassword123!",
            status=PlatformUserStatus.ACTIVE,
            tenant=self.tenant,
        )
        from apps.api_clients.models import APIClient

        api_client = APIClient(
            tenant=self.tenant,
            created_by=api_client_user,
            name="Backend",
            scopes_json=["verifications:create"],
        )
        api_client.set_client_secret("client-secret")
        api_client.save()
        self.client.force_authenticate(user=None)

        response = self.client.post(
            "/api/v1/verifications/",
            {
                "external_reference": "customer_12345",
                "purpose": "Customer onboarding verification",
                "verification_subject": {"full_name": "Kwame Mensah"},
            },
            format="json",
            HTTP_X_CLIENT_ID=api_client.client_id,
            HTTP_AUTHORIZATION="Bearer client-secret",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            WebhookEvent.objects.filter(
                tenant=self.tenant,
                webhook_endpoint=endpoint,
                event_type="verification.created",
            ).exists()
        )

    def test_manual_decision_queues_verification_result_webhook(self):
        endpoint = WebhookEndpoint(
            tenant=self.tenant,
            url="https://example.com/webhooks/identitycore",
            events_json=["verification.verified"],
            created_by=self.user,
        )
        endpoint.set_secret("secret")
        endpoint.save()
        verification = Verification.objects.create(
            tenant=self.tenant,
            organization=self.organization,
            verification_subject=VerificationSubject.objects.create(tenant=self.tenant, full_name="Case"),
            purpose="Manual review case",
            expires_at=self.tenant.created_at,
            status=VerificationStatus.MANUAL_REVIEW_REQUIRED,
        )

        response = self.client.post(
            reverse("manual-review-decision", kwargs={"verification_id": verification.public_id}),
            {
                "decision": "verified",
                "reason_code": "evidence_confirmed",
                "reason_detail": "Document and selfie match after manual review.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            WebhookEvent.objects.filter(
                tenant=self.tenant,
                webhook_endpoint=endpoint,
                event_type="verification.verified",
            ).exists()
        )

    @patch("apps.webhooks.services._send_webhook_request")
    def test_deliver_webhook_event_marks_event_delivered_and_logs_attempt(self, mock_send_request):
        mock_send_request.return_value = (202, '{"received":true}', 42)
        endpoint = WebhookEndpoint(
            tenant=self.tenant,
            url="https://example.com/webhooks/identitycore",
            events_json=["verification.verified"],
            created_by=self.user,
        )
        endpoint.set_secret("secret")
        endpoint.save()
        webhook_event = WebhookEvent.objects.create(
            tenant=self.tenant,
            webhook_endpoint=endpoint,
            event_type="verification.verified",
            payload_json={"id": "evt_1", "type": "verification.verified", "data": {"status": "verified"}},
        )

        deliver_webhook_event(webhook_event)

        webhook_event.refresh_from_db()
        self.assertEqual(webhook_event.status, WebhookEventStatus.DELIVERED)
        self.assertEqual(webhook_event.attempt_count, 1)
        attempt = WebhookDeliveryAttempt.objects.get(webhook_event=webhook_event)
        self.assertEqual(attempt.status_code, 202)
        self.assertEqual(attempt.duration_ms, 42)
        self.assertTrue(
            AuditEvent.objects.filter(
                tenant=self.tenant,
                action="webhook.delivered",
                target_id=webhook_event.public_id,
            ).exists()
        )

    @patch("apps.webhooks.services._send_webhook_request")
    def test_failed_delivery_schedules_retry(self, mock_send_request):
        mock_send_request.return_value = (500, "server error", 15)
        endpoint = WebhookEndpoint(
            tenant=self.tenant,
            url="https://example.com/webhooks/identitycore",
            events_json=["verification.verified"],
            created_by=self.user,
        )
        endpoint.set_secret("secret")
        endpoint.save()
        webhook_event = WebhookEvent.objects.create(
            tenant=self.tenant,
            webhook_endpoint=endpoint,
            event_type="verification.verified",
            payload_json={"id": "evt_1", "type": "verification.verified", "data": {"status": "verified"}},
        )

        deliver_webhook_event(webhook_event)

        webhook_event.refresh_from_db()
        self.assertEqual(webhook_event.status, WebhookEventStatus.PENDING)
        self.assertEqual(webhook_event.attempt_count, 1)
        self.assertIsNotNone(webhook_event.next_retry_at)
        attempt = WebhookDeliveryAttempt.objects.get(webhook_event=webhook_event)
        self.assertEqual(attempt.status_code, 500)

    @patch("apps.webhooks.services._send_webhook_request")
    def test_failed_delivery_hits_max_attempts(self, mock_send_request):
        mock_send_request.return_value = (500, "server error", 15)
        endpoint = WebhookEndpoint(
            tenant=self.tenant,
            url="https://example.com/webhooks/identitycore",
            events_json=["verification.verified"],
            created_by=self.user,
        )
        endpoint.set_secret("secret")
        endpoint.save()
        webhook_event = WebhookEvent.objects.create(
            tenant=self.tenant,
            webhook_endpoint=endpoint,
            event_type="verification.verified",
            payload_json={"id": "evt_1", "type": "verification.verified", "data": {"status": "verified"}},
        )

        with self.settings(WEBHOOK_MAX_ATTEMPTS=2):
            deliver_webhook_event(webhook_event)
            webhook_event.refresh_from_db()
            webhook_event.next_retry_at = timezone.now()
            webhook_event.save(update_fields=["next_retry_at", "updated_at"])
            deliver_webhook_event(webhook_event)

        webhook_event.refresh_from_db()
        self.assertEqual(webhook_event.status, WebhookEventStatus.FAILED)
        self.assertEqual(webhook_event.attempt_count, 2)
        self.assertEqual(WebhookDeliveryAttempt.objects.filter(webhook_event=webhook_event).count(), 2)
        self.assertTrue(
            AuditEvent.objects.filter(
                tenant=self.tenant,
                action="webhook.delivery_failed",
                target_id=webhook_event.public_id,
            ).exists()
        )

    def test_disabled_endpoint_cancels_delivery(self):
        endpoint = WebhookEndpoint(
            tenant=self.tenant,
            url="https://example.com/webhooks/identitycore",
            events_json=["verification.verified"],
            created_by=self.user,
            status="disabled",
        )
        endpoint.set_secret("secret")
        endpoint.save()
        webhook_event = WebhookEvent.objects.create(
            tenant=self.tenant,
            webhook_endpoint=endpoint,
            event_type="verification.verified",
            payload_json={"id": "evt_1", "type": "verification.verified", "data": {"status": "verified"}},
        )

        deliver_webhook_event(webhook_event)

        webhook_event.refresh_from_db()
        self.assertEqual(webhook_event.status, WebhookEventStatus.CANCELLED)
        self.assertEqual(webhook_event.attempt_count, 0)

    @patch("apps.webhooks.services._send_webhook_request")
    def test_process_pending_webhook_events_only_processes_due_events(self, mock_send_request):
        mock_send_request.return_value = (200, "ok", 10)
        endpoint = WebhookEndpoint(
            tenant=self.tenant,
            url="https://example.com/webhooks/identitycore",
            events_json=["verification.verified"],
            created_by=self.user,
        )
        endpoint.set_secret("secret")
        endpoint.save()
        due_event = WebhookEvent.objects.create(
            tenant=self.tenant,
            webhook_endpoint=endpoint,
            event_type="verification.verified",
            payload_json={"id": "evt_due", "type": "verification.verified", "data": {"status": "verified"}},
            next_retry_at=timezone.now(),
        )
        future_event = WebhookEvent.objects.create(
            tenant=self.tenant,
            webhook_endpoint=endpoint,
            event_type="verification.verified",
            payload_json={"id": "evt_future", "type": "verification.verified", "data": {"status": "verified"}},
            next_retry_at=timezone.now() + timedelta(hours=1),
        )

        processed = process_pending_webhook_events(limit=10)

        self.assertEqual(processed, 1)
        due_event.refresh_from_db()
        future_event.refresh_from_db()
        self.assertEqual(due_event.status, WebhookEventStatus.DELIVERED)
        self.assertEqual(future_event.status, WebhookEventStatus.PENDING)

    def test_signature_format_uses_endpoint_signing_key(self):
        endpoint = WebhookEndpoint(
            tenant=self.tenant,
            url="https://example.com/webhooks/identitycore",
            events_json=["verification.verified"],
            created_by=self.user,
        )
        endpoint.set_secret("secret")

        signature = _build_signature(endpoint.signing_key, "1720180800", b'{"id":"evt_1"}')

        self.assertTrue(signature.startswith("sha256="))
