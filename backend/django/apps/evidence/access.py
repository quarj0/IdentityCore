"""Current actor and purpose checks shared by evidence and reusable claims."""

from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, NotFound, APIException

from apps.accounts.models import PlatformUser
from apps.api_clients.models import APIClient
from apps.consent.services import active_consent
from common.authorization import AuthorizationAction, decide_user_access

PERMISSIONS = {
    "schemas:write": "manage_evidence",
    "evidence:read": "read_evidence",
    "evidence:write": "manage_evidence",
    "authorizations:write": "manage_subject_privacy",
    "authorizations:approve": "manage_subject_privacy",
    "claims:read": "read_claims",
    "claims:write": "manage_claims",
    "claims:review": "review_verification",
    "claims:disclose": "disclose_claims",
    "providers:operations": "manage_providers",
    "providers:assurance": "manage_provider_assurance",
    "providers:assurance:approve": "approve_provider_assurance",
}


def current_actor(actor, tenant, operation, *, project=None):
    privacy_maintenance = operation == "authorizations:write"
    if (tenant.deleted_at or tenant.status != "active") and not privacy_maintenance:
        raise PermissionDenied("An active tenant is required.")
    if project is not None and (
        project.tenant_id != tenant.pk
        or not privacy_maintenance
        and (project.deleted_at or project.status != "active")
    ):
        raise NotFound()
    if isinstance(actor, APIClient):
        principal = (
            APIClient.objects.select_related("project", "tenant")
            .filter(
                pk=actor.pk, tenant=tenant, deleted_at__isnull=True, status="active"
            )
            .first()
        )
        if principal is None or operation not in principal.scopes:
            raise PermissionDenied("The required API scope is missing.")
        if operation in {
            "authorizations:write",
            "authorizations:approve",
            "claims:review",
            "schemas:write",
            "providers:assurance",
            "providers:assurance:approve",
        }:
            raise PermissionDenied("This operation requires an authorized tenant user.")
        if project is not None and principal.project_id != project.pk:
            raise NotFound()
        if principal.project is not None and (
            principal.project.deleted_at or principal.project.status != "active"
        ):
            raise PermissionDenied("The credential project is inactive.")
        return principal
    if not isinstance(actor, PlatformUser):
        raise PermissionDenied("An explicitly authorized actor is required.")
    principal = PlatformUser.objects.filter(
        pk=actor.pk, tenant=tenant, deleted_at__isnull=True, status="active"
    ).first()
    permission = PERMISSIONS.get(operation)
    if (
        principal is None
        or permission is None
        or not decide_user_access(
            principal,
            action=AuthorizationAction.TENANT_ACCESS,
            tenant=tenant,
            permission_code=permission,
        ).allowed
    ):
        raise PermissionDenied("The required role permission is missing.")
    return principal


def identity(actor):
    return actor.public_id


def require_authorization(authorization, *, operation, at=None):
    now = at or timezone.now()
    if (
        authorization.deleted_at
        or authorization.revoked_at
        or not authorization.approved_at
        or not authorization.valid_from <= now < authorization.valid_until
        or operation not in authorization.allowed_operations_json
        or authorization.subject.deleted_at
        or authorization.project.deleted_at
        or authorization.project.status != "active"
        or authorization.tenant.deleted_at
        or authorization.tenant.status != "active"
    ):
        raise PermissionDenied("The purpose authorization is unavailable.")
    from apps.evidence.models import SubjectResourceRestriction

    if SubjectResourceRestriction.objects.filter(
        subject_id=authorization.subject_id, tenant_id=authorization.tenant_id
    ).exists():
        raise PermissionDenied("Subject resource use has been restricted.")
    if authorization.legal_basis == "consent":
        record = authorization.consent_record
        if (
            record is None
            or record.verification_subject_id != authorization.subject_id
            or record.tenant_id != authorization.tenant_id
        ):
            raise PermissionDenied("The consent authorization is unavailable.")
        case = record.verification
        if (
            case.project_id != authorization.project_id
            or case.purpose != authorization.purpose
        ):
            raise PermissionDenied("The consent purpose does not match.")
        current = active_consent(case, raise_on_unavailable=True)
        if current is None or current.pk != record.pk:
            raise PermissionDenied("Current consent is required.")
    return authorization


class GovernedContentUnavailable(APIException):
    status_code = 503
    default_detail = "Protected resource content is temporarily unavailable."
    default_code = "governed_content_unavailable"


def protected_value(record, field):
    try:
        return getattr(record, field)
    except (ValueError, KeyError):
        raise GovernedContentUnavailable() from None
