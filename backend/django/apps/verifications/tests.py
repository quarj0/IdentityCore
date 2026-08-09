from datetime import timedelta
from unittest.mock import Mock, patch

from django.urls import reverse
from django.test import TestCase
from django.test import override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import PlatformUser, PlatformUserStatus
from apps.api_clients.models import APIClient
from apps.audit.models import AuditEvent
from apps.biometrics.models import (
    FaceMatch,
    LivenessCheck,
    SelfieCapture,
    SelfieCaptureStatus,
)
from apps.document_captures.models import DocumentCapture, DocumentCaptureStatus
from apps.identity_documents.models import IdentityDocument, IdentityDocumentStatus
from apps.notifications.models import Notification
from apps.organizations.models import Organization
from apps.projects.models import Project, ProjectEnvironment
from apps.risk.models import RiskAssessment
from apps.tenants.models import Tenant
from apps.verification_policies.models import VerificationPolicy
from apps.verifications.models import (
    Verification,
    VerificationDecision,
    RetentionLegalHold,
    VerificationSession,
    VerificationSessionStatus,
    VerificationStatus,
    VerificationReviewOwner,
)
from apps.verifications.tasks import (
    cleanup_expired_verification_sessions_task,
    cleanup_retained_media_task,
    expire_pending_verifications_task,
)
from apps.verifications.transitions import (
    VerificationTransitionError,
    transition_verification,
)
from apps.verification_subjects.models import VerificationSubject
from apps.webhooks.models import WebhookEndpoint, WebhookEvent, WebhookEventStatus
from common.crypto import encrypt_object_bytes


class VerificationTransitionTests(TestCase):
    def setUp(self):
        organization = Organization.objects.create(
            name="Transitions", slug="transitions"
        )
        tenant = Tenant.objects.create(
            organization=organization,
            name="Transitions Tenant",
            slug="transitions-tenant",
            status="active",
        )
        subject = VerificationSubject.objects.create(
            tenant=tenant,
            full_name="Transition Subject",
        )
        self.verification = Verification.objects.create(
            tenant=tenant,
            organization=organization,
            verification_subject=subject,
            purpose="Transition test",
            status=VerificationStatus.PENDING_CONSENT,
            expires_at=timezone.now() + timedelta(hours=1),
        )

    def test_transition_table_applies_valid_change_and_is_idempotent(self):
        transitioned, changed = transition_verification(
            self.verification, VerificationStatus.IN_PROGRESS
        )

        self.assertTrue(changed)
        self.assertEqual(transitioned.status, VerificationStatus.IN_PROGRESS)

        repeated, changed = transition_verification(
            self.verification, VerificationStatus.IN_PROGRESS
        )

        self.assertFalse(changed)
        self.assertEqual(repeated.status, VerificationStatus.IN_PROGRESS)

    def test_invalid_transition_is_rejected_without_mutating_status(self):
        with self.assertRaises(VerificationTransitionError):
            transition_verification(self.verification, VerificationStatus.VERIFIED)

        self.verification.refresh_from_db()
        self.assertEqual(self.verification.status, VerificationStatus.PENDING_CONSENT)

    def test_terminal_transition_records_completion_and_rejects_later_change(self):
        transition_verification(self.verification, VerificationStatus.IN_PROGRESS)
        transitioned, changed = transition_verification(
            self.verification,
            VerificationStatus.CANCELLED,
        )

        self.assertTrue(changed)
        self.assertIsNotNone(transitioned.completed_at)
        with self.assertRaises(VerificationTransitionError):
            transition_verification(self.verification, VerificationStatus.IN_PROGRESS)


class VerificationWorkflowTests(APITestCase):
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
        self.api_client = APIClient(
            tenant=self.tenant,
            created_by=self.user,
            name="Backend",
            scopes_json=["verifications:create", "verifications:read"],
        )
        self.raw_secret = "client-secret"
        self.api_client.set_client_secret(self.raw_secret)
        self.api_client.save()
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

    def auth_headers(self, *, idempotency_key=None):
        self._idempotency_sequence = getattr(self, "_idempotency_sequence", 0) + 1
        return {
            "HTTP_X_CLIENT_ID": self.api_client.client_id,
            "HTTP_AUTHORIZATION": f"Bearer {self.raw_secret}",
            "HTTP_IDEMPOTENCY_KEY": idempotency_key
            or f"test-{self._idempotency_sequence}",
        }

    def authenticate_dashboard_user(self):
        self.client.force_authenticate(self.user)

    def test_dashboard_jwt_is_not_mistaken_for_api_client_secret(self):
        login = self.client.post(
            reverse("auth-login"),
            {"email": "owner@example.com", "password": "StrongPassword123!"},
            format="json",
        )
        access = login.data["data"]["tokens"]["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        response = self.client.get(reverse("verification-list-create"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_verification_creates_subject_and_session(self):
        response = self.client.post(
            reverse("verification-list-create"),
            {
                "external_reference": "customer_12345",
                "purpose": "Customer onboarding verification",
                "policy_id": self.policy.public_id,
                "verification_subject": {
                    "full_name": "Kwame Mensah",
                    "email": "kwame@example.com",
                    "phone_number": "+233500000000",
                },
                "redirect_url": "https://example.com/verification-complete",
                "metadata": {"source": "mobile_app"},
            },
            format="json",
            **self.auth_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["data"]["id"].startswith("ver_"))
        self.assertTrue(response.data["data"]["session_id"].startswith("ses_"))
        verification = Verification.objects.get(public_id=response.data["data"]["id"])
        self.assertEqual(
            verification.verification_subject.external_reference, "customer_12345"
        )
        self.assertTrue(
            Notification.objects.filter(
                tenant=self.tenant,
                template_code="verification.created",
                recipient="kwame@example.com",
            ).exists()
        )

    def test_api_client_create_requires_idempotency_key(self):
        response = self.client.post(
            reverse("verification-list-create"),
            {
                "purpose": "Customer onboarding verification",
                "policy_id": self.policy.public_id,
                "verification_subject": {"full_name": "Kwame Mensah"},
            },
            format="json",
            HTTP_X_CLIENT_ID=self.api_client.client_id,
            HTTP_AUTHORIZATION=f"Bearer {self.raw_secret}",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("idempotency_key", response.data["error"]["details"])

    def test_create_verification_replays_same_idempotency_key(self):
        payload = {
            "purpose": "Customer onboarding verification",
            "policy_id": self.policy.public_id,
            "verification_subject": {"full_name": "Kwame Mensah"},
        }
        headers = self.auth_headers(idempotency_key="customer-123-onboarding")

        first = self.client.post(
            reverse("verification-list-create"), payload, format="json", **headers
        )
        second = self.client.post(
            reverse("verification-list-create"), payload, format="json", **headers
        )

        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second.status_code, status.HTTP_201_CREATED)
        self.assertEqual(first.data["data"]["id"], second.data["data"]["id"])
        self.assertEqual(Verification.objects.count(), 1)

    def test_idempotency_key_rejects_a_different_payload(self):
        headers = self.auth_headers(idempotency_key="customer-123-onboarding")
        base = {
            "purpose": "Customer onboarding verification",
            "policy_id": self.policy.public_id,
            "verification_subject": {"full_name": "Kwame Mensah"},
        }
        self.client.post(
            reverse("verification-list-create"), base, format="json", **headers
        )
        changed = {**base, "external_reference": "different"}
        response = self.client.post(
            reverse("verification-list-create"), changed, format="json", **headers
        )

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(Verification.objects.count(), 1)

    def test_dashboard_user_can_create_verification(self):
        self.authenticate_dashboard_user()

        response = self.client.post(
            reverse("verification-list-create"),
            {
                "external_reference": "customer_dash_123",
                "purpose": "No-code dashboard verification",
                "verification_subject": {
                    "full_name": "Akosua Dashboard",
                    "email": "akosua.dashboard@example.com",
                },
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["data"]["id"].startswith("ver_"))
        self.assertTrue(response.data["data"]["verification_url"])
        verification = Verification.objects.get(public_id=response.data["data"]["id"])
        self.assertEqual(verification.tenant, self.tenant)

    def test_list_verifications_is_tenant_scoped(self):
        response = self.client.post(
            reverse("verification-list-create"),
            {
                "external_reference": "customer_12345",
                "purpose": "Customer onboarding verification",
                "policy_id": self.policy.public_id,
                "verification_subject": {"full_name": "Kwame Mensah"},
            },
            format="json",
            **self.auth_headers(),
        )
        verification_id = response.data["data"]["id"]

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
        other_client = APIClient(
            tenant=other_tenant,
            created_by=other_user,
            name="Other Backend",
            scopes_json=["verifications:create", "verifications:read"],
        )
        other_client.set_client_secret("other-secret")
        other_client.save()
        other_policy = VerificationPolicy.objects.create(
            tenant=other_tenant,
            name="Other Default",
            version=1,
            status="active",
            required_document_types_json=["national_id"],
            required_liveness_level="passive",
            face_match_threshold="0.8500",
            manual_review_threshold="0.6500",
            verification_expiry_minutes=1440,
            media_retention_days=30,
            metadata_retention_days=365,
            created_by=other_user,
        )
        self.client.post(
            reverse("verification-list-create"),
            {
                "external_reference": "beta_123",
                "purpose": "Another verification",
                "policy_id": other_policy.public_id,
                "verification_subject": {"full_name": "Ama Asare"},
            },
            format="json",
            HTTP_X_CLIENT_ID=other_client.client_id,
            HTTP_AUTHORIZATION="Bearer other-secret",
        )

        list_response = self.client.get(
            reverse("verification-list-create"), **self.auth_headers()
        )
        ids = [item["id"] for item in list_response.data["data"]["results"]]
        self.assertEqual(ids, [verification_id])

    def test_dashboard_user_can_list_and_view_verifications(self):
        verification = Verification.objects.create(
            tenant=self.tenant,
            organization=self.organization,
            verification_subject=self.tenant.verification_subjects.create(
                full_name="Dashboard Subject"
            ),
            purpose="Dashboard detail",
            expires_at=timezone.now() + timedelta(hours=1),
            status=VerificationStatus.PENDING_CONSENT,
        )

        self.authenticate_dashboard_user()
        list_response = self.client.get(reverse("verification-list-create"))
        detail_response = self.client.get(
            reverse(
                "verification-detail",
                kwargs={"verification_id": verification.public_id},
            )
        )

        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            list_response.data["data"]["results"][0]["id"], verification.public_id
        )
        self.assertEqual(detail_response.data["data"]["id"], verification.public_id)

    def test_list_rejects_invalid_and_unbounded_pagination(self):
        for query in ("?page=zero", "?page=0", "?page_size=0", "?page_size=101"):
            with self.subTest(query=query):
                response = self.client.get(
                    reverse("verification-list-create") + query,
                    **self.auth_headers(),
                )
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertEqual(response.data["error"]["code"], "validation_error")

        for query in ("?limit=0", "?limit=101", "?limit=many", "?cursor=invalid"):
            with self.subTest(query=query):
                response = self.client.get(
                    reverse("verification-list-create") + query,
                    **self.auth_headers(),
                )
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cursor_traversal_is_stable_during_concurrent_inserts(self):
        def create_verification(name):
            return Verification.objects.create(
                tenant=self.tenant,
                organization=self.organization,
                verification_subject=self.tenant.verification_subjects.create(
                    full_name=name
                ),
                purpose="Cursor traversal",
                expires_at=timezone.now() + timedelta(hours=1),
                status=VerificationStatus.PENDING_CONSENT,
            )

        older = create_verification("Older")
        newest = create_verification("Newest")
        first = self.client.get(
            reverse("verification-list-create") + "?limit=1",
            **self.auth_headers(),
        )
        cursor = first.data["data"]["pagination"]["next_cursor"]
        inserted = create_verification("Inserted concurrently")

        second = self.client.get(
            reverse("verification-list-create") + f"?limit=1&cursor={cursor}",
            **self.auth_headers(),
        )

        self.assertEqual(first.data["data"]["results"][0]["id"], newest.public_id)
        self.assertEqual(second.data["data"]["results"][0]["id"], older.public_id)
        self.assertNotEqual(second.data["data"]["results"][0]["id"], inserted.public_id)

    def test_cursor_cannot_be_reused_with_different_filters(self):
        for name in ("First", "Second"):
            Verification.objects.create(
                tenant=self.tenant,
                organization=self.organization,
                verification_subject=self.tenant.verification_subjects.create(
                    full_name=name
                ),
                purpose="Cursor filters",
                expires_at=timezone.now() + timedelta(hours=1),
                status=VerificationStatus.PENDING_CONSENT,
            )
        first = self.client.get(
            reverse("verification-list-create") + "?limit=1",
            **self.auth_headers(),
        )
        cursor = first.data["data"]["pagination"]["next_cursor"]

        response = self.client.get(
            reverse("verification-list-create")
            + f"?limit=1&status=verified&cursor={cursor}",
            **self.auth_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cursor_cannot_cross_api_client_environment_scope(self):
        for name in ("First", "Second"):
            Verification.objects.create(
                tenant=self.tenant,
                organization=self.organization,
                verification_subject=self.tenant.verification_subjects.create(
                    full_name=name
                ),
                purpose="Cursor scope",
                expires_at=timezone.now() + timedelta(hours=1),
                status=VerificationStatus.PENDING_CONSENT,
            )
        first = self.client.get(
            reverse("verification-list-create") + "?limit=1",
            **self.auth_headers(),
        )
        cursor = first.data["data"]["pagination"]["next_cursor"]
        production_project = Project.objects.create(
            tenant=self.tenant,
            name="Production",
            slug="production",
            environment=ProjectEnvironment.PRODUCTION,
            created_by=self.user,
        )
        self.api_client.project = production_project
        self.api_client.save(update_fields=["project", "updated_at"])

        response = self.client.get(
            reverse("verification-list-create") + f"?limit=1&cursor={cursor}",
            **self.auth_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_rejects_out_of_range_pages_instead_of_repeating_last_page(self):
        response = self.client.get(
            reverse("verification-list-create") + "?page=2",
            **self.auth_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("out of range", response.data["error"]["message"])

    def test_list_filters_by_created_date_and_validates_date_range(self):
        verification = Verification.objects.create(
            tenant=self.tenant,
            organization=self.organization,
            verification_subject=self.tenant.verification_subjects.create(
                full_name="Date Filter Subject"
            ),
            purpose="Date filtering",
            expires_at=timezone.now() + timedelta(hours=1),
            status=VerificationStatus.PENDING_CONSENT,
        )
        today = timezone.localdate().isoformat()

        response = self.client.get(
            reverse("verification-list-create")
            + f"?created_from={today}&created_to={today}",
            **self.auth_headers(),
        )
        invalid_response = self.client.get(
            reverse("verification-list-create")
            + "?created_from=2026-02-02&created_to=2026-02-01",
            **self.auth_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["data"]["results"][0]["id"], verification.public_id
        )
        self.assertEqual(invalid_response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_detail_requires_read_scope(self):
        self.api_client.scopes_json = ["verifications:create"]
        self.api_client.save(update_fields=["scopes_json", "updated_at"])
        verification = Verification.objects.create(
            tenant=self.tenant,
            organization=self.organization,
            verification_subject=self.tenant.verification_subjects.create(
                full_name="Kwame"
            ),
            purpose="Test",
            expires_at=self.tenant.created_at,
            status=VerificationStatus.PENDING_CONSENT,
        )

        response = self.client.get(
            reverse(
                "verification-detail",
                kwargs={"verification_id": verification.public_id},
            ),
            **self.auth_headers(),
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_cancel_verification_marks_cancelled(self):
        create_response = self.client.post(
            reverse("verification-list-create"),
            {
                "external_reference": "customer_12345",
                "purpose": "Customer onboarding verification",
                "policy_id": self.policy.public_id,
                "verification_subject": {
                    "full_name": "Kwame Mensah",
                    "email": "kwame@example.com",
                },
            },
            format="json",
            **self.auth_headers(),
        )
        verification_id = create_response.data["data"]["id"]

        response = self.client.post(
            reverse("verification-cancel", kwargs={"verification_id": verification_id}),
            {"reason": "User abandoned onboarding"},
            format="json",
            **self.auth_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["status"], VerificationStatus.CANCELLED)
        self.assertTrue(
            Notification.objects.filter(
                tenant=self.tenant,
                template_code="verification.cancelled",
            ).exists()
        )

    def test_resend_link_sends_notification_when_subject_has_email(self):
        create_response = self.client.post(
            reverse("verification-list-create"),
            {
                "external_reference": "customer_12345",
                "purpose": "Customer onboarding verification",
                "policy_id": self.policy.public_id,
                "verification_subject": {
                    "full_name": "Kwame Mensah",
                    "email": "kwame@example.com",
                },
            },
            format="json",
            **self.auth_headers(),
        )
        verification_id = create_response.data["data"]["id"]

        response = self.client.post(
            reverse(
                "verification-resend-link", kwargs={"verification_id": verification_id}
            ),
            {"channel": "email"},
            format="json",
            **self.auth_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["data"]["sent"])
        self.assertTrue(
            Notification.objects.filter(
                tenant=self.tenant,
                template_code="verification.created",
                recipient="kwame@example.com",
            ).count()
            >= 2
        )
        self.assertTrue(response.data["data"]["verification_url"])
        self.assertTrue(response.data["data"]["session_id"].startswith("ses_"))

    def test_dashboard_user_can_resend_link(self):
        verification = Verification.objects.create(
            tenant=self.tenant,
            organization=self.organization,
            verification_subject=self.tenant.verification_subjects.create(
                full_name="Resend Dashboard",
                email="resend@example.com",
            ),
            purpose="Resend flow",
            expires_at=timezone.now() + timedelta(hours=1),
            status=VerificationStatus.PENDING_CONSENT,
        )

        self.authenticate_dashboard_user()
        response = self.client.post(
            reverse(
                "verification-resend-link",
                kwargs={"verification_id": verification.public_id},
            ),
            {"channel": "email"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["data"]["sent"])
        self.assertTrue(response.data["data"]["verification_url"])

    def test_detail_includes_latest_liveness_and_face_match_states(self):
        subject = self.tenant.verification_subjects.create(full_name="Kwame")
        verification = Verification.objects.create(
            tenant=self.tenant,
            organization=self.organization,
            verification_subject=subject,
            purpose="Test",
            expires_at=self.tenant.created_at,
            status=VerificationStatus.PROCESSING,
        )
        identity_document = IdentityDocument.objects.create(
            tenant=self.tenant,
            verification=verification,
            verification_subject=subject,
            document_type_id="national_id",
            country_profile_id="GH",
            status="processing",
        )
        document_capture = DocumentCapture.objects.create(
            tenant=self.tenant,
            identity_document=identity_document,
            side="front",
            storage_key="uploads/documents/upl_01JABC",
            storage_provider="local",
            mime_type="image/jpeg",
            file_size_bytes=0,
            checksum_sha256="",
            status="uploaded",
            captured_at=self.tenant.created_at,
        )
        selfie_capture = self.tenant.selfie_captures.create(
            verification=verification,
            verification_subject=subject,
            storage_key="uploads/selfies/upl_01JSELFIE",
            storage_provider="local",
            capture_type="image",
            mime_type="image/jpeg",
            file_size_bytes=0,
            checksum_sha256="",
            face_count=1,
            status="uploaded",
            captured_at=self.tenant.created_at,
        )
        LivenessCheck.objects.create(
            tenant=self.tenant,
            verification=verification,
            selfie_capture=selfie_capture,
            liveness_type="passive",
            status="inconclusive",
            checked_at=self.tenant.created_at,
        )
        FaceMatch.objects.create(
            tenant=self.tenant,
            verification=verification,
            selfie_capture=selfie_capture,
            identity_document=identity_document,
            document_capture=document_capture,
            status="inconclusive",
            matched_at=self.tenant.created_at,
        )

        response = self.client.get(
            reverse(
                "verification-detail",
                kwargs={"verification_id": verification.public_id},
            ),
            **self.auth_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["data"]["checks"]["liveness"]["status"], "inconclusive"
        )
        self.assertEqual(
            response.data["data"]["checks"]["face_match"]["status"], "inconclusive"
        )
        self.assertIsNone(response.data["data"]["risk_assessment"])

    def test_create_verification_copies_policy_snapshot(self):
        policy = self.policy

        response = self.client.post(
            reverse("verification-list-create"),
            {
                "external_reference": "customer_999",
                "purpose": "Customer onboarding verification",
                "policy_id": policy.public_id,
                "verification_subject": {
                    "full_name": "Kwame Mensah",
                },
            },
            format="json",
            **self.auth_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        verification = Verification.objects.get(public_id=response.data["data"]["id"])
        self.assertEqual(verification.policy_public_id, policy.public_id)
        self.assertEqual(verification.policy_snapshot_json["id"], policy.public_id)
        self.assertEqual(
            verification.policy_snapshot_json["required_liveness_level"], "passive"
        )

    def test_create_verification_copies_workflow_version_snapshot(self):
        from apps.workflows.models import Workflow, WorkflowVersion

        project = Project.objects.create(
            tenant=self.tenant,
            created_by=self.user,
            name="Sandbox",
            slug="sandbox",
            is_default=True,
        )

        workflow = Workflow.objects.create(
            tenant=self.tenant,
            project=project,
            name="Identity workflow",
            steps_json=["consent", "document", "decision"],
            settings_json={"required_document_types": ["passport"]},
            current_version=1,
            status="published",
            created_by=self.user,
        )
        workflow_version = WorkflowVersion.objects.create(
            workflow=workflow,
            version=1,
            steps_json=workflow.steps_json,
            settings_json=workflow.settings_json,
            policy=self.policy,
            published_by=self.user,
        )

        response = self.client.post(
            reverse("verification-list-create"),
            {
                "external_reference": "customer_workflow_snapshot",
                "purpose": "Customer onboarding verification",
                "policy_id": self.policy.public_id,
                "verification_subject": {"full_name": "Kwame Mensah"},
            },
            format="json",
            **self.auth_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        verification = Verification.objects.get(public_id=response.data["data"]["id"])
        self.assertEqual(
            verification.workflow_snapshot_json["id"], workflow_version.public_id
        )
        self.assertEqual(verification.workflow_snapshot_json["version"], 1)
        self.assertEqual(
            verification.workflow_snapshot_json["steps"], workflow.steps_json
        )

        workflow.steps_json = ["consent", "selfie", "decision"]
        workflow.save(update_fields=["steps_json", "updated_at"])
        verification.refresh_from_db()
        self.assertEqual(
            verification.workflow_snapshot_json["steps"],
            ["consent", "document", "decision"],
        )

    def test_api_client_create_requires_active_policy(self):
        response = self.client.post(
            reverse("verification-list-create"),
            {
                "external_reference": "customer_missing_policy",
                "purpose": "Customer onboarding verification",
                "verification_subject": {"full_name": "Kwame Mensah"},
            },
            format="json",
            **self.auth_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("policy_id", response.data["error"]["details"])

    def test_manual_review_list_is_tenant_scoped(self):
        verification = Verification.objects.create(
            tenant=self.tenant,
            organization=self.organization,
            verification_subject=self.tenant.verification_subjects.create(
                full_name="Reviewer Case",
                email="reviewer@example.com",
            ),
            purpose="Manual review case",
            expires_at=self.tenant.created_at,
            status=VerificationStatus.MANUAL_REVIEW_REQUIRED,
        )
        RiskAssessment.objects.create(
            tenant=self.tenant,
            verification=verification,
            risk_score="78.00",
            risk_level="high",
            recommendation="manual_review",
        )
        other_org = Organization.objects.create(name="Gamma", slug="gamma")
        other_tenant = Tenant.objects.create(
            organization=other_org,
            name="Gamma Tenant",
            slug="gamma-tenant",
            status="active",
        )
        Verification.objects.create(
            tenant=other_tenant,
            organization=other_org,
            verification_subject=other_tenant.verification_subjects.create(
                full_name="Other Case"
            ),
            purpose="Other manual review case",
            expires_at=other_tenant.created_at,
            status=VerificationStatus.MANUAL_REVIEW_REQUIRED,
            metadata_json={"risk_level": "critical"},
        )

        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("manual-review-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["data"]["results"]), 1)
        self.assertEqual(response.data["data"]["results"][0]["risk_level"], "high")

    def test_manual_review_decision_records_manual_decision(self):
        verification = Verification.objects.create(
            tenant=self.tenant,
            organization=self.organization,
            verification_subject=self.tenant.verification_subjects.create(
                full_name="Reviewer Case",
                email="reviewer@example.com",
            ),
            purpose="Manual review case",
            expires_at=self.tenant.created_at,
            status=VerificationStatus.MANUAL_REVIEW_REQUIRED,
        )

        self.client.force_authenticate(self.user)
        response = self.client.post(
            reverse(
                "manual-review-decision",
                kwargs={"verification_id": verification.public_id},
            ),
            {
                "decision": "verified",
                "reason_code": "evidence_confirmed",
                "reason_detail": "Document and selfie match after manual review.",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        verification.refresh_from_db()
        self.assertEqual(verification.status, VerificationStatus.VERIFIED)
        decision = VerificationDecision.objects.get(verification=verification)
        self.assertEqual(decision.decision_type, "manual")
        self.assertEqual(decision.reason_code, "evidence_confirmed")
        verification.refresh_from_db()
        self.assertEqual(verification.assigned_reviewer_id, self.user.id)
        self.assertIsNotNone(verification.assigned_at)
        self.assertTrue(
            Notification.objects.filter(
                tenant=self.tenant,
                template_code="verification.verified",
            ).exists()
        )

    def test_assigned_review_cannot_be_decided_by_another_reviewer(self):
        verification = Verification.objects.create(
            tenant=self.tenant,
            organization=self.organization,
            verification_subject=self.tenant.verification_subjects.create(
                full_name="Assigned Reviewer Case"
            ),
            purpose="Manual review case",
            expires_at=self.tenant.created_at,
            status=VerificationStatus.MANUAL_REVIEW_REQUIRED,
            assigned_reviewer=self.user,
            assigned_at=timezone.now(),
        )
        other_reviewer = PlatformUser.objects.create_user(
            email="other-reviewer@example.com",
            password="StrongPassword123!",
            status=PlatformUserStatus.ACTIVE,
            tenant=self.tenant,
        )
        self.client.force_authenticate(other_reviewer)

        response = self.client.post(
            reverse(
                "manual-review-decision",
                kwargs={"verification_id": verification.public_id},
            ),
            {
                "decision": "verified",
                "reason_code": "evidence_confirmed",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        verification.refresh_from_db()
        self.assertEqual(verification.status, VerificationStatus.MANUAL_REVIEW_REQUIRED)

    def test_high_risk_manual_decision_requires_independent_approval(self):
        verification = Verification.objects.create(
            tenant=self.tenant,
            organization=self.organization,
            verification_subject=self.tenant.verification_subjects.create(
                full_name="High Risk Case"
            ),
            purpose="High risk manual review",
            expires_at=self.tenant.created_at,
            status=VerificationStatus.MANUAL_REVIEW_REQUIRED,
        )
        RiskAssessment.objects.create(
            tenant=self.tenant,
            verification=verification,
            risk_score="85.00",
            risk_level="high",
            recommendation="manual_review",
        )
        checker = PlatformUser.objects.create_user(
            email="checker@example.com",
            password="StrongPassword123!",
            status=PlatformUserStatus.ACTIVE,
            tenant=self.tenant,
        )

        self.client.force_authenticate(self.user)
        proposal = self.client.post(
            reverse(
                "manual-review-decision",
                kwargs={"verification_id": verification.public_id},
            ),
            {"decision": "rejected", "reason_code": "evidence_confirmed"},
            format="json",
        )
        self.assertEqual(proposal.status_code, status.HTTP_202_ACCEPTED)
        verification.refresh_from_db()
        self.assertEqual(verification.status, VerificationStatus.MANUAL_REVIEW_REQUIRED)

        # Authenticate as the independent checker for the approval step.
        self.client.force_authenticate(checker)
        approval = self.client.post(
            reverse(
                "manual-review-approval",
                kwargs={"verification_id": verification.public_id},
            ),
            {"decision": "verified"},
            format="json",
        )
        self.assertEqual(approval.status_code, status.HTTP_200_OK)
        verification.refresh_from_db()
        self.assertEqual(verification.status, VerificationStatus.VERIFIED)
        decision = verification.decision_record
        self.assertEqual(decision.reason_code, "manual_review_verified")
        self.assertEqual(decision.reason_codes_json, ["manual_review_verified"])

    def test_detail_includes_decision_when_present(self):
        verification = Verification.objects.create(
            tenant=self.tenant,
            organization=self.organization,
            verification_subject=self.tenant.verification_subjects.create(
                full_name="Reviewer Case"
            ),
            purpose="Manual review case",
            expires_at=self.tenant.created_at,
            status=VerificationStatus.VERIFIED,
        )
        VerificationDecision.objects.create(
            tenant=self.tenant,
            verification=verification,
            decision="verified",
            decision_type="manual",
            reason_code="evidence_confirmed",
            reason_detail="Document and selfie match after manual review.",
            decided_by=self.user,
            decided_at=self.tenant.created_at,
        )
        RiskAssessment.objects.create(
            tenant=self.tenant,
            verification=verification,
            risk_score="14.00",
            risk_level="low",
            recommendation="approve",
        )

        response = self.client.get(
            reverse(
                "verification-detail",
                kwargs={"verification_id": verification.public_id},
            ),
            **self.auth_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["decision"]["decision"], "verified")
        self.assertEqual(response.data["data"]["decision"]["decision_type"], "manual")
        self.assertEqual(response.data["data"]["risk_assessment"]["risk_level"], "low")

    def test_detail_includes_document_classification_when_present(self):
        verification = Verification.objects.create(
            tenant=self.tenant,
            organization=self.organization,
            verification_subject=self.tenant.verification_subjects.create(
                full_name="Classification Case"
            ),
            purpose="Document classification case",
            expires_at=self.tenant.created_at,
            status=VerificationStatus.AWAITING_SELFIE,
        )
        identity_document = IdentityDocument.objects.create(
            tenant=self.tenant,
            verification=verification,
            verification_subject=verification.verification_subject,
            document_type_id="national_id",
            country_profile_id="GH",
            status=IdentityDocumentStatus.PROCESSED,
            extracted_data_json={
                "document_classification": {
                    "classification_status": "recognized",
                    "predicted_document_type": "passport",
                    "expected_document_type": "national_id",
                    "matched_expected_document_type": False,
                    "workflow_action": "continue_with_review",
                    "requires_manual_review": True,
                    "manual_review": {
                        "required": True,
                        "priority": "high",
                        "reason_codes": ["document_type_mismatch"],
                        "review_category": "document_classification",
                    },
                    "issues": ["document_type_mismatch"],
                }
            },
        )

        response = self.client.get(
            reverse(
                "verification-detail",
                kwargs={"verification_id": verification.public_id},
            ),
            **self.auth_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["data"]["document_classification"]["classification_status"],
            "recognized",
        )
        self.assertEqual(
            response.data["data"]["document_classification"]["manual_review"][
                "priority"
            ],
            "high",
        )
        self.assertEqual(
            response.data["data"]["document_classification"]["issues"],
            ["document_type_mismatch"],
        )
        self.assertEqual(
            identity_document.extracted_data_json["document_classification"][
                "workflow_action"
            ],
            "continue_with_review",
        )

    @override_settings(
        OBJECT_STORAGE_EVIDENCE_BUCKET="identitycore-evidence",
        OBJECT_STORAGE_ENDPOINT_URL="https://example.r2.cloudflarestorage.com",
        OBJECT_STORAGE_ACCESS_KEY_ID="key",
        OBJECT_STORAGE_SECRET_ACCESS_KEY="secret",
        OBJECT_STORAGE_REGION="auto",
        OBJECT_STORAGE_SIGNATURE_VERSION="s3v4",
    )
    @patch("common.storage.boto3.client")
    def test_evidence_report_endpoint_generates_report_in_evidence_bucket(
        self, mock_client_factory
    ):
        mock_client = Mock()
        mock_client.generate_presigned_url.side_effect = [
            "https://r2.example/evidence-download",
            "https://r2.example/evidence-download.pdf",
        ]
        mock_client_factory.return_value = mock_client
        verification = Verification.objects.create(
            tenant=self.tenant,
            organization=self.organization,
            verification_subject=self.tenant.verification_subjects.create(
                full_name="Reviewer Case"
            ),
            purpose="Manual review case",
            expires_at=self.tenant.created_at,
            status=VerificationStatus.VERIFIED,
            completed_at=timezone.now(),
        )
        VerificationDecision.objects.create(
            tenant=self.tenant,
            verification=verification,
            decision="verified",
            decision_type="manual",
            reason_code="evidence_confirmed",
            reason_detail="Document and selfie match after manual review.",
            decided_by=self.user,
            decided_at=self.tenant.created_at,
        )

        response = self.client.get(
            reverse(
                "verification-evidence-report",
                kwargs={"verification_id": verification.public_id},
            ),
            **self.auth_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        verification.refresh_from_db()
        self.assertIn("evidence_report_storage_key", verification.metadata_json)
        self.assertIn("evidence_report_pdf_storage_key", verification.metadata_json)
        self.assertTrue(
            response.data["data"]["download_url"].endswith(
                f"/api/v1/verifications/{verification.public_id}/evidence-report/download"
            )
        )
        self.assertTrue(
            response.data["data"]["pdf_download_url"].endswith(
                f"/api/v1/verifications/{verification.public_id}/evidence-report/download.pdf"
            )
        )
        self.assertEqual(mock_client.put_object.call_count, 2)

    @override_settings(
        OBJECT_STORAGE_EVIDENCE_BUCKET="identitycore-evidence",
        OBJECT_STORAGE_ENDPOINT_URL="https://example.r2.cloudflarestorage.com",
        OBJECT_STORAGE_ACCESS_KEY_ID="key",
        OBJECT_STORAGE_SECRET_ACCESS_KEY="secret",
        OBJECT_STORAGE_REGION="auto",
        OBJECT_STORAGE_SIGNATURE_VERSION="s3v4",
    )
    @patch("common.storage.boto3.client")
    def test_dashboard_user_can_fetch_evidence_report(self, mock_client_factory):
        mock_client = Mock()
        mock_client.generate_presigned_url.side_effect = [
            "https://r2.example/evidence-download",
            "https://r2.example/evidence-download.pdf",
        ]
        mock_client_factory.return_value = mock_client
        verification = Verification.objects.create(
            tenant=self.tenant,
            organization=self.organization,
            verification_subject=self.tenant.verification_subjects.create(
                full_name="Dashboard Evidence"
            ),
            purpose="Dashboard evidence case",
            expires_at=timezone.now() + timedelta(hours=1),
            status=VerificationStatus.VERIFIED,
            completed_at=timezone.now(),
        )
        VerificationDecision.objects.create(
            tenant=self.tenant,
            verification=verification,
            decision="verified",
            decision_type="manual",
            reason_code="evidence_confirmed",
            decided_by=self.user,
            decided_at=timezone.now(),
        )

        self.authenticate_dashboard_user()
        response = self.client.get(
            reverse(
                "verification-evidence-report",
                kwargs={"verification_id": verification.public_id},
            )
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            response.data["data"]["pdf_download_url"].endswith(
                f"/api/v1/verifications/{verification.public_id}/evidence-report/download.pdf"
            )
        )

    @override_settings(
        OBJECT_STORAGE_EVIDENCE_BUCKET="identitycore-evidence",
        OBJECT_STORAGE_ENDPOINT_URL="https://example.r2.cloudflarestorage.com",
        OBJECT_STORAGE_ACCESS_KEY_ID="key",
        OBJECT_STORAGE_SECRET_ACCESS_KEY="secret",
        OBJECT_STORAGE_REGION="auto",
        OBJECT_STORAGE_SIGNATURE_VERSION="s3v4",
    )
    @patch("common.storage.boto3.client")
    def test_detail_includes_evidence_report_when_generated(self, mock_client_factory):
        mock_client = Mock()
        mock_client.generate_presigned_url.side_effect = [
            "https://r2.example/evidence-download",
            "https://r2.example/evidence-download.pdf",
        ]
        mock_client_factory.return_value = mock_client
        verification = Verification.objects.create(
            tenant=self.tenant,
            organization=self.organization,
            verification_subject=self.tenant.verification_subjects.create(
                full_name="Evidence Case"
            ),
            purpose="Evidence case",
            expires_at=self.tenant.created_at,
            status=VerificationStatus.VERIFIED,
            metadata_json={
                "evidence_report_storage_key": (
                    f"organizations/{self.organization.public_id}/verifications/ver_test/reports/verification-report.json"
                ),
                "evidence_report_pdf_storage_key": (
                    f"organizations/{self.organization.public_id}/verifications/ver_test/reports/verification-report.pdf"
                ),
                "evidence_report_encrypted": True,
                "evidence_report_pdf_encrypted": True,
            },
        )

        response = self.client.get(
            reverse(
                "verification-detail",
                kwargs={"verification_id": verification.public_id},
            ),
            **self.auth_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            response.data["data"]["evidence_report"]["download_url"].endswith(
                f"/api/v1/verifications/{verification.public_id}/evidence-report/download"
            )
        )
        self.assertTrue(
            response.data["data"]["evidence_report"]["pdf_download_url"].endswith(
                f"/api/v1/verifications/{verification.public_id}/evidence-report/download.pdf"
            )
        )

    @override_settings(
        OBJECT_STORAGE_EVIDENCE_BUCKET="identitycore-evidence",
        OBJECT_STORAGE_ENDPOINT_URL="https://example.r2.cloudflarestorage.com",
        OBJECT_STORAGE_ACCESS_KEY_ID="key",
        OBJECT_STORAGE_SECRET_ACCESS_KEY="secret",
        OBJECT_STORAGE_REGION="auto",
        OBJECT_STORAGE_SIGNATURE_VERSION="s3v4",
        APP_MANAGED_MEDIA_ENCRYPTION_ENABLED=True,
    )
    @patch("common.storage.boto3.client")
    def test_encrypted_evidence_download_endpoint_decrypts_pdf_payload(
        self, mock_client_factory
    ):
        encrypted_payload = encrypt_object_bytes(
            content=b"%PDF-test",
            content_type="application/pdf",
            purpose="evidence.reports",
        )
        mock_client = Mock()
        mock_client.get_object.return_value = {
            "Body": Mock(read=Mock(return_value=encrypted_payload)),
            "ContentType": "application/vnd.identitycore.encrypted+json",
        }
        mock_client_factory.return_value = mock_client
        verification = Verification.objects.create(
            tenant=self.tenant,
            organization=self.organization,
            verification_subject=self.tenant.verification_subjects.create(
                full_name="Encrypted Evidence"
            ),
            purpose="Encrypted evidence case",
            expires_at=self.tenant.created_at,
            status=VerificationStatus.VERIFIED,
            metadata_json={
                "evidence_report_pdf_storage_key": (
                    f"organizations/{self.organization.public_id}/verifications/ver_pdf/reports/verification-report.pdf"
                ),
                "evidence_report_pdf_encrypted": True,
            },
        )

        response = self.client.get(
            reverse(
                "verification-evidence-report-pdf-download",
                kwargs={"verification_id": verification.public_id},
            ),
            **self.auth_headers(),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertEqual(response.content, b"%PDF-test")


class VerificationOperationsTaskTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name="Acme", slug="acme-ops")
        self.tenant = Tenant.objects.create(
            organization=self.organization,
            name="Acme Ops Tenant",
            slug="acme-ops-tenant",
            status="active",
        )
        self.user = PlatformUser.objects.create_user(
            email="ops@example.com",
            password="StrongPassword123!",
            status=PlatformUserStatus.ACTIVE,
            tenant=self.tenant,
        )
        self.subject = VerificationSubject.objects.create(
            tenant=self.tenant,
            full_name="Akosua Owusu",
            email="akosua@example.com",
        )

    def test_expire_pending_verifications_task_expires_records_and_queues_follow_up_work(
        self,
    ):
        verification = Verification.objects.create(
            tenant=self.tenant,
            organization=self.organization,
            verification_subject=self.subject,
            purpose="Customer onboarding",
            status=VerificationStatus.IN_PROGRESS,
            external_reference="ext-123",
            expires_at=timezone.now() - timedelta(minutes=5),
        )
        session = VerificationSession.objects.create(
            verification=verification,
            tenant=self.tenant,
            session_token_hash="hashed-session-token",
            status=VerificationSessionStatus.ACTIVE,
            expires_at=timezone.now() - timedelta(minutes=5),
        )
        webhook_endpoint = WebhookEndpoint(
            tenant=self.tenant,
            created_by=self.user,
            url="https://example.com/webhooks/verification",
            events_json=["verification.expired"],
        )
        webhook_endpoint.set_secret("webhook-secret")
        webhook_endpoint.save()

        processed = expire_pending_verifications_task(limit=10)

        verification.refresh_from_db()
        session.refresh_from_db()
        self.assertEqual(processed, 1)
        self.assertEqual(verification.status, VerificationStatus.EXPIRED)
        self.assertIsNotNone(verification.completed_at)
        self.assertEqual(session.status, VerificationSessionStatus.EXPIRED)
        self.assertTrue(
            AuditEvent.objects.filter(
                tenant=self.tenant,
                action="verification.expired",
                target_id=verification.public_id,
            ).exists()
        )
        self.assertTrue(
            WebhookEvent.objects.filter(
                tenant=self.tenant,
                webhook_endpoint=webhook_endpoint,
                event_type="verification.expired",
                status=WebhookEventStatus.PENDING,
            ).exists()
        )
        self.assertTrue(
            Notification.objects.filter(
                tenant=self.tenant,
                template_code="verification.expired",
                recipient="akosua@example.com",
            ).exists()
        )

    def test_cleanup_expired_verification_sessions_task_marks_due_sessions_expired(
        self,
    ):
        verification = Verification.objects.create(
            tenant=self.tenant,
            organization=self.organization,
            verification_subject=self.subject,
            purpose="Customer onboarding",
            status=VerificationStatus.PENDING_CONSENT,
            expires_at=timezone.now() + timedelta(hours=1),
        )
        due_session = VerificationSession.objects.create(
            verification=verification,
            tenant=self.tenant,
            session_token_hash="due-session-hash",
            status=VerificationSessionStatus.CREATED,
            expires_at=timezone.now() - timedelta(minutes=2),
        )
        future_session = VerificationSession.objects.create(
            verification=verification,
            tenant=self.tenant,
            session_token_hash="future-session-hash",
            status=VerificationSessionStatus.ACTIVE,
            expires_at=timezone.now() + timedelta(minutes=30),
        )

        updated = cleanup_expired_verification_sessions_task(limit=10)

        due_session.refresh_from_db()
        future_session.refresh_from_db()
        self.assertEqual(updated, 1)
        self.assertEqual(due_session.status, VerificationSessionStatus.EXPIRED)
        self.assertEqual(future_session.status, VerificationSessionStatus.ACTIVE)

    def test_cleanup_retained_media_task_deletes_raw_media_and_preserves_metadata(self):
        verification = Verification.objects.create(
            tenant=self.tenant,
            organization=self.organization,
            verification_subject=self.subject,
            purpose="Completed verification",
            status=VerificationStatus.VERIFIED,
            policy_snapshot_json={
                "media_retention_days": 30,
                "metadata_retention_days": 365,
            },
            expires_at=timezone.now() - timedelta(days=31),
            completed_at=timezone.now() - timedelta(days=31),
        )
        identity_document = IdentityDocument.objects.create(
            tenant=self.tenant,
            verification=verification,
            verification_subject=self.subject,
            document_type_id="national_id",
            country_profile_id="GH",
            status="processed",
            extracted_data_json={"full_name": "Akosua Owusu"},
        )
        document_capture = DocumentCapture.objects.create(
            tenant=self.tenant,
            identity_document=identity_document,
            side="front",
            storage_key="uploads/documents/upl_retention",
            storage_provider="local",
            mime_type="image/jpeg",
            file_size_bytes=1024,
            checksum_sha256="abc123",
            status=DocumentCaptureStatus.UPLOADED,
            captured_at=timezone.now() - timedelta(days=31),
        )
        selfie_capture = SelfieCapture.objects.create(
            tenant=self.tenant,
            verification=verification,
            verification_subject=self.subject,
            storage_key="uploads/selfies/upl_selfie_retention",
            storage_provider="local",
            capture_type="image",
            mime_type="image/jpeg",
            file_size_bytes=2048,
            checksum_sha256="def456",
            face_count=1,
            status=SelfieCaptureStatus.UPLOADED,
            captured_at=timezone.now() - timedelta(days=31),
        )

        cleaned = cleanup_retained_media_task(limit=10)

        identity_document.refresh_from_db()
        document_capture.refresh_from_db()
        selfie_capture.refresh_from_db()
        self.assertEqual(cleaned, 1)
        self.assertIsNone(identity_document.deleted_at)
        self.assertEqual(
            identity_document.extracted_data_json["full_name"], "Akosua Owusu"
        )
        self.assertEqual(document_capture.status, DocumentCaptureStatus.DELETED)
        self.assertIsNotNone(document_capture.deleted_at)
        self.assertEqual(selfie_capture.status, SelfieCaptureStatus.DELETED)
        self.assertIsNotNone(selfie_capture.deleted_at)
        self.assertTrue(
            AuditEvent.objects.filter(
                tenant=self.tenant,
                action="retention.media_deleted",
                target_id=verification.public_id,
            ).exists()
        )

        self.assertEqual(cleanup_retained_media_task(limit=10), 0)

    def test_cleanup_retained_media_task_respects_active_legal_hold(self):
        verification = Verification.objects.create(
            tenant=self.tenant,
            organization=self.organization,
            verification_subject=self.subject,
            purpose="Held verification",
            status=VerificationStatus.VERIFIED,
            policy_snapshot_json={"media_retention_days": 30},
            expires_at=timezone.now() - timedelta(days=31),
            completed_at=timezone.now() - timedelta(days=31),
        )
        RetentionLegalHold.objects.create(
            tenant=self.tenant,
            verification=verification,
            reason="Regulatory investigation",
        )

        self.assertEqual(cleanup_retained_media_task(limit=10), 0)
        self.assertTrue(
            AuditEvent.objects.filter(
                tenant=self.tenant,
                action="retention.media_deletion_deferred",
                target_id=verification.public_id,
            ).exists()
        )

    @patch("apps.verifications.tasks.delete_object")
    @patch(
        "apps.verifications.tasks.get_object_storage_media_bucket_name",
        return_value="media",
    )
    def test_cleanup_retained_media_task_keeps_db_row_when_storage_delete_fails(
        self, _bucket, delete_object
    ):
        verification = Verification.objects.create(
            tenant=self.tenant,
            organization=self.organization,
            verification_subject=self.subject,
            purpose="Storage failure",
            status=VerificationStatus.VERIFIED,
            policy_snapshot_json={"media_retention_days": 30},
            expires_at=timezone.now() - timedelta(days=31),
            completed_at=timezone.now() - timedelta(days=31),
        )
        identity_document = IdentityDocument.objects.create(
            tenant=self.tenant,
            verification=verification,
            verification_subject=self.subject,
            document_type_id="passport",
            country_profile_id="GH",
            status="processed",
        )
        capture = DocumentCapture.objects.create(
            tenant=self.tenant,
            identity_document=identity_document,
            side="front",
            storage_key="uploads/documents/storage-failure",
            captured_at=timezone.now() - timedelta(days=31),
        )
        delete_object.side_effect = RuntimeError("storage unavailable")

        self.assertEqual(cleanup_retained_media_task(limit=10), 0)
        capture.refresh_from_db()
        self.assertIsNone(capture.deleted_at)
        self.assertTrue(
            AuditEvent.objects.filter(
                tenant=self.tenant,
                action="retention.media_deletion_failed",
                target_id=verification.public_id,
            ).exists()
        )


class ManualReviewOwnershipTests(APITestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            name="Review Ownership", slug="review-ownership"
        )
        self.tenant = Tenant.objects.create(
            organization=self.organization,
            name="Review Ownership Tenant",
            slug="review-ownership-tenant",
            status="active",
        )
        self.tenant_reviewer = PlatformUser.objects.create_user(
            email="tenant-reviewer@example.com",
            password="StrongPassword123!",
            status=PlatformUserStatus.ACTIVE,
            tenant=self.tenant,
        )
        self.platform_reviewer = PlatformUser.objects.create_user(
            email="platform-reviewer@example.com",
            password="StrongPassword123!",
            status=PlatformUserStatus.ACTIVE,
            is_platform_admin=True,
        )
        self.tenant_case = self._create_case(
            "Tenant Case",
            metadata={},
        )
        self.platform_case = self._create_case(
            "Administrator Onboarding",
            metadata={"workflow": "administrator_onboarding"},
        )

    def _create_case(self, name, *, metadata):
        subject = VerificationSubject.objects.create(
            tenant=self.tenant,
            full_name=name,
            email=f"{name.lower().replace(' ', '-')}@example.com",
        )
        return Verification.objects.create(
            tenant=self.tenant,
            organization=self.organization,
            verification_subject=subject,
            purpose=name,
            status=VerificationStatus.MANUAL_REVIEW_REQUIRED,
            metadata_json=metadata,
            review_owner=(
                VerificationReviewOwner.PLATFORM
                if metadata.get("workflow") == "administrator_onboarding"
                else VerificationReviewOwner.TENANT
            ),
            expires_at=timezone.now() + timedelta(hours=1),
        )

    def test_tenant_queue_excludes_platform_owned_cases(self):
        self.client.force_authenticate(self.tenant_reviewer)

        response = self.client.get(reverse("manual-review-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            [item["verification_id"] for item in response.data["data"]["results"]],
            [self.tenant_case.public_id],
        )

    def test_platform_queue_contains_only_platform_owned_cases(self):
        self.client.force_authenticate(self.platform_reviewer)

        response = self.client.get(reverse("manual-review-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            [item["verification_id"] for item in response.data["data"]["results"]],
            [self.platform_case.public_id],
        )

    def test_tenant_reviewer_cannot_decide_platform_owned_case(self):
        self.client.force_authenticate(self.tenant_reviewer)

        response = self.client.post(
            reverse(
                "manual-review-decision",
                kwargs={"verification_id": self.platform_case.public_id},
            ),
            {
                "decision": VerificationStatus.VERIFIED,
                "reason_code": "evidence_confirmed",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.platform_case.refresh_from_db()
        self.assertEqual(
            self.platform_case.status,
            VerificationStatus.MANUAL_REVIEW_REQUIRED,
        )

    def test_platform_reviewer_cannot_decide_tenant_owned_case(self):
        self.client.force_authenticate(self.platform_reviewer)

        response = self.client.post(
            reverse(
                "manual-review-decision",
                kwargs={"verification_id": self.tenant_case.public_id},
            ),
            {
                "decision": VerificationStatus.VERIFIED,
                "reason_code": "evidence_confirmed",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.tenant_case.refresh_from_db()
        self.assertEqual(
            self.tenant_case.status,
            VerificationStatus.MANUAL_REVIEW_REQUIRED,
        )
