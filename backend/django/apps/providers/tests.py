import json
import socket
from unittest.mock import Mock, patch
from urllib.error import HTTPError

from django.db import connection
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.utils import timezone

from apps.providers.ai_service import (
    AI_SERVICE_UNAVAILABLE_MESSAGE,
    AIServiceUnavailable,
    run_document_quality,
)
from apps.organizations.models import Organization
from apps.providers.models import (
    Provider,
    ProviderAssignment,
    ProviderCheck,
    ProviderCheckStatus,
    ProviderCheckType,
    ProviderType,
)
from apps.providers.services import create_provider_check
from apps.tenants.models import Tenant
from apps.verification_subjects.models import VerificationSubject
from apps.verifications.models import Verification, VerificationStatus


class ProviderModelTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name="Acme", slug="acme")
        self.tenant = Tenant.objects.create(
            organization=self.organization,
            name="Acme Tenant",
            slug="acme-tenant",
            status="active",
        )
        self.subject = VerificationSubject.objects.create(
            tenant=self.tenant,
            full_name="Kwame Mensah",
        )
        self.verification = Verification.objects.create(
            tenant=self.tenant,
            organization=self.organization,
            verification_subject=self.subject,
            purpose="Provider test",
            status=VerificationStatus.PROCESSING,
            expires_at=timezone.now(),
        )

    def test_create_provider_check_with_matching_provider_type(self):
        provider = Provider.objects.create(
            name="Internal Liveness Engine",
            code="internal-liveness",
            provider_type=ProviderType.LIVENESS,
        )

        check = ProviderCheck.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            provider=provider,
            check_type=ProviderCheckType.LIVENESS,
            status=ProviderCheckStatus.COMPLETED,
            started_at=timezone.now(),
            completed_at=timezone.now(),
            normalized_result_json={"status": "inconclusive"},
        )

        self.assertTrue(check.public_id.startswith("pck_"))

    def test_provider_configuration_is_encrypted_at_rest(self):
        provider = Provider.objects.create(
            name="SMTP Provider",
            code="smtp-provider",
            provider_type=ProviderType.NOTIFICATION,
            configuration_json={"api_key": "super-secret", "region": "eu-west-1"},
        )

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT configuration_json FROM providers_provider WHERE id = %s",
                [provider.id],
            )
            raw_value = cursor.fetchone()[0]

        if isinstance(raw_value, str):
            raw_value = json.loads(raw_value)
        self.assertEqual(provider.configuration_json["api_key"], "super-secret")
        self.assertEqual(raw_value["__enc__"], "ic-field-v1")
        self.assertNotIn("super-secret", json.dumps(raw_value))

    def test_provider_check_rejects_mismatched_provider_type(self):
        provider = Provider.objects.create(
            name="Notification Gateway",
            code="notify-gateway",
            provider_type=ProviderType.NOTIFICATION,
        )

        with self.assertRaises(ValidationError) as exc:
            ProviderCheck.objects.create(
                tenant=self.tenant,
                verification=self.verification,
                provider=provider,
                check_type=ProviderCheckType.LIVENESS,
                status=ProviderCheckStatus.PENDING,
                started_at=timezone.now(),
            )

        self.assertIn("provider", exc.exception.message_dict)

    def test_completed_provider_check_requires_timestamp(self):
        provider = Provider.objects.create(
            name="Internal Face Match Engine",
            code="internal-face-match",
            provider_type=ProviderType.BIOMETRIC,
        )

        with self.assertRaises(ValidationError) as exc:
            ProviderCheck.objects.create(
                tenant=self.tenant,
                verification=self.verification,
                provider=provider,
                check_type=ProviderCheckType.FACE_MATCH,
                status=ProviderCheckStatus.COMPLETED,
                started_at=timezone.now(),
            )

        self.assertIn("completed_at", exc.exception.message_dict)

    def test_failed_provider_check_allows_completion_timestamp(self):
        provider = Provider.objects.create(
            name="Internal Face Match Engine",
            code="internal-face-match-failed",
            provider_type=ProviderType.BIOMETRIC,
        )

        check = ProviderCheck.objects.create(
            tenant=self.tenant,
            verification=self.verification,
            provider=provider,
            check_type=ProviderCheckType.FACE_MATCH,
            status=ProviderCheckStatus.FAILED,
            started_at=timezone.now(),
            completed_at=timezone.now(),
            error_code="provider_unavailable",
        )

        self.assertEqual(check.status, ProviderCheckStatus.FAILED)

    def test_tenant_assignment_routes_provider_checks_to_byo_provider(self):
        tenant_provider = Provider.objects.create(
            tenant=self.tenant,
            name="Tenant OCR Engine",
            code="tenant-ocr-engine",
            provider_type=ProviderType.DOCUMENT,
        )
        ProviderAssignment.objects.create(
            tenant=self.tenant,
            assignment_key=ProviderCheckType.DOCUMENT_OCR,
            provider=tenant_provider,
        )

        check = create_provider_check(
            verification=self.verification,
            check_type=ProviderCheckType.DOCUMENT_OCR,
            status=ProviderCheckStatus.COMPLETED,
            normalized_result={"status": "completed"},
        )

        self.assertEqual(check.provider_id, tenant_provider.id)


class AIServiceClientTests(TestCase):
    @override_settings(
        AI_SERVICE_BASE_URL="http://ai-service:8001",
        AI_SERVICE_TIMEOUT_SECONDS=1,
        AI_SERVICE_SHARED_TOKEN="shared-token",
    )
    @patch("apps.providers.ai_service.request.urlopen")
    def test_http_error_returns_human_ready_unavailable_error(self, mock_urlopen):
        mock_urlopen.side_effect = HTTPError(
            url="http://ai-service:8001/v1/document/quality",
            code=503,
            msg="Service Unavailable",
            hdrs=None,
            fp=Mock(read=Mock(return_value=b'{"detail":"models missing"}')),
        )

        with self.assertRaises(AIServiceUnavailable) as exc:
            run_document_quality(
                verification_id="ver_123",
                document_storage_key="documents/front.jpg",
            )

        self.assertEqual(str(exc.exception), AI_SERVICE_UNAVAILABLE_MESSAGE)
        self.assertEqual(exc.exception.error_code, "provider_http_503")
        self.assertEqual(exc.exception.reason, "models missing")

    @override_settings(AI_SERVICE_BASE_URL="http://ai-service:8001")
    @patch("apps.providers.ai_service.request.urlopen")
    def test_invalid_json_returns_human_ready_unavailable_error(self, mock_urlopen):
        response = Mock()
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        response.read.return_value = b"InvalidTag"
        mock_urlopen.return_value = response

        with self.assertRaises(AIServiceUnavailable) as exc:
            run_document_quality(
                verification_id="ver_123",
                document_storage_key="documents/front.jpg",
            )

        self.assertEqual(str(exc.exception), AI_SERVICE_UNAVAILABLE_MESSAGE)
        self.assertEqual(exc.exception.error_code, "provider_invalid_response")

    @override_settings(AI_SERVICE_BASE_URL="http://ai-service:8001")
    @patch("apps.providers.ai_service.request.urlopen")
    def test_timeout_returns_timeout_provider_status(self, mock_urlopen):
        mock_urlopen.side_effect = socket.timeout("timed out")

        with self.assertRaises(AIServiceUnavailable) as exc:
            run_document_quality(
                verification_id="ver_123",
                document_storage_key="documents/front.jpg",
            )

        self.assertEqual(str(exc.exception), AI_SERVICE_UNAVAILABLE_MESSAGE)
        self.assertEqual(exc.exception.error_code, "provider_timeout")
        self.assertEqual(exc.exception.provider_check_status, "timeout")
