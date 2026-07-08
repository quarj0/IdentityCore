from __future__ import annotations

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify
from django_countries import countries

from apps.access_control.models import Role, RoleScope, UserRole
from apps.accounts.models import PlatformUser, PlatformUserStatus
from apps.accounts.verification import issue_and_queue_email_verification
from apps.audit.services import record_audit_event
from apps.organizations.models import Organization, OrganizationStatus
from apps.tenants.models import Tenant, TenantStatus
from common.validators import normalize_email, validate_business_email

ORGANIZATION_TYPE_CHOICES = (
    "government",
    "financial_institution",
    "educational_institution",
    "healthcare_provider",
    "enterprise",
    "ngo",
    "startup",
    "other",
)

ORGANIZATION_TIER_TRIAL = "trial"
ORGANIZATION_TIER_VERIFIED = "verified"
ORGANIZATION_TIER_TRUSTED = "trusted"
ORGANIZATION_TIER_ENTERPRISE = "enterprise"

ONBOARDING_STATUS_EMAIL_VERIFICATION_PENDING = "email_verification_pending"
ONBOARDING_STATUS_ORGANIZATION_VERIFICATION_REQUIRED = (
    "organization_verification_required"
)
ONBOARDING_STATUS_ADMIN_IDENTITY_VERIFICATION_REQUIRED = (
    "administrator_identity_verification_required"
)
ONBOARDING_STATUS_PLATFORM_REVIEW_PENDING = "platform_review_pending"
ONBOARDING_STATUS_ACTIVE = "active"
ONBOARDING_STATUS_NEEDS_INFORMATION = "needs_information"
ONBOARDING_STATUS_REJECTED = "rejected"


def split_full_name(full_name: str) -> tuple[str, str]:
    parts = full_name.strip().split(maxsplit=1)
    first_name = parts[0] if parts else ""
    last_name = parts[1] if len(parts) > 1 else ""
    return first_name, last_name


def generate_unique_slug(model, raw_value: str) -> str:
    base_slug = slugify(raw_value).strip("-") or "organization"
    candidate = base_slug
    suffix = 2
    while model.objects.filter(slug=candidate).exists():
        candidate = f"{base_slug}-{suffix}"
        suffix += 1
    return candidate


def _normalize_country_code(country_code: str) -> str:
    normalized = (country_code or "").strip().upper()
    if not normalized:
        raise ValidationError("Organization country is required.")
    if normalized not in countries:
        raise ValidationError("Unsupported organization country.")
    return normalized


def _validate_registration_fields(
    *,
    full_name: str,
    business_email: str,
    password: str,
    support_email: str,
    organization_name: str,
    organization_type: str,
    organization_country: str,
) -> tuple[str, str, str]:
    if not full_name.strip():
        raise ValidationError("Full name is required.")
    if not organization_name.strip():
        raise ValidationError("Organization name is required.")
    if organization_type not in ORGANIZATION_TYPE_CHOICES:
        raise ValidationError("Unsupported organization type.")
    business_email = validate_business_email(business_email)
    support_email = normalize_email(support_email)
    organization_country = _normalize_country_code(organization_country)
    validate_password(password)
    return business_email, support_email, organization_country


def _build_onboarding_settings(
    *,
    user: PlatformUser,
    organization_type: str,
    organization_country: str,
    website: str,
    support_email: str,
    phone_number: str,
) -> dict:
    now = timezone.now().isoformat()
    return {
        "tier": ORGANIZATION_TIER_TRIAL,
        "status": ONBOARDING_STATUS_EMAIL_VERIFICATION_PENDING,
        "current_step": "email_verification",
        "registered_at": now,
        "registration": {
            "organization_type": organization_type,
            "organization_country": organization_country.strip(),
            "website": website.strip(),
            "support_email": support_email,
            "phone_number": phone_number.strip(),
        },
        "primary_administrator": {
            "user_id": user.public_id,
            "full_name": f"{user.first_name} {user.last_name}".strip(),
            "business_email": user.email,
        },
        "email_verification": {
            "required": True,
            "verified_at": None,
        },
        "organization_verification": {
            "submitted_at": None,
            "business_registration_number": "",
            "tax_identification_number": "",
            "registered_address": "",
            "official_website": "",
            "supporting_document_keys": [],
        },
        "administrator_identity_verification": {
            "status": "pending",
            "verification_id": "",
            "submitted_at": None,
        },
        "platform_review": {
            "status": "not_started",
            "reviewed_at": None,
            "reviewed_by": "",
            "note": "",
        },
    }


def _get_onboarding_settings(organization: Organization) -> dict:
    settings_json = dict(organization.settings_json or {})
    return dict(settings_json.get("onboarding") or {})


def _save_onboarding_settings(
    organization: Organization, onboarding: dict
) -> Organization:
    settings_json = dict(organization.settings_json or {})
    settings_json["onboarding"] = onboarding
    organization.settings_json = settings_json
    organization.save(update_fields=["settings_json", "updated_at"])
    return organization


def ensure_tenant_administrator_role(*, tenant: Tenant, user: PlatformUser) -> None:
    role, _ = Role.objects.get_or_create(
        tenant=tenant,
        name="Tenant Administrator",
        defaults={
            "description": "Default onboarding administrator role.",
            "scope": RoleScope.TENANT,
            "is_system_role": True,
        },
    )
    UserRole.objects.get_or_create(user=user, role=role, tenant=tenant)


@transaction.atomic
def register_organization_onboarding(
    *,
    full_name: str,
    business_email: str,
    password: str,
    organization_name: str,
    organization_type: str,
    organization_country: str,
    website: str = "",
    support_email: str,
    phone_number: str,
    request=None,
) -> tuple[Organization, Tenant, PlatformUser, str]:
    business_email, support_email, organization_country = _validate_registration_fields(
        full_name=full_name,
        business_email=business_email,
        password=password,
        support_email=support_email,
        organization_name=organization_name,
        organization_type=organization_type,
        organization_country=organization_country,
    )
    first_name, last_name = split_full_name(full_name)
    organization_slug = generate_unique_slug(Organization, organization_name)
    tenant_slug = generate_unique_slug(Tenant, f"{organization_name}-workspace")

    organization = Organization.objects.create(
        name=organization_name.strip(),
        slug=organization_slug,
        industry=organization_type,
        status=OrganizationStatus.PENDING_EMAIL_VERIFICATION,
    )
    tenant = Tenant.objects.create(
        organization=organization,
        name=f"{organization.name} Workspace",
        slug=tenant_slug,
        status=TenantStatus.PENDING,
    )
    user = PlatformUser.objects.create_user(
        email=business_email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        tenant=tenant,
        status=PlatformUserStatus.INACTIVE,
    )
    onboarding = _build_onboarding_settings(
        user=user,
        organization_type=organization_type,
        organization_country=organization_country,
        website=website,
        support_email=support_email,
        phone_number=phone_number,
    )
    _save_onboarding_settings(organization, onboarding)
    _, raw_verification_token = issue_and_queue_email_verification(user=user)
    record_audit_event(
        tenant=tenant,
        actor=user,
        request=request,
        action="onboarding.started",
        target_type="organization",
        target_id=organization.public_id,
        metadata={
            "organization_type": organization_type,
            "tier": onboarding["tier"],
            "organization_status": organization.status,
            "tenant_status": tenant.status,
        },
        sensitive_metadata={
            "business_email": user.email,
            "support_email": support_email,
            "phone_number": phone_number,
        },
    )
    return organization, tenant, user, raw_verification_token


def serialize_onboarding_state(
    *, organization: Organization, tenant: Tenant, user: PlatformUser
) -> dict:
    onboarding = _get_onboarding_settings(organization)
    registration = dict(onboarding.get("registration") or {})
    email_verification = dict(onboarding.get("email_verification") or {})
    organization_verification = dict(onboarding.get("organization_verification") or {})
    admin_identity = dict(onboarding.get("administrator_identity_verification") or {})
    platform_review = dict(onboarding.get("platform_review") or {})
    primary_admin = dict(onboarding.get("primary_administrator") or {})
    return {
        "organization_id": organization.public_id,
        "organization_name": organization.name,
        "organization_slug": organization.slug,
        "organization_type": registration.get(
            "organization_type", organization.industry
        ),
        "organization_country": registration.get("organization_country", ""),
        "organization_status": organization.status,
        "organization_tier": onboarding.get("tier", ORGANIZATION_TIER_TRIAL),
        "tenant_id": tenant.public_id,
        "tenant_slug": tenant.slug,
        "tenant_status": tenant.status,
        "administrator_user_id": user.public_id,
        "administrator_full_name": primary_admin.get(
            "full_name", f"{user.first_name} {user.last_name}".strip()
        ),
        "administrator_email": user.email,
        "administrator_country": primary_admin.get("country", ""),
        "administrator_status": user.status,
        "support_email": registration.get("support_email", ""),
        "phone_number": registration.get("phone_number", ""),
        "website": registration.get("website", ""),
        "requires_email_verification": bool(email_verification.get("required", True)),
        "email_verified_at": email_verification.get("verified_at"),
        "onboarding_status": onboarding.get(
            "status", ONBOARDING_STATUS_EMAIL_VERIFICATION_PENDING
        ),
        "current_step": onboarding.get("current_step", "email_verification"),
        "organization_verification_submitted_at": organization_verification.get(
            "submitted_at"
        ),
        "administrator_identity_verification_status": admin_identity.get(
            "status", "pending"
        ),
        "administrator_identity_verification_id": admin_identity.get(
            "verification_id", ""
        ),
        "administrator_identity_submitted_at": admin_identity.get("submitted_at"),
        "platform_review_status": platform_review.get("status", "not_started"),
        "platform_review_note": platform_review.get("note", ""),
        "platform_reviewed_at": platform_review.get("reviewed_at"),
    }


@transaction.atomic
def confirm_onboarding_email_verification(
    *, user: PlatformUser, actor: PlatformUser, request=None
) -> tuple[Organization, Tenant, PlatformUser]:
    tenant = user.tenant
    organization = tenant.organization
    onboarding = _get_onboarding_settings(organization)
    ensure_tenant_administrator_role(tenant=tenant, user=user)
    onboarding["email_verification"] = {
        "required": True,
        "verified_at": timezone.now().isoformat(),
    }
    onboarding["status"] = ONBOARDING_STATUS_ORGANIZATION_VERIFICATION_REQUIRED
    onboarding["current_step"] = "organization_verification"
    _save_onboarding_settings(organization, onboarding)
    user.status = PlatformUserStatus.ACTIVE
    user.save(update_fields=["status", "updated_at"])
    organization.status = OrganizationStatus.PENDING_REVIEW
    tenant.status = TenantStatus.PENDING_REVIEW
    organization.save(update_fields=["status", "updated_at"])
    tenant.save(update_fields=["status", "updated_at"])
    record_audit_event(
        tenant=tenant,
        actor=actor,
        request=request,
        action="onboarding.email_verified",
        target_type="platform_user",
        target_id=user.public_id,
        metadata={
            "organization_id": organization.public_id,
            "role_assigned": "Tenant Administrator",
        },
    )
    return organization, tenant, user


@transaction.atomic
def submit_organization_verification(
    *,
    user: PlatformUser,
    business_registration_number: str,
    registered_address: str,
    official_website: str = "",
    tax_identification_number: str = "",
    supporting_document_keys: list[str] | None = None,
    request=None,
) -> tuple[Organization, Tenant, PlatformUser]:
    if not business_registration_number.strip():
        raise ValidationError("Business registration number is required.")
    if not registered_address.strip():
        raise ValidationError("Registered address is required.")

    tenant = user.tenant
    organization = tenant.organization
    onboarding = _get_onboarding_settings(organization)
    onboarding["organization_verification"] = {
        "submitted_at": timezone.now().isoformat(),
        "business_registration_number": business_registration_number.strip(),
        "tax_identification_number": tax_identification_number.strip(),
        "registered_address": registered_address.strip(),
        "official_website": official_website.strip(),
        "supporting_document_keys": supporting_document_keys or [],
    }
    onboarding["status"] = ONBOARDING_STATUS_ADMIN_IDENTITY_VERIFICATION_REQUIRED
    onboarding["current_step"] = "administrator_identity_verification"
    _save_onboarding_settings(organization, onboarding)
    record_audit_event(
        tenant=tenant,
        actor=user,
        request=request,
        action="onboarding.organization_verification_submitted",
        target_type="organization",
        target_id=organization.public_id,
        metadata={
            "supporting_document_count": len(supporting_document_keys or []),
        },
        sensitive_metadata={
            "business_registration_number": business_registration_number,
            "tax_identification_number": tax_identification_number,
            "registered_address": registered_address,
        },
    )
    return organization, tenant, user


@transaction.atomic
def submit_administrator_identity_verification(
    *,
    user: PlatformUser,
    verification_id: str = "",
    request=None,
) -> tuple[Organization, Tenant, PlatformUser]:
    tenant = user.tenant
    organization = tenant.organization
    onboarding = _get_onboarding_settings(organization)
    onboarding["administrator_identity_verification"] = {
        "status": "submitted",
        "verification_id": verification_id.strip(),
        "submitted_at": timezone.now().isoformat(),
    }
    onboarding["status"] = ONBOARDING_STATUS_PLATFORM_REVIEW_PENDING
    onboarding["current_step"] = "platform_review"
    onboarding["platform_review"] = {
        "status": "pending_review",
        "reviewed_at": None,
        "reviewed_by": "",
        "note": "",
    }
    organization.status = OrganizationStatus.PENDING_REVIEW
    tenant.status = TenantStatus.PENDING_REVIEW
    organization.save(update_fields=["status", "updated_at"])
    tenant.save(update_fields=["status", "updated_at"])
    _save_onboarding_settings(organization, onboarding)
    record_audit_event(
        tenant=tenant,
        actor=user,
        request=request,
        action="onboarding.administrator_identity_submitted",
        target_type="organization",
        target_id=organization.public_id,
        metadata={"verification_id": verification_id.strip()},
    )
    return organization, tenant, user


@transaction.atomic
def review_organization_onboarding(
    *,
    organization: Organization,
    actor: PlatformUser,
    decision: str,
    note: str = "",
    request=None,
) -> tuple[Organization, Tenant, PlatformUser]:
    if decision not in {"approved", "rejected", "needs_information"}:
        raise ValidationError("Unsupported onboarding review decision.")

    tenant = organization.tenant
    user = tenant.platform_users.order_by("created_at").first()
    onboarding = _get_onboarding_settings(organization)
    onboarding["platform_review"] = {
        "status": decision,
        "reviewed_at": timezone.now().isoformat(),
        "reviewed_by": actor.public_id,
        "note": note.strip(),
    }

    if decision == "approved":
        organization.status = OrganizationStatus.ACTIVE
        tenant.status = TenantStatus.ACTIVE
        onboarding["tier"] = ORGANIZATION_TIER_VERIFIED
        onboarding["status"] = ONBOARDING_STATUS_ACTIVE
        onboarding["current_step"] = "active"
        if user is not None and user.status == PlatformUserStatus.INACTIVE:
            user.status = PlatformUserStatus.ACTIVE
            user.save(update_fields=["status", "updated_at"])
    elif decision == "needs_information":
        organization.status = OrganizationStatus.PENDING_REVIEW
        tenant.status = TenantStatus.PENDING_REVIEW
        onboarding["status"] = ONBOARDING_STATUS_NEEDS_INFORMATION
        onboarding["current_step"] = "organization_verification"
    else:
        organization.status = OrganizationStatus.SUSPENDED
        tenant.status = TenantStatus.SUSPENDED
        onboarding["status"] = ONBOARDING_STATUS_REJECTED
        onboarding["current_step"] = "platform_review"
        if user is not None:
            user.status = PlatformUserStatus.SUSPENDED
            user.save(update_fields=["status", "updated_at"])

    organization.save(update_fields=["status", "updated_at"])
    tenant.save(update_fields=["status", "updated_at"])
    _save_onboarding_settings(organization, onboarding)
    record_audit_event(
        tenant=tenant,
        actor=actor,
        request=request,
        action=f"onboarding.review_{decision}",
        target_type="organization",
        target_id=organization.public_id,
        metadata={"note": note.strip()},
    )
    return organization, tenant, user


@transaction.atomic
def resend_onboarding_email_verification(*, business_email: str, request=None) -> bool:
    normalized_email = normalize_email(business_email)
    user = (
        PlatformUser.objects.select_related("tenant", "tenant__organization")
        .filter(email=normalized_email, tenant__isnull=False)
        .first()
    )
    if user is None or user.tenant is None:
        return False

    organization = user.tenant.organization
    onboarding = _get_onboarding_settings(organization)
    email_verification = dict(onboarding.get("email_verification") or {})
    already_verified = bool(email_verification.get("verified_at"))
    if already_verified or user.status == PlatformUserStatus.ACTIVE:
        return False

    issue_and_queue_email_verification(user=user)
    record_audit_event(
        tenant=user.tenant,
        actor=user,
        request=request,
        action="onboarding.email_verification_resent",
        target_type="platform_user",
        target_id=user.public_id,
        metadata={"organization_id": organization.public_id},
    )
    return True
