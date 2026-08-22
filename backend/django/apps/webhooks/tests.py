from datetime import timedelta
import hashlib
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from django.db import transaction
from django.test import TransactionTestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import PlatformUser, PlatformUserStatus
from apps.audit.models import AuditEvent
from apps.organizations.models import Organization
from apps.tenants.models import Tenant
from apps.verification_policies.models import VerificationPolicy
from apps.verifications.models import Verification, VerificationStatus
from apps.verification_subjects.models import VerificationSubject
from apps.webhooks.models import WebhookDeliveryAttempt, WebhookEndpoint, WebhookEvent, WebhookEventStatus
from apps.webhooks.services import (
    _build_legacy_signature,
    _build_signature,
    _send_webhook_request,
    deliver_webhook_event,
    process_pending_webhook_events,
    queue_webhook_events,
)


class WebhookEndpointTests(APITestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name="Acme", slug="acme", status="active")
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
        self.policy = VerificationPolicy.objects.create(
            tenant=self.tenant,
            name="Default Verification",
            version=1,
            status="active",
            required_document_types_json=["national_id"],
            required_liveness_level="passive",
            face_match_threshold="0.8500",
            manual_review_threshold="0.6500",
            verification_expiry_minutes=1440,
            media_retention_days=30,
            metadata_retention_days=365,
            created_by=self.user,
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
            HTTP_IDEMPOTENCY_KEY="create-primary-webhook",
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

    def test_create_webhook_endpoint_requires_idempotency_key(self):
        response = self.client.post(
            reverse("webhook-endpoint-list-create"),
            {
                "url": "https://example.com/missing-key",
                "events": ["verification.verified"],
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("idempotency_key", response.data["error"]["details"])

    def test_create_webhook_endpoint_replays_original_secret(self):
        payload = {
            "url": "https://example.com/replay",
            "events": ["verification.verified"],
        }
        url = reverse("webhook-endpoint-list-create")
        first = self.client.post(
            url,
            payload,
            format="json",
            HTTP_IDEMPOTENCY_KEY="replay-webhook",
        )
        replay = self.client.post(
            url,
            payload,
            format="json",
            HTTP_IDEMPOTENCY_KEY="replay-webhook",
        )

        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertEqual(replay.status_code, status.HTTP_201_CREATED)
        self.assertEqual(first.data["data"], replay.data["data"])
        self.assertEqual(WebhookEndpoint.objects.filter(url=payload["url"]).count(), 1)

    def test_create_webhook_endpoint_rejects_mismatched_replay(self):
        url = reverse("webhook-endpoint-list-create")
        self.client.post(
            url,
            {
                "url": "https://example.com/original",
                "events": ["verification.verified"],
            },
            format="json",
            HTTP_IDEMPOTENCY_KEY="conflicting-webhook",
        )
        conflict = self.client.post(
            url,
            {
                "url": "https://example.com/changed",
                "events": ["verification.verified"],
            },
            format="json",
            HTTP_IDEMPOTENCY_KEY="conflicting-webhook",
        )

        self.assertEqual(conflict.status_code, status.HTTP_409_CONFLICT)
        self.assertFalse(
            WebhookEndpoint.objects.filter(url="https://example.com/changed").exists()
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

    def test_patch_does_not_overwrite_a_completed_secret_rotation(self):
        endpoint = WebhookEndpoint(
            tenant=self.tenant,
            url="https://example.com/webhooks/original",
            events_json=["verification.verified"],
            created_by=self.user,
        )
        endpoint.set_secret("old-secret")
        endpoint.save()
        stale_endpoint = WebhookEndpoint.objects.get(pk=endpoint.pk)
        rotated_endpoint = WebhookEndpoint.objects.get(pk=endpoint.pk)
        rotated_endpoint.rotate_secret(
            "new-secret",
            previous_secret_expires_at=timezone.now() + timedelta(minutes=5),
        )
        rotated_endpoint.save(
            update_fields=[
                "secret_hash",
                "signing_key",
                "previous_signing_key",
                "signing_secret_version",
                "previous_secret_expires_at",
                "updated_at",
            ]
        )

        with patch(
            "apps.webhooks.views.WebhookEndpointDetailView.obj",
            return_value=stale_endpoint,
        ):
            response = self.client.patch(
                f"/api/v1/webhook-endpoints/{endpoint.public_id}",
                {"url": "https://example.com/webhooks/updated"},
                format="json",
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        endpoint.refresh_from_db()
        self.assertEqual(endpoint.url, "https://example.com/webhooks/updated")
        self.assertEqual(endpoint.signing_secret_version, 2)
        self.assertEqual(
            endpoint.signing_key, hashlib.sha256(b"new-secret").hexdigest()
        )
        self.assertEqual(
            endpoint.previous_signing_key,
            hashlib.sha256(b"old-secret").hexdigest(),
        )

    def test_rotate_signing_secret_returns_new_secret_and_bounded_overlap(self):
        endpoint = WebhookEndpoint(
            tenant=self.tenant,
            url="https://example.com/webhooks/identitycore",
            events_json=["verification.verified"],
            created_by=self.user,
        )
        endpoint.set_secret("old-secret")
        endpoint.save()

        with (
            self.settings(WEBHOOK_SECRET_ROTATION_OVERLAP_SECONDS=60),
            patch.object(
                WebhookEndpoint.objects,
                "select_for_update",
                wraps=WebhookEndpoint.objects.select_for_update,
            ) as select_for_update,
        ):
            response = self.client.post(
                reverse("webhook-endpoint-rotate", kwargs={"webhook_id": endpoint.public_id}),
                format="json",
                HTTP_IDEMPOTENCY_KEY="rotate-webhook-secret",
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        select_for_update.assert_called_once_with()
        endpoint.refresh_from_db()
        new_secret = response.data["data"]["secret"]
        self.assertEqual(endpoint.signing_secret_version, 2)
        self.assertEqual(
            endpoint.previous_signing_key,
            hashlib.sha256(b"old-secret").hexdigest(),
        )
        self.assertTrue(endpoint.verify_secret(new_secret))
        self.assertFalse(endpoint.verify_secret("old-secret"))
        self.assertTrue(endpoint.previous_secret_overlap_active)
        self.assertEqual(response.data["data"]["signing_secret_version"], 2)
        self.assertIsNotNone(response.data["data"]["previous_secret_expires_at"])
        audit_event = AuditEvent.objects.get(
            tenant=self.tenant,
            action="webhook_endpoint.rotate",
            target_id=endpoint.public_id,
        )
        self.assertNotIn(new_secret, json.dumps(audit_event.metadata_json))

    def test_rotate_signing_secret_replays_the_same_secret(self):
        endpoint = WebhookEndpoint(
            tenant=self.tenant,
            url="https://example.com/webhooks/replay-rotation",
            events_json=["verification.verified"],
            created_by=self.user,
        )
        endpoint.set_secret("old-secret")
        endpoint.save()
        url = reverse("webhook-endpoint-rotate", kwargs={"webhook_id": endpoint.public_id})

        first = self.client.post(url, format="json", HTTP_IDEMPOTENCY_KEY="same-rotation")
        replay = self.client.post(url, format="json", HTTP_IDEMPOTENCY_KEY="same-rotation")

        self.assertEqual(first.data["data"], replay.data["data"])
        endpoint.refresh_from_db()
        self.assertEqual(endpoint.signing_secret_version, 2)

    def test_rotate_signing_secret_rejects_an_obsolete_idempotent_replay(self):
        endpoint = WebhookEndpoint(
            tenant=self.tenant,
            url="https://example.com/webhooks/obsolete-replay",
            events_json=["verification.verified"],
            created_by=self.user,
        )
        endpoint.set_secret("original-secret")
        endpoint.save()
        url = reverse("webhook-endpoint-rotate", kwargs={"webhook_id": endpoint.public_id})

        first = self.client.post(url, format="json", HTTP_IDEMPOTENCY_KEY="first-rotation")
        first_secret = first.data["data"]["secret"]
        endpoint.refresh_from_db()
        endpoint.previous_secret_expires_at = timezone.now() - timedelta(seconds=1)
        endpoint.save(update_fields=["previous_secret_expires_at", "updated_at"])
        second = self.client.post(url, format="json", HTTP_IDEMPOTENCY_KEY="second-rotation")
        obsolete_replay = self.client.post(
            url, format="json", HTTP_IDEMPOTENCY_KEY="first-rotation"
        )

        self.assertEqual(first.status_code, status.HTTP_200_OK)
        self.assertEqual(second.status_code, status.HTTP_200_OK)
        self.assertEqual(obsolete_replay.status_code, status.HTTP_409_CONFLICT)
        self.assertNotIn(first_secret, json.dumps(obsolete_replay.data))
        endpoint.refresh_from_db()
        self.assertEqual(endpoint.signing_secret_version, 3)

    def test_rotate_signing_secret_rejects_a_new_rotation_during_overlap(self):
        endpoint = WebhookEndpoint(
            tenant=self.tenant,
            url="https://example.com/webhooks/overlapping-rotation",
            events_json=["verification.verified"],
            created_by=self.user,
        )
        endpoint.set_secret("old-secret")
        endpoint.save()
        url = reverse("webhook-endpoint-rotate", kwargs={"webhook_id": endpoint.public_id})

        first = self.client.post(url, format="json", HTTP_IDEMPOTENCY_KEY="rotation-one")
        rejected = self.client.post(
            url, format="json", HTTP_IDEMPOTENCY_KEY="rotation-two"
        )

        self.assertEqual(first.status_code, status.HTTP_200_OK)
        self.assertEqual(rejected.status_code, status.HTTP_409_CONFLICT)
        endpoint.refresh_from_db()
        self.assertEqual(endpoint.signing_secret_version, 2)
        self.assertEqual(
            endpoint.signing_key,
            hashlib.sha256(first.data["data"]["secret"].encode()).hexdigest(),
        )
        self.assertEqual(
            endpoint.previous_signing_key,
            hashlib.sha256(b"old-secret").hexdigest(),
        )

    def test_rotate_signing_secret_requires_idempotency_key(self):
        endpoint = WebhookEndpoint(
            tenant=self.tenant,
            url="https://example.com/webhooks/missing-rotation-key",
            events_json=["verification.verified"],
            created_by=self.user,
        )
        endpoint.set_secret("old-secret")
        endpoint.save()

        response = self.client.post(
            reverse("webhook-endpoint-rotate", kwargs={"webhook_id": endpoint.public_id}),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        endpoint.refresh_from_db()
        self.assertEqual(endpoint.signing_secret_version, 1)

    def test_rotate_signing_secret_cannot_cross_tenant_boundary(self):
        other_organization = Organization.objects.create(name="Other", slug="other", status="active")
        other_tenant = Tenant.objects.create(
            organization=other_organization,
            name="Other Tenant",
            slug="other-tenant",
            status="active",
        )
        other_user = PlatformUser.objects.create_user(
            email="other-owner@example.com",
            password="StrongPassword123!",
            status=PlatformUserStatus.ACTIVE,
            tenant=other_tenant,
        )
        endpoint = WebhookEndpoint(
            tenant=other_tenant,
            url="https://other.example.com/webhooks/identitycore",
            events_json=["verification.verified"],
            created_by=other_user,
        )
        endpoint.set_secret("other-secret")
        endpoint.save()

        response = self.client.post(
            reverse("webhook-endpoint-rotate", kwargs={"webhook_id": endpoint.public_id}),
            format="json",
            HTTP_IDEMPOTENCY_KEY="cross-tenant-rotation",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        endpoint.refresh_from_db()
        self.assertEqual(endpoint.signing_secret_version, 1)
        self.assertTrue(endpoint.verify_secret("other-secret"))

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
                "policy_id": self.policy.public_id,
                "verification_subject": {"full_name": "Kwame Mensah"},
            },
            format="json",
            HTTP_X_CLIENT_ID=api_client.client_id,
            HTTP_IDEMPOTENCY_KEY="webhook-verification-created",
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
            HTTP_IDEMPOTENCY_KEY="manual-webhook-decision",
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
        sent_payload = json.loads(mock_send_request.call_args.kwargs["payload_bytes"].decode())
        self.assertEqual(sent_payload["id"], webhook_event.public_id)
        self.assertEqual(sent_payload["schema_version"], "1")
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
    def test_delivered_event_is_not_sent_twice(self, mock_send_request):
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
            status=WebhookEventStatus.DELIVERED,
            attempt_count=1,
            last_attempt_at=timezone.now(),
        )

        deliver_webhook_event(webhook_event)

        webhook_event.refresh_from_db()
        self.assertEqual(webhook_event.status, WebhookEventStatus.DELIVERED)
        self.assertEqual(webhook_event.attempt_count, 1)
        self.assertEqual(WebhookDeliveryAttempt.objects.filter(webhook_event=webhook_event).count(), 0)
        mock_send_request.assert_not_called()

    def test_missing_signing_key_marks_event_failed(self):
        endpoint = WebhookEndpoint.objects.create(
            tenant=self.tenant,
            url="https://example.com/webhooks/identitycore",
            events_json=["verification.verified"],
            created_by=self.user,
            secret_hash="placeholder",
            signing_key="",
        )
        webhook_event = WebhookEvent.objects.create(
            tenant=self.tenant,
            webhook_endpoint=endpoint,
            event_type="verification.verified",
            payload_json={"id": "evt_1", "type": "verification.verified", "data": {"status": "verified"}},
        )

        deliver_webhook_event(webhook_event)

        webhook_event.refresh_from_db()
        self.assertEqual(webhook_event.status, WebhookEventStatus.FAILED)
        self.assertEqual(webhook_event.attempt_count, 1)
        self.assertIsNone(webhook_event.next_retry_at)
        attempt = WebhookDeliveryAttempt.objects.get(webhook_event=webhook_event)
        self.assertEqual(attempt.status_code, None)
        self.assertIn("signing key is unavailable", attempt.error_message)
        self.assertTrue(
            AuditEvent.objects.filter(
                tenant=self.tenant,
                action="webhook.delivery_failed",
                target_id=webhook_event.public_id,
            ).exists()
        )

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
        fixture = json.loads((Path(__file__).resolve().parents[4] / "sdk/fixtures/webhook-signature-v1.json").read_text())
        endpoint = WebhookEndpoint(
            tenant=self.tenant,
            url="https://example.com/webhooks/identitycore",
            events_json=["verification.verified"],
            created_by=self.user,
        )
        endpoint.set_secret(fixture["current_secret"])

        signature = _build_signature(endpoint.signing_key, fixture["timestamp"], fixture["event_id"], fixture["raw_body"].encode())
        other_event_signature = _build_signature(endpoint.signing_key, fixture["timestamp"], "evt_other", fixture["raw_body"].encode())

        self.assertEqual(signature, fixture["current_signature"])
        self.assertNotEqual(signature, other_event_signature)

    @patch("apps.webhooks.services.request.urlopen")
    def test_delivery_sends_version_and_event_bound_signature_headers(self, mock_urlopen):
        response = MagicMock(status=200)
        response.read.return_value = b"ok"
        mock_urlopen.return_value.__enter__.return_value = response
        endpoint = WebhookEndpoint(
            tenant=self.tenant,
            url="https://example.com/webhooks/identitycore",
            events_json=["verification.verified"],
            created_by=self.user,
            signing_secret_version=3,
        )
        endpoint.set_secret("secret")
        endpoint.save()
        event = WebhookEvent.objects.create(
            tenant=self.tenant,
            webhook_endpoint=endpoint,
            event_type="verification.verified",
            payload_json={"id": "placeholder", "schema_version": "1"},
        )

        _send_webhook_request(
            webhook_event=event,
            payload_bytes=b'{"id":"placeholder","schema_version":"1"}',
            timestamp="1720180800",
        )

        sent_request = mock_urlopen.call_args.args[0]
        self.assertEqual(sent_request.get_header("X-identitycore-event-id"), event.public_id)
        self.assertEqual(sent_request.get_header("X-identitycore-signature-version"), "v1")
        self.assertEqual(sent_request.get_header("X-identitycore-signing-secret-version"), "3")
        self.assertTrue(sent_request.get_header("X-identitycore-signature").startswith("sha256="))
        self.assertTrue(sent_request.get_header("X-identitycore-signature-v1").startswith("v1="))

    @patch("apps.webhooks.services.request.urlopen")
    def test_delivery_is_signed_with_current_and_previous_keys_during_overlap(self, mock_urlopen):
        response = MagicMock(status=200)
        response.read.return_value = b"ok"
        mock_urlopen.return_value.__enter__.return_value = response
        endpoint = WebhookEndpoint(
            tenant=self.tenant,
            url="https://example.com/webhooks/rotating",
            events_json=["verification.verified"],
            created_by=self.user,
        )
        endpoint.set_secret("previous-secret")
        endpoint.rotate_secret(
            "current-secret",
            previous_secret_expires_at=timezone.now() + timedelta(minutes=5),
        )
        endpoint.save()
        event = WebhookEvent.objects.create(
            tenant=self.tenant,
            webhook_endpoint=endpoint,
            event_type="verification.verified",
            payload_json={"id": "placeholder", "schema_version": "1"},
        )
        payload = b'{"id":"placeholder","schema_version":"1"}'

        _send_webhook_request(
            webhook_event=event, payload_bytes=payload, timestamp="1720180800"
        )

        sent_request = mock_urlopen.call_args.args[0]
        signature_header = sent_request.get_header(
            "X-identitycore-signature-v1"
        )
        self.assertEqual(
            signature_header.split(","),
            [
                _build_signature(
                    endpoint.signing_key, "1720180800", event.public_id, payload
                ),
                _build_signature(
                    endpoint.previous_signing_key,
                    "1720180800",
                    event.public_id,
                    payload,
                ),
            ],
        )

        self.assertEqual(
            sent_request.get_header("X-identitycore-signature"),
            _build_legacy_signature(
                endpoint.previous_signing_key, "1720180800", payload
            ),
        )

        endpoint.previous_secret_expires_at = timezone.now() - timedelta(seconds=1)
        endpoint.save(update_fields=["previous_secret_expires_at", "updated_at"])
        _send_webhook_request(
            webhook_event=event, payload_bytes=payload, timestamp="1720180801"
        )
        sent_request = mock_urlopen.call_args.args[0]
        self.assertEqual(
            sent_request.get_header("X-identitycore-signature-v1"),
            _build_signature(
                endpoint.signing_key, "1720180801", event.public_id, payload
            ),
        )
        self.assertEqual(
            sent_request.get_header("X-identitycore-signature"),
            _build_legacy_signature(endpoint.signing_key, "1720180801", payload),
        )

    @patch("apps.webhooks.services.request.urlopen")
    def test_delivery_refreshes_signing_state_after_concurrent_rotation(self, mock_urlopen):
        response = MagicMock(status=200)
        response.read.return_value = b"ok"
        mock_urlopen.return_value.__enter__.return_value = response
        endpoint = WebhookEndpoint(
            tenant=self.tenant,
            url="https://example.com/webhooks/stale-worker",
            events_json=["verification.verified"],
            created_by=self.user,
        )
        endpoint.set_secret("old-secret")
        endpoint.save()
        event = WebhookEvent.objects.create(
            tenant=self.tenant,
            webhook_endpoint=endpoint,
            event_type="verification.verified",
            payload_json={"id": "placeholder", "schema_version": "1"},
        )
        stale_event = WebhookEvent.objects.select_related("webhook_endpoint").get(
            pk=event.pk
        )
        rotated_endpoint = WebhookEndpoint.objects.get(pk=endpoint.pk)
        rotated_endpoint.rotate_secret(
            "new-secret",
            previous_secret_expires_at=timezone.now() - timedelta(seconds=1),
        )
        rotated_endpoint.save(
            update_fields=[
                "secret_hash",
                "signing_key",
                "previous_signing_key",
                "signing_secret_version",
                "previous_secret_expires_at",
                "updated_at",
            ]
        )
        payload = b'{"id":"placeholder","schema_version":"1"}'

        _send_webhook_request(
            webhook_event=stale_event,
            payload_bytes=payload,
            timestamp="1720180802",
        )

        sent_request = mock_urlopen.call_args.args[0]
        self.assertEqual(
            sent_request.get_header("X-identitycore-signature-v1"),
            _build_signature(
                rotated_endpoint.signing_key,
                "1720180802",
                event.public_id,
                payload,
            ),
        )
        self.assertEqual(
            sent_request.get_header("X-identitycore-signing-secret-version"), "2"
        )


class WebhookOutboxTransactionTests(TransactionTestCase):
    def setUp(self):
        organization = Organization.objects.create(
            name="Outbox Organization", slug="outbox-organization"
        )
        self.tenant = Tenant.objects.create(
            organization=organization,
            name="Outbox Tenant",
            slug="outbox-tenant",
            status="active",
        )
        self.user = PlatformUser.objects.create_user(
            email="outbox@example.com",
            password="StrongPassword123!",
            status=PlatformUserStatus.ACTIVE,
            tenant=self.tenant,
        )
        self.endpoint = WebhookEndpoint(
            tenant=self.tenant,
            url="https://example.com/webhooks/outbox",
            events_json=["verification.verified"],
            created_by=self.user,
        )
        self.endpoint.set_secret("outbox-secret")
        self.endpoint.save()

    def queue_event(self):
        return queue_webhook_events(
            tenant=self.tenant,
            event_type="verification.verified",
            payload={"status": "verified"},
        )

    def test_queue_requires_an_active_domain_transaction(self):
        with self.assertRaisesMessage(
            RuntimeError,
            "Webhook outbox events must be queued inside the domain transaction.",
        ):
            self.queue_event()
        self.assertFalse(WebhookEvent.objects.exists())

    def test_rolled_back_domain_change_never_leaves_an_outbox_event(self):
        with self.assertRaises(RuntimeError):
            with transaction.atomic():
                self.endpoint.description = "must roll back"
                self.endpoint.save(update_fields=["description", "updated_at"])
                self.queue_event()
                raise RuntimeError("force rollback")

        self.endpoint.refresh_from_db()
        self.assertEqual(self.endpoint.description, "")
        self.assertFalse(WebhookEvent.objects.exists())

    @patch("apps.webhooks.services._send_webhook_request")
    def test_committed_outbox_event_is_eventually_delivered(self, send_request):
        send_request.return_value = (200, "ok", 5)
        with transaction.atomic():
            self.endpoint.description = "committed"
            self.endpoint.save(update_fields=["description", "updated_at"])
            queued = self.queue_event()

        self.assertEqual(len(queued), 1)
        self.assertEqual(process_pending_webhook_events(limit=10), 1)
        event = WebhookEvent.objects.get(pk=queued[0].pk)
        self.assertEqual(event.status, WebhookEventStatus.DELIVERED)
        self.assertEqual(event.payload_json["id"], event.public_id)

    @patch("apps.webhooks.services._send_webhook_request")
    def test_duplicate_delivery_uses_one_stable_event_id(self, send_request):
        send_request.side_effect = [(500, "retry", 5), (200, "ok", 5)]
        with transaction.atomic():
            event = self.queue_event()[0]

        deliver_webhook_event(event)
        first_event_id = send_request.call_args_list[0].kwargs[
            "webhook_event"
        ].public_id
        deliver_webhook_event(event)
        second_event_id = send_request.call_args_list[1].kwargs[
            "webhook_event"
        ].public_id

        event.refresh_from_db()
        self.assertEqual(first_event_id, event.public_id)
        self.assertEqual(second_event_id, event.public_id)
        self.assertEqual(event.payload_json["id"], event.public_id)
        self.assertEqual(event.attempt_count, 2)
        self.assertEqual(event.status, WebhookEventStatus.DELIVERED)
