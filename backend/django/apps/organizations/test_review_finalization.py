from django.core.exceptions import ValidationError
from django.test import TestCase
from apps.accounts.models import PlatformUser
from apps.access_control.models import UserRole
from apps.audit.models import AuditEvent
from apps.organizations.models import Organization, OrganizationSupportingDocument
from apps.organizations.onboarding import (
    submit_organization_verification,
    review_organization_onboarding,
)
from apps.tenants.models import Tenant
from config.graphql_auth import ensure_platform_role


class OrganizationReviewFinalizationTests(TestCase):
    def setUp(self):
        self.organization = Organization.objects.create(
            name="Synthetic organization", slug="synthetic-review"
        )
        self.tenant = Tenant.objects.create(
            organization=self.organization, name="Synthetic", slug="synthetic-review"
        )
        self.user = PlatformUser.objects.create_user(
            email="synthetic@organization.test",
            password="StrongPassword123!",
            tenant=self.tenant,
            status="active",
        )
        self.actor = PlatformUser.objects.create_superuser(
            email="reviewer@example.test",
            password="StrongPassword123!",
            status="active",
        )
        role = ensure_platform_role(name="Platform Admin")
        UserRole.objects.create(user=self.actor, role=role, tenant=None)
        self.document = OrganizationSupportingDocument.objects.create(
            organization=self.organization,
            tenant=self.tenant,
            uploaded_by=self.user,
            filename="synthetic.pdf",
            file_size_bytes=14,
            storage_key="synthetic/document.pdf",
            status="uploaded",
        )

    def submit(self, number="SYNTHETIC-1"):
        return submit_organization_verification(
            user=self.user,
            business_registration_number=number,
            registered_address="Synthetic address",
            supporting_document_keys=[self.document.storage_key],
        )

    def review(self, decision):
        return review_organization_onboarding(
            organization=self.organization,
            actor=self.actor,
            decision=decision,
            note="Synthetic reviewer rationale",
        )

    def test_closed_review_cannot_be_redecided_from_stale_organization(self):
        self.submit()
        self.review("approved")
        before = AuditEvent.objects.count()
        for decision in ["approved", "rejected", "needs_information"]:
            with self.subTest(decision=decision), self.assertRaises(ValidationError):
                self.review(decision)
        self.organization.refresh_from_db()
        self.assertEqual(self.organization.status, "active")
        self.assertEqual(AuditEvent.objects.count(), before)

    def test_updated_evidence_reopens_review_through_submission_only(self):
        self.submit()
        self.review("needs_information")
        with self.assertRaises(ValidationError):
            self.review("approved")
        self.submit("SYNTHETIC-2")
        self.review("approved")
        self.organization.refresh_from_db()
        self.assertEqual(self.organization.status, "active")

    def test_draft_and_revoked_reviewer_cannot_finalize(self):
        with self.assertRaises(ValidationError):
            self.review("approved")
        self.submit()
        PlatformUser.objects.filter(pk=self.actor.pk).update(status="inactive")
        with self.assertRaises(ValidationError):
            self.review("approved")
