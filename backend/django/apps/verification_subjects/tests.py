from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import PlatformUser, PlatformUserStatus
from apps.organizations.models import Organization
from apps.tenants.models import Tenant
from apps.audit.models import AuditEvent
from apps.identity_documents.models import IdentityDocument
from apps.verification_subjects.models import VerificationSubject, VerificationSubjectExport
from apps.verifications.models import RetentionLegalHold, Verification, VerificationStatus
from apps.verification_subjects.services import request_subject_deletion
from django.utils import timezone
from datetime import timedelta


class VerificationSubjectModelTests(TestCase):
    def test_generates_prefixed_public_id(self):
        organization = Organization.objects.create(name="Acme", slug="acme")
        tenant = Tenant.objects.create(
            organization=organization,
            name="Acme Tenant",
            slug="acme-tenant",
            status="active",
        )
        subject = VerificationSubject.objects.create(
            tenant=tenant,
            external_reference="customer_123",
            full_name="Kwame Mensah",
        )

        self.assertTrue(subject.public_id.startswith("sub_"))


class VerificationSubjectAPITests(APITestCase):
    def setUp(self):
        self.organization = Organization.objects.create(name="Acme", slug="acme-api")
        self.tenant = Tenant.objects.create(
            organization=self.organization,
            name="Acme API Tenant",
            slug="acme-api-tenant",
            status="active",
        )
        self.user = PlatformUser.objects.create_user(
            email="subjects@example.com",
            password="StrongPassword123!",
            status=PlatformUserStatus.ACTIVE,
            tenant=self.tenant,
        )
        self.client.force_authenticate(self.user)

    def test_lists_tenant_subjects(self):
        subject = VerificationSubject.objects.create(
            tenant=self.tenant,
            external_reference="customer_123",
            full_name="Kwame Mensah",
            email="kwame@example.com",
        )

        response = self.client.get("/api/v1/subjects/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["results"][0]["id"], subject.public_id)
        self.assertEqual(response.data["data"]["pagination"]["total"], 1)

    def test_subject_deletion_anonymizes_profile_and_reports_retained_facts(self):
        subject = VerificationSubject.objects.create(
            tenant=self.tenant,
            external_reference="customer_123",
            full_name="Kwame Mensah",
            email="kwame@example.com",
            phone_number="+233200000000",
            metadata_json={"sensitive": "value"},
        )
        verification = Verification.objects.create(
            tenant=self.tenant,
            organization=self.organization,
            verification_subject=subject,
            purpose="Account opening",
            status=VerificationStatus.VERIFIED,
            expires_at=timezone.now() + timedelta(hours=1),
        )
        IdentityDocument.objects.create(
            tenant=self.tenant,
            verification=verification,
            verification_subject=subject,
            document_type_id="passport",
            document_number_hash="hashed-number",
            extracted_data_json={"full_name": "Kwame Mensah"},
        )

        response = self.client.post(
            f"/api/v1/subjects/{subject.public_id}",
            {"action": "delete", "confirm": True},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["status"], "completed")
        subject.refresh_from_db()
        verification.refresh_from_db()
        self.assertEqual(subject.full_name, "Deleted subject")
        self.assertEqual(subject.email, "")
        self.assertIsNotNone(subject.deleted_at)
        self.assertEqual(verification.metadata_json, {})
        self.assertTrue(
            AuditEvent.objects.filter(
                action="privacy.subject_deletion_completed",
                target_id=subject.public_id,
            ).exists()
        )

    def test_subject_deletion_is_deferred_by_legal_hold(self):
        subject = VerificationSubject.objects.create(
            tenant=self.tenant,
            full_name="Held Subject",
            email="held@example.com",
        )
        RetentionLegalHold.objects.create(
            tenant=self.tenant,
            reason="Litigation hold",
        )

        response = self.client.post(
            f"/api/v1/subjects/{subject.public_id}",
            {"action": "delete", "confirm": True},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["status"], "deferred")
        subject.refresh_from_db()
        self.assertEqual(subject.full_name, "Held Subject")

    def test_subject_export_requires_tenant_authorization_and_redacts_sensitive_data(self):
        subject = VerificationSubject.objects.create(
            tenant=self.tenant,
            full_name="Kwame Mensah",
            email="kwame@example.com",
            metadata_json={"internal_note": "do not export"},
        )
        response = self.client.post(
            f"/api/v1/subjects/{subject.public_id}",
            {"action": "export"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        export_id = response.data["data"]["export_id"]
        token = response.data["data"]["download_token"]
        download = self.client.get(
            f"/api/v1/subjects/exports/{export_id}", {"token": token}
        )
        self.assertEqual(download.status_code, status.HTTP_200_OK)
        self.assertEqual(download.data["data"]["subject"]["email"], "kwame@example.com")
        self.assertNotIn("internal_note", download.data["data"]["subject"]["metadata"])
        self.assertIn("raw document/selfie media", download.data["data"]["redactions"])
        self.assertTrue(
            AuditEvent.objects.filter(action="privacy.subject_export_created").exists()
        )
        self.assertTrue(
            AuditEvent.objects.filter(action="privacy.subject_export_downloaded").exists()
        )

    def test_subject_export_token_expires(self):
        subject = VerificationSubject.objects.create(tenant=self.tenant, full_name="Expired")
        export = VerificationSubjectExport.objects.create(
            tenant=self.tenant,
            subject=subject,
            payload_json={"subject": {"id": subject.public_id}},
            download_token_hash="not-a-valid-hash",
            expires_at=timezone.now() - timedelta(minutes=1),
        )
        response = self.client.get(
            f"/api/v1/subjects/exports/{export.public_id}", {"token": "anything"}
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
