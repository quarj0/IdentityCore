import json

from django.db import connection
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from apps.organizations.models import Organization
from apps.providers.models import (
    Provider,
    ProviderCheck,
    ProviderCheckStatus,
    ProviderCheckType,
    ProviderType,
)
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
