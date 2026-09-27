from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import PlatformUser, PlatformUserStatus
from apps.organizations.models import Organization
from apps.tenants.models import Tenant
from apps.verification_subjects.models import VerificationSubject
from apps.verifications.models import Verification, VerificationStatus


class ProductMetricsViewTests(APITestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            name="Metrics Example",
            slug="metrics-example",
        )
        self.tenant = Tenant.objects.create(
            organization=self.organization,
            name="Metrics Tenant",
            slug="metrics-tenant",
            status="active",
        )
        self.user = PlatformUser.objects.create_user(
            email="metrics-admin@example.test",
            password="StrongPassword123!",
            status=PlatformUserStatus.ACTIVE,
            tenant=self.tenant,
        )
        self.subject = VerificationSubject.objects.create(
            tenant=self.tenant,
            full_name="Synthetic Applicant",
            email="synthetic@example.test",
        )
        self.client.force_authenticate(self.user)
        self.url = reverse("tenant-product-metrics")

    def create_verification(self, status_value, *, completed=False):
        now = timezone.now()
        return Verification.objects.create(
            tenant=self.tenant,
            organization=self.organization,
            verification_subject=self.subject,
            purpose="Synthetic analytics fixture",
            status=status_value,
            expires_at=now + timedelta(days=1),
            completed_at=now if completed else None,
        )

    def test_small_cohort_is_suppressed_without_identifiers(self):
        self.create_verification(VerificationStatus.VERIFIED, completed=True)
        self.create_verification(VerificationStatus.EXPIRED)

        response = self.client.get(self.url)
        metrics = response.data["data"]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(metrics["suppressed"])
        self.assertIsNone(metrics["cohort_size"])
        self.assertIsNone(metrics["completed_count"])
        self.assertEqual(metrics["failure_reason_counts"], [])
        self.assertNotIn("Synthetic Applicant", str(response.data))
        self.assertNotIn("synthetic@example.test", str(response.data))

    def test_tenant_scope_and_small_bucket_suppression(self):
        for _ in range(9):
            self.create_verification(VerificationStatus.VERIFIED, completed=True)

        other_org = Organization.objects.create(
            name="Other Metrics Example",
            slug="other-metrics-example",
        )
        other_tenant = Tenant.objects.create(
            organization=other_org,
            name="Other Metrics Tenant",
            slug="other-metrics-tenant",
            status="active",
        )
        other_subject = VerificationSubject.objects.create(
            tenant=other_tenant,
            full_name="Other Applicant",
            email="other@example.test",
        )
        now = timezone.now()
        for _ in range(20):
            Verification.objects.create(
                tenant=other_tenant,
                organization=other_org,
                verification_subject=other_subject,
                purpose="Other synthetic fixture",
                status=VerificationStatus.VERIFIED,
                expires_at=now + timedelta(days=1),
                completed_at=now,
            )

        metrics = self.client.get(self.url).data["data"]

        self.assertTrue(metrics["suppressed"])
        self.assertIsNone(metrics["cohort_size"])
        self.assertNotIn("Other Applicant", str(metrics))

    def test_metrics_are_aggregated_after_minimum_cohort(self):
        for _ in range(10):
            self.create_verification(VerificationStatus.VERIFIED, completed=True)

        metrics = self.client.get(self.url).data["data"]

        self.assertFalse(metrics["suppressed"])
        self.assertEqual(metrics["cohort_size"], 10)
        self.assertEqual(metrics["completed_count"], 10)
        self.assertEqual(metrics["completion_rate"], 1.0)
        self.assertIsNotNone(metrics["average_completion_latency_seconds"])

    def test_tenant_can_opt_out_and_metrics_are_disabled(self):
        response = self.client.patch(
            self.url,
            {"product_metrics_opt_out": True},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["data"]["product_metrics_opt_out"])

        metrics = self.client.get(self.url).data["data"]
        self.assertEqual(metrics, {"status": "disabled", "reason": "tenant_opt_out"})

    def test_invalid_window_is_rejected(self):
        response = self.client.get(self.url, {"days": "365"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
