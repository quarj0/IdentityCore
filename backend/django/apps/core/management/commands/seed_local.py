from datetime import datetime, timezone as datetime_timezone
from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.access_control.models import Role, RoleScope, UserRole
from apps.accounts.models import PlatformUser, PlatformUserStatus
from apps.consent.models import ConsentTemplate, ConsentTemplateStatus
from apps.organizations.models import Organization, OrganizationStatus
from apps.projects.models import Project, ProjectEnvironment, ProjectStatus
from apps.tenants.models import Tenant, TenantStatus
from apps.verification_policies.models import (
    VerificationPolicy,
    VerificationPolicyStatus,
)
from apps.verification_subjects.models import VerificationSubject
from apps.verifications.models import (
    Verification,
    VerificationDecision,
    VerificationDecisionType,
    VerificationStatus,
)


SEED_PASSWORD = "IdentityCoreLocal123!"
FUTURE_EXPIRY = datetime(2099, 1, 1, tzinfo=datetime_timezone.utc)
PAST_EXPIRY = datetime(2020, 1, 1, tzinfo=datetime_timezone.utc)


class Command(BaseCommand):
    help = "Create deterministic development-only tenants, users, policies, and cases."

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("seed_local is restricted to DEBUG development settings.")

        with transaction.atomic():
            primary = self._seed_tenant(
                slug="acme-identity-lab",
                name="Acme Identity Lab",
                owner_email="owner@local.identitycore.test",
                reviewer_email="reviewer@local.identitycore.test",
            )
            self._seed_tenant(
                slug="northstar-sandbox",
                name="Northstar Sandbox",
                owner_email="northstar@local.identitycore.test",
            )
            self._seed_verification_cases(**primary)

        self.stdout.write(self.style.SUCCESS("Local IdentityCore data is ready."))
        self.stdout.write("Dashboard: http://localhost:3001")
        self.stdout.write("Owner: owner@local.identitycore.test")
        self.stdout.write("Reviewer: reviewer@local.identitycore.test")
        self.stdout.write(f"Development-only password: {SEED_PASSWORD}")

    def _seed_tenant(
        self,
        *,
        slug: str,
        name: str,
        owner_email: str,
        reviewer_email: str | None = None,
    ) -> dict:
        organization, _ = Organization.objects.update_or_create(
            slug=slug,
            defaults={
                "name": name,
                "industry": "Technology",
                "status": OrganizationStatus.ACTIVE,
                "settings_json": {"seeded": True},
            },
        )
        tenant, _ = Tenant.objects.update_or_create(
            slug=slug,
            defaults={
                "organization": organization,
                "name": name,
                "status": TenantStatus.ACTIVE,
                "settings_json": {"seeded": True},
            },
        )
        owner = self._seed_user(
            tenant=tenant,
            email=owner_email,
            first_name="Local",
            last_name="Owner",
        )
        reviewer = (
            self._seed_user(
                tenant=tenant,
                email=reviewer_email,
                first_name="Local",
                last_name="Reviewer",
            )
            if reviewer_email
            else owner
        )

        for user, role_name in (
            (owner, "Organization Administrator"),
            (reviewer, "Verification Officer"),
        ):
            role, _ = Role.objects.update_or_create(
                tenant=tenant,
                name=role_name,
                defaults={
                    "description": "Development fixture role",
                    "scope": RoleScope.TENANT,
                    "status": "active",
                    "is_system_role": True,
                },
            )
            UserRole.objects.get_or_create(user=user, role=role, tenant=tenant)

        project, _ = Project.objects.update_or_create(
            tenant=tenant,
            slug="sandbox",
            defaults={
                "name": "Sandbox",
                "environment": ProjectEnvironment.SANDBOX,
                "status": ProjectStatus.ACTIVE,
                "allowed_origins_json": ["http://localhost:3001"],
                "is_default": True,
                "created_by": owner,
            },
        )
        consent, _ = ConsentTemplate.objects.update_or_create(
            tenant=tenant,
            name="Local verification consent",
            version=1,
            language="en",
            defaults={
                "content": "I consent to the processing of synthetic local-development identity data.",
                "status": ConsentTemplateStatus.ACTIVE,
                "created_by": owner,
            },
        )
        policy, _ = VerificationPolicy.objects.update_or_create(
            tenant=tenant,
            name="Local standard verification",
            version=1,
            defaults={
                "project": project,
                "description": "Deterministic development policy for local UI states.",
                "consent_template": consent,
                "default_locale": "en",
                "supported_locales_json": ["en", "ar"],
                "status": VerificationPolicyStatus.ACTIVE,
                "required_document_types_json": ["passport", "national_id"],
                "required_liveness_level": "passive",
                "face_match_threshold": Decimal("0.8500"),
                "manual_review_threshold": Decimal("0.6500"),
                "verification_expiry_minutes": 1440,
                "media_retention_days": 30,
                "metadata_retention_days": 365,
                "created_by": owner,
            },
        )
        return {
            "organization": organization,
            "tenant": tenant,
            "project": project,
            "owner": owner,
            "reviewer": reviewer,
            "policy": policy,
        }

    def _seed_user(self, *, tenant, email: str, first_name: str, last_name: str):
        user = PlatformUser.objects.filter(email=email).first()
        if user is None:
            return PlatformUser.objects.create_user(
                email=email,
                password=SEED_PASSWORD,
                tenant=tenant,
                first_name=first_name,
                last_name=last_name,
                status=PlatformUserStatus.ACTIVE,
            )

        user.tenant = tenant
        user.first_name = first_name
        user.last_name = last_name
        user.status = PlatformUserStatus.ACTIVE
        user.is_staff = False
        user.is_platform_admin = False
        user.set_password(SEED_PASSWORD)
        user.save()
        return user

    def _seed_verification_cases(
        self, *, organization, tenant, project, owner, reviewer, policy
    ) -> None:
        terminal_statuses = {
            VerificationStatus.VERIFIED,
            VerificationStatus.REJECTED,
            VerificationStatus.EXPIRED,
            VerificationStatus.CANCELLED,
            VerificationStatus.FAILED,
        }
        decision_statuses = {
            VerificationStatus.VERIFIED,
            VerificationStatus.REJECTED,
        }
        for index, status in enumerate(VerificationStatus.values, start=1):
            subject, _ = VerificationSubject.objects.update_or_create(
                tenant=tenant,
                external_reference=f"local-subject-{status}",
                defaults={
                    "full_name": f"Local {status.replace('_', ' ').title()}",
                    "email": f"case-{status}@local.identitycore.test",
                    "metadata_json": {"seeded": True, "scenario": status},
                },
            )
            defaults = {
                "project": project,
                "organization": organization,
                "verification_subject": subject,
                "policy_public_id": policy.public_id,
                "policy_snapshot_json": policy.snapshot(),
                "workflow_snapshot_json": {
                    "version": 1,
                    "steps": ["consent", "document", "liveness", "decision"],
                },
                "status": status,
                "purpose": "Local development verification",
                "metadata_json": {"seeded": True, "scenario": status},
                "expires_at": (
                    PAST_EXPIRY if status == VerificationStatus.EXPIRED else FUTURE_EXPIRY
                ),
                "completed_at": PAST_EXPIRY if status in terminal_statuses else None,
                "cancelled_at": (
                    PAST_EXPIRY if status == VerificationStatus.CANCELLED else None
                ),
                "assigned_reviewer": (
                    reviewer
                    if status == VerificationStatus.MANUAL_REVIEW_REQUIRED
                    else None
                ),
                "created_by": owner,
            }
            verification, _ = Verification.objects.update_or_create(
                tenant=tenant,
                external_reference=f"local-case-{index:02d}-{status}",
                defaults=defaults,
            )
            if status in decision_statuses:
                VerificationDecision.objects.update_or_create(
                    verification=verification,
                    defaults={
                        "tenant": tenant,
                        "decision": status,
                        "decision_type": VerificationDecisionType.AUTOMATIC,
                        "reason_code": f"local_{status}",
                        "reason_codes_json": [f"local_{status}"],
                        "input_snapshot_json": {"seeded": True},
                        "evidence_summary_json": {"synthetic": True},
                        "decided_at": PAST_EXPIRY,
                    },
                )
            else:
                VerificationDecision.objects.filter(verification=verification).delete()
