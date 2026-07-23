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
from common.storage import (
    build_signed_download_url,
    get_object_storage_public_bucket_name,
)

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

ORGANIZATION_VERIFICATION_REVIEW_DRAFT = "draft"
ORGANIZATION_VERIFICATION_REVIEW_SUBMITTED = "submitted"
ORGANIZATION_VERIFICATION_REVIEW_NEEDS_INFORMATION = "needs_information"
ORGANIZATION_VERIFICATION_REVIEW_REJECTED = "rejected"
ORGANIZATION_VERIFICATION_REVIEW_APPROVED = "approved"
ORGANIZATION_VERIFICATION_REVIEW_CHANGED_AFTER_APPROVAL = "changed_after_approval"
PLATFORM_REVIEW_STATUS_NOT_STARTED = "not_started"
PLATFORM_REVIEW_STATUS_QUEUED = "queued"
PLATFORM_REVIEW_STATUS_ASSIGNED = "assigned"
PLATFORM_REVIEW_STATUS_ESCALATED = "escalated"
PLATFORM_REVIEW_STATUS_REVIEWED = "reviewed"


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
            "country": organization_country.strip(),
        },
        "email_verification": {
            "required": True,
            "verified_at": None,
        },
        "organization_verification": {
            "review_status": ORGANIZATION_VERIFICATION_REVIEW_DRAFT,
            "reviewed_at": None,
            "reviewed_by": "",
            "review_note": "",
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
            "status": PLATFORM_REVIEW_STATUS_NOT_STARTED,
            "reviewed_at": None,
            "reviewed_by": "",
            "note": "",
            "assigned_reviewer_id": "",
            "assigned_reviewer_name": "",
            "assigned_at": None,
            "escalated": False,
            "escalation_reason": "",
            "escalated_at": None,
            "required_approver_role": "",
        },
    }


def _get_onboarding_settings(organization: Organization) -> dict:
    settings_json = dict(organization.settings_json or {})
    return dict(settings_json.get("onboarding") or {})


def _normalize_supporting_document_keys(keys: list[str] | None) -> list[str]:
    return sorted({key.strip() for key in (keys or []) if key and key.strip()})


def _organization_verification_review_status(onboarding: dict) -> str:
    organization_verification = dict(onboarding.get("organization_verification") or {})
    review_status = organization_verification.get("review_status") or ""
    if review_status:
        return review_status
    if not organization_verification.get("submitted_at"):
        return ORGANIZATION_VERIFICATION_REVIEW_DRAFT
    if onboarding.get("status") in {
        ONBOARDING_STATUS_NEEDS_INFORMATION,
        ONBOARDING_STATUS_REJECTED,
    }:
        return onboarding.get("status", ORGANIZATION_VERIFICATION_REVIEW_SUBMITTED)
    return ORGANIZATION_VERIFICATION_REVIEW_SUBMITTED


def _organization_verification_editable(onboarding: dict) -> bool:
    return _organization_verification_review_status(onboarding) in {
        ORGANIZATION_VERIFICATION_REVIEW_DRAFT,
        ORGANIZATION_VERIFICATION_REVIEW_NEEDS_INFORMATION,
        ORGANIZATION_VERIFICATION_REVIEW_REJECTED,
    }


def _organization_verification_has_changed(
    *,
    existing: dict,
    business_registration_number: str,
    registered_address: str,
    official_website: str,
    tax_identification_number: str,
    supporting_document_keys: list[str] | None,
) -> bool:
    return any(
        (
            existing.get("business_registration_number", "").strip()
            != business_registration_number.strip(),
            existing.get("registered_address", "").strip()
            != registered_address.strip(),
            existing.get("official_website", "").strip()
            != official_website.strip(),
            existing.get("tax_identification_number", "").strip()
            != tax_identification_number.strip(),
            _normalize_supporting_document_keys(
                existing.get("supporting_document_keys")
            )
            != _normalize_supporting_document_keys(supporting_document_keys),
        )
    )


def _organization_verification_is_submitted(onboarding: dict) -> bool:
    organization_verification = dict(onboarding.get("organization_verification") or {})
    return bool(organization_verification.get("submitted_at"))


def _platform_review_state(onboarding: dict) -> dict:
    return dict(onboarding.get("platform_review") or {})


def _platform_role_names_for_user(user: PlatformUser) -> set[str]:
    return set(
        user.user_roles.filter(role__scope=RoleScope.PLATFORM)
        .select_related("role")
        .values_list("role__name", flat=True)
    )


def _user_can_act_as_senior_reviewer(user: PlatformUser) -> bool:
    role_names = _platform_role_names_for_user(user)
    return bool(role_names & {"Senior Reviewer", "Platform Admin"})


def assign_platform_review_reviewer(
    *,
    organization: Organization,
    reviewer: PlatformUser,
    actor: PlatformUser,
    request=None,
) -> Organization:
    onboarding = _get_onboarding_settings(organization)
    if reviewer.is_platform_admin is not True:
        raise ValidationError("Choose a platform administrator reviewer.")
    platform_review = _platform_review_state(onboarding)
    platform_review.update(
        {
            "status": PLATFORM_REVIEW_STATUS_ASSIGNED,
            "assigned_reviewer_id": reviewer.public_id,
            "assigned_reviewer_name": f"{reviewer.first_name} {reviewer.last_name}".strip()
            or reviewer.email,
            "assigned_at": timezone.now().isoformat(),
            "required_approver_role": platform_review.get(
                "required_approver_role", ""
            ),
        }
    )
    onboarding["platform_review"] = platform_review
    _save_onboarding_settings(organization, onboarding)
    record_audit_event(
        tenant=organization.tenant,
        actor=actor,
        request=request,
        action="onboarding.platform_review_assigned",
        target_type="organization",
        target_id=organization.public_id,
        metadata={"reviewer_id": reviewer.public_id},
    )
    return organization


def escalate_platform_review(
    *,
    organization: Organization,
    actor: PlatformUser,
    reason: str,
    request=None,
) -> Organization:
    onboarding = _get_onboarding_settings(organization)
    platform_review = _platform_review_state(onboarding)
    platform_review.update(
        {
            "status": PLATFORM_REVIEW_STATUS_ESCALATED,
            "escalated": True,
            "escalation_reason": reason.strip(),
            "escalated_at": timezone.now().isoformat(),
            "required_approver_role": "Senior Reviewer",
        }
    )
    onboarding["platform_review"] = platform_review
    _save_onboarding_settings(organization, onboarding)
    record_audit_event(
        tenant=organization.tenant,
        actor=actor,
        request=request,
        action="onboarding.platform_review_escalated",
        target_type="organization",
        target_id=organization.public_id,
        metadata={"reason": reason.strip()},
    )
    return organization


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
    documents = organization.supporting_documents.filter(deleted_at__isnull=True)
    country_code = registration.get("organization_country", "")
    country_names = dict(countries)
    organization_verification_review_status = _organization_verification_review_status(
        onboarding
    )
    organization_verification_changed_after_approval = (
        organization_verification_review_status
        == ORGANIZATION_VERIFICATION_REVIEW_CHANGED_AFTER_APPROVAL
    )
    return {
        "organization_id": organization.public_id,
        "organization_name": organization.name,
        "organization_slug": organization.slug,
        "organization_type": registration.get(
            "organization_type", organization.industry
        ),
        "organization_country": country_code,
        "organization_country_name": country_names.get(country_code, country_code),
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
        "organization_verification_editable": _organization_verification_editable(
            onboarding
        ),
        "organization_verification_review_status": organization_verification_review_status,
        "organization_verification_changed_after_approval": organization_verification_changed_after_approval,
        "organization_verification_reviewed_at": organization_verification.get(
            "reviewed_at"
        ),
        "organization_verification_review_note": organization_verification.get(
            "review_note", ""
        ),
        "business_registration_number": organization_verification.get(
            "business_registration_number", ""
        ),
        "tax_identification_number": organization_verification.get(
            "tax_identification_number", ""
        ),
        "registered_address": organization_verification.get("registered_address", ""),
        "official_website": organization_verification.get("official_website", ""),
        "supporting_documents": [
            {
                "id": doc.public_id,
                "filename": doc.filename,
                "file_size_bytes": doc.file_size_bytes,
                "status": doc.status,
                "storage_key": doc.storage_key,
                "download_url": build_signed_download_url(
                    storage_key=doc.storage_key,
                    filename=doc.filename,
                    bucket_name=get_object_storage_public_bucket_name(),
                ),
            }
            for doc in documents
        ],
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
        "platform_review_assigned_reviewer_id": platform_review.get(
            "assigned_reviewer_id", ""
        ),
        "platform_review_assigned_reviewer_name": platform_review.get(
            "assigned_reviewer_name", ""
        ),
        "platform_review_assigned_at": platform_review.get("assigned_at"),
        "platform_review_escalated": bool(platform_review.get("escalated", False)),
        "platform_review_escalation_reason": platform_review.get(
            "escalation_reason", ""
        ),
        "platform_review_escalated_at": platform_review.get("escalated_at"),
        "platform_review_required_approver_role": platform_review.get(
            "required_approver_role", ""
        ),
    }


def serialize_organization_review_state(organization: Organization) -> dict:
    tenant = organization.tenant
    user = tenant.platform_users.order_by("created_at").first()
    if user is None:
        raise ValidationError("Onboarding organization does not have an administrator.")
    onboarding = serialize_onboarding_state(organization=organization, tenant=tenant, user=user)
    review_status = onboarding["organization_verification_review_status"]
    review_notes = {
        ORGANIZATION_VERIFICATION_REVIEW_SUBMITTED: "Waiting for review.",
        ORGANIZATION_VERIFICATION_REVIEW_NEEDS_INFORMATION: "More information was requested.",
        ORGANIZATION_VERIFICATION_REVIEW_REJECTED: "Submission was rejected.",
        ORGANIZATION_VERIFICATION_REVIEW_CHANGED_AFTER_APPROVAL: "Approved record changed and needs another review.",
    }
    onboarding["review_priority"] = (
        "critical"
        if onboarding["organization_verification_changed_after_approval"]
        or onboarding["platform_review_escalated"]
        else "high"
        if review_status in {
            ORGANIZATION_VERIFICATION_REVIEW_NEEDS_INFORMATION,
            ORGANIZATION_VERIFICATION_REVIEW_REJECTED,
        }
        else "medium"
    )
    onboarding["review_summary"] = review_notes.get(
        review_status, "Pending organization review."
    )
    return onboarding


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

    if not supporting_document_keys or not 1 <= len(supporting_document_keys) <= 5:
        raise ValidationError("Upload between one and five supporting PDF documents.")
    tenant = user.tenant
    organization = tenant.organization
    documents = organization.supporting_documents.filter(
        tenant=tenant, storage_key__in=supporting_document_keys,
        status__in=["uploaded", "submitted"], deleted_at__isnull=True
    )
    if documents.count() != len(set(supporting_document_keys)):
        raise ValidationError("One or more supporting documents are invalid.")
    documents.filter(status="uploaded").update(status="submitted")
    onboarding = _get_onboarding_settings(organization)
    existing_verification = dict(onboarding.get("organization_verification") or {})
    has_changed = _organization_verification_has_changed(
        existing=existing_verification,
        business_registration_number=business_registration_number,
        registered_address=registered_address,
        official_website=official_website,
        tax_identification_number=tax_identification_number,
        supporting_document_keys=supporting_document_keys,
    )
    post_approval_edit = (
        onboarding.get("status") == ONBOARDING_STATUS_ACTIVE
        or organization.status == OrganizationStatus.ACTIVE
        or tenant.status == TenantStatus.ACTIVE
    )
    if post_approval_edit and not has_changed:
        return organization, tenant, user
    review_status = ORGANIZATION_VERIFICATION_REVIEW_SUBMITTED
    if post_approval_edit and has_changed:
        review_status = ORGANIZATION_VERIFICATION_REVIEW_CHANGED_AFTER_APPROVAL
    onboarding["organization_verification"] = {
        "review_status": review_status,
        "reviewed_at": None,
        "reviewed_by": "",
        "review_note": "",
        "submitted_at": timezone.now().isoformat(),
        "business_registration_number": business_registration_number.strip(),
        "tax_identification_number": tax_identification_number.strip(),
        "registered_address": registered_address.strip(),
        "official_website": official_website.strip(),
        "supporting_document_keys": _normalize_supporting_document_keys(
            supporting_document_keys
        ),
    }
    if post_approval_edit and has_changed:
        onboarding["status"] = ONBOARDING_STATUS_PLATFORM_REVIEW_PENDING
        onboarding["current_step"] = "platform_review"
        onboarding["platform_review"] = {
            "status": PLATFORM_REVIEW_STATUS_QUEUED,
            "reviewed_at": None,
            "reviewed_by": "",
            "note": "Organization verification changed after approval.",
            "assigned_reviewer_id": "",
            "assigned_reviewer_name": "",
            "assigned_at": None,
            "escalated": True,
            "escalation_reason": "Organization verification changed after approval.",
            "escalated_at": timezone.now().isoformat(),
            "required_approver_role": "Senior Reviewer",
        }
        organization.status = OrganizationStatus.PENDING_REVIEW
        tenant.status = TenantStatus.PENDING_REVIEW
        organization.save(update_fields=["status", "updated_at"])
        tenant.save(update_fields=["status", "updated_at"])
    else:
        onboarding["status"] = ONBOARDING_STATUS_ADMIN_IDENTITY_VERIFICATION_REQUIRED
        onboarding["current_step"] = "administrator_identity_verification"
        organization.save(update_fields=["status", "updated_at"])
        tenant.save(update_fields=["status", "updated_at"])
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
    if not _organization_verification_is_submitted(onboarding):
        raise ValidationError(
            "Complete organization verification before administrator identity verification."
        )
    existing = dict(onboarding.get("administrator_identity_verification") or {})
    if (
        existing.get("status") == "submitted"
        and existing.get("verification_id") == verification_id.strip()
    ):
        return organization, tenant, user
    onboarding["administrator_identity_verification"] = {
        "status": "submitted",
        "verification_id": verification_id.strip(),
        "submitted_at": timezone.now().isoformat(),
    }
    onboarding["status"] = ONBOARDING_STATUS_PLATFORM_REVIEW_PENDING
    onboarding["current_step"] = "platform_review"
    onboarding["platform_review"] = {
        "status": PLATFORM_REVIEW_STATUS_QUEUED,
        "reviewed_at": None,
        "reviewed_by": "",
        "note": "",
        "assigned_reviewer_id": "",
        "assigned_reviewer_name": "",
        "assigned_at": None,
        "escalated": False,
        "escalation_reason": "",
        "escalated_at": None,
        "required_approver_role": "",
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
    platform_review = dict(onboarding.get("platform_review") or {})
    onboarding["platform_review"] = {
        "status": platform_review.get("status", PLATFORM_REVIEW_STATUS_QUEUED),
        "reviewed_at": timezone.now().isoformat(),
        "reviewed_by": actor.public_id,
        "note": note.strip(),
        "assigned_reviewer_id": platform_review.get("assigned_reviewer_id", ""),
        "assigned_reviewer_name": platform_review.get(
            "assigned_reviewer_name", ""
        ),
        "assigned_at": platform_review.get("assigned_at"),
        "escalated": bool(platform_review.get("escalated", False)),
        "escalation_reason": platform_review.get("escalation_reason", ""),
        "escalated_at": platform_review.get("escalated_at"),
        "required_approver_role": platform_review.get("required_approver_role", ""),
    }
    organization_verification = dict(
        onboarding.get("organization_verification") or {}
    )

    if decision == "approved":
        if (
            onboarding.get("organization_verification_changed_after_approval", False)
            or bool(platform_review.get("escalated", False))
        ) and not _user_can_act_as_senior_reviewer(actor):
            raise ValidationError(
                "A senior reviewer must approve escalated or changed-after-approval cases."
            )
        organization.status = OrganizationStatus.ACTIVE
        tenant.status = TenantStatus.ACTIVE
        onboarding["tier"] = ORGANIZATION_TIER_VERIFIED
        onboarding["status"] = ONBOARDING_STATUS_ACTIVE
        onboarding["current_step"] = "active"
        onboarding["organization_verification"] = {
            **organization_verification,
            "review_status": ORGANIZATION_VERIFICATION_REVIEW_APPROVED,
            "reviewed_at": timezone.now().isoformat(),
            "reviewed_by": actor.public_id,
            "review_note": note.strip(),
        }
        onboarding["platform_review"]["status"] = decision
        if user is not None and user.status == PlatformUserStatus.INACTIVE:
            user.status = PlatformUserStatus.ACTIVE
            user.save(update_fields=["status", "updated_at"])
    elif decision == "needs_information":
        organization.status = OrganizationStatus.PENDING_REVIEW
        tenant.status = TenantStatus.PENDING_REVIEW
        onboarding["status"] = ONBOARDING_STATUS_NEEDS_INFORMATION
        onboarding["current_step"] = "organization_verification"
        onboarding["organization_verification"] = {
            **organization_verification,
            "review_status": ORGANIZATION_VERIFICATION_REVIEW_NEEDS_INFORMATION,
            "reviewed_at": timezone.now().isoformat(),
            "reviewed_by": actor.public_id,
            "review_note": note.strip(),
        }
        onboarding["platform_review"]["status"] = decision
    else:
        organization.status = OrganizationStatus.PENDING_REVIEW
        tenant.status = TenantStatus.PENDING_REVIEW
        onboarding["status"] = ONBOARDING_STATUS_REJECTED
        onboarding["current_step"] = "organization_verification"
        onboarding["organization_verification"] = {
            **organization_verification,
            "review_status": ORGANIZATION_VERIFICATION_REVIEW_REJECTED,
            "reviewed_at": timezone.now().isoformat(),
            "reviewed_by": actor.public_id,
            "review_note": note.strip(),
        }
        onboarding["platform_review"]["status"] = decision

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
