from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import PlatformUser, PlatformUserStatus
from apps.organizations.models import Organization
from apps.tenants.models import Tenant
from apps.audit.models import AuditEvent
from apps.identity_documents.models import IdentityDocument
from apps.verification_subjects.models import (
    VerificationSubject,
    VerificationSubjectExport,
)
from apps.verifications.models import (
    RetentionLegalHold,
    Verification,
    VerificationStatus,
)
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
        from apps.access_control.models import (
            Permission,
            Role,
            RolePermission,
            UserRole,
        )

        permission, _ = Permission.objects.get_or_create(
            code="manage_subject_privacy", defaults={"name": "Manage subject privacy"}
        )
        role = Role.objects.create(
            tenant=self.tenant, name="Privacy operator", scope="tenant"
        )
        RolePermission.objects.create(role=role, permission=permission)
        UserRole.objects.create(user=self.user, role=role, tenant=self.tenant)
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

    def test_subject_export_requires_tenant_authorization_and_redacts_sensitive_data(
        self,
    ):
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
            AuditEvent.objects.filter(
                action="privacy.subject_export_downloaded"
            ).exists()
        )

    def test_subject_export_token_expires(self):
        subject = VerificationSubject.objects.create(
            tenant=self.tenant, full_name="Expired"
        )
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

    def test_membership_without_privacy_grant_cannot_delete_or_export(self):
        from apps.access_control.models import UserRole

        UserRole.objects.filter(user=self.user).delete()
        subject = VerificationSubject.objects.create(
            tenant=self.tenant, full_name="Protected"
        )
        for action in ("delete", "export"):
            with self.subTest(action=action):
                response = self.client.post(
                    f"/api/v1/subjects/{subject.public_id}",
                    {"action": action, "confirm": True},
                    format="json",
                )
                self.assertEqual(response.status_code, 403)
        subject.refresh_from_db()
        self.assertIsNone(subject.deleted_at)
        self.assertFalse(
            VerificationSubjectExport.objects.filter(subject=subject).exists()
        )

    def test_deletion_revokes_sessions_jobs_and_scrubs_copied_personal_data(self):
        from apps.consent.test_helpers import accept_test_consent
        from apps.consent.services import active_consent
        from apps.verifications.models import VerificationSession, ProcessingJob
        from apps.verifications.processing_jobs import (
            lock_processing_job_for_finalization,
            ProcessingJobOwnershipLost,
        )
        from apps.providers.services import create_provider_check
        from django.db import transaction

        subject = VerificationSubject.objects.create(
            tenant=self.tenant, full_name="Private", email="private@example.test"
        )
        case = Verification.objects.create(
            tenant=self.tenant,
            organization=self.organization,
            verification_subject=subject,
            purpose="Synthetic privacy",
            external_reference="private-reference",
            metadata_json={
                "personal": "private",
                "evidence_report_storage_key": "opaque/report.json",
                "evidence_report_pdf_storage_key": "opaque/report.pdf",
            },
            expires_at=timezone.now() + timedelta(hours=1),
            status="pending_consent",
        )
        accept_test_consent(case)
        session = VerificationSession(
            tenant=self.tenant,
            verification=case,
            expires_at=case.expires_at,
            allowed_actions_json=["session:read"],
        )
        session.set_session_token("synthetic-privacy-session")
        session.save()
        job = ProcessingJob.objects.create(
            tenant=self.tenant,
            verification=case,
            job_type="identity_document",
            resource_public_id="synthetic-document",
            status="processing",
            attempt_count=1,
            lease_expires_at=case.expires_at,
        )
        check = create_provider_check(
            verification=case,
            check_type="document_ocr",
            status="completed",
            response_metadata={"full_name": "Private"},
            normalized_result={"ocr": {"full_name": "Private"}},
        )
        export = VerificationSubjectExport(
            tenant=self.tenant,
            subject=subject,
            payload_json={"email": subject.email},
            expires_at=case.expires_at,
        )
        export.set_download_token("synthetic-private-export")
        export.save()
        response = self.client.post(
            f"/api/v1/subjects/{subject.public_id}",
            {"action": "delete", "confirm": True},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        for obj in (subject, case, session, job, check, export):
            obj.refresh_from_db()
        self.assertEqual(case.status, "cancelled")
        self.assertEqual(case.external_reference, "")
        self.assertEqual(
            case.metadata_json,
            {
                "evidence_report_storage_key": "opaque/report.json",
                "evidence_report_pdf_storage_key": "opaque/report.pdf",
            },
        )
        self.assertEqual(session.status, "revoked")
        self.assertEqual(job.status, "exhausted")
        self.assertEqual(job.error_code, "subject_deleted")
        self.assertEqual(check.response_metadata_json, {})
        self.assertEqual(check.normalized_result_json, {})
        self.assertEqual(export.payload_json, {})
        self.assertTrue(export.is_expired)
        self.assertIsNone(active_consent(case, "document"))
        with transaction.atomic(), self.assertRaises(ProcessingJobOwnershipLost):
            lock_processing_job_for_finalization(job)
        from rest_framework.test import APIClient

        portal = APIClient()
        denied = portal.get(
            f"/api/v1/sessions/{session.public_id}",
            HTTP_AUTHORIZATION="Bearer synthetic-privacy-session",
            HTTP_X_SESSION_ID=session.public_id,
        )
        self.assertEqual(denied.status_code, 401)

    def test_service_rechecks_revoked_privacy_grant(self):
        from apps.access_control.models import UserRole
        from rest_framework.exceptions import PermissionDenied

        subject = VerificationSubject.objects.create(
            tenant=self.tenant, full_name="Protected"
        )
        UserRole.objects.filter(user=self.user).delete()
        with self.assertRaises(PermissionDenied):
            request_subject_deletion(subject=subject, actor=self.user)
        subject.refresh_from_db()
        self.assertIsNone(subject.deleted_at)

    def test_cached_subject_cannot_create_an_export_after_deletion(self):
        from apps.verification_subjects.services import create_subject_export
        from rest_framework.exceptions import NotFound

        subject = VerificationSubject.objects.create(
            tenant=self.tenant, full_name="Private", email="private@example.test"
        )
        stale = VerificationSubject.objects.get(pk=subject.pk)
        request_subject_deletion(subject=subject, actor=self.user)
        with self.assertRaises(NotFound):
            create_subject_export(subject=stale, actor=self.user)
        self.assertFalse(
            VerificationSubjectExport.objects.filter(subject=subject).exists()
        )


class SubjectPrivacyPermissionMigrationTests(TestCase):
    def test_only_designated_system_administrators_receive_migrated_privacy_grant(self):
        from django.apps import apps
        from importlib import import_module
        from apps.access_control.models import Role

        org = Organization.objects.create(name="Migration", slug="privacy-grants")
        tenant = Tenant.objects.create(
            organization=org, name="Migration", slug="privacy-grants"
        )
        admin = Role.objects.create(
            tenant=tenant,
            name="Tenant Administrator",
            scope="tenant",
            is_system_role=True,
        )
        reviewer = Role.objects.create(
            tenant=tenant,
            name="Verification Officer",
            scope="tenant",
            is_system_role=True,
        )
        custom = Role.objects.create(
            tenant=tenant, name="Privacy Custom", scope="tenant", is_system_role=False
        )
        platform = Role.objects.create(
            name="Organization Administrator", scope="platform", is_system_role=True
        )
        grant = import_module(
            "apps.access_control.migrations.0008_manage_subject_privacy_permission"
        ).grant
        grant(apps, None)
        grant(apps, None)
        self.assertTrue(
            admin.role_permissions.filter(
                permission__code="manage_subject_privacy"
            ).exists()
        )
        for role in (reviewer, custom, platform):
            self.assertFalse(
                role.role_permissions.filter(
                    permission__code="manage_subject_privacy"
                ).exists()
            )
