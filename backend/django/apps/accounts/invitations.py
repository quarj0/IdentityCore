"""Tenant-bound single-use invitations and encrypted, recoverable delivery."""

import hashlib
import secrets
from datetime import timedelta
from urllib.parse import urlencode, urlsplit

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from apps.accounts.models import PlatformUser, TeamInvitation
from apps.accounts.mfa import verify_challenge
from apps.access_control.models import Role, UserRole
from apps.audit.services import record_audit_event
from apps.notifications.models import Notification
from apps.notifications.services import enqueue_notification_delivery
from apps.tenants.models import Tenant


def _tenant(tenant_id):
    tenant = (
        Tenant.objects.select_for_update(no_key=True)
        .filter(pk=tenant_id, deleted_at__isnull=True, status="active")
        .first()
    )
    if tenant is None:
        raise PermissionDenied("An active organization is required.")
    return tenant


def _role(tenant, public_id):
    role = (
        Role.objects.select_for_update(no_key=True)
        .filter(
            tenant=tenant,
            public_id=public_id,
            scope="tenant",
            status="active",
            deleted_at__isnull=True,
        )
        .first()
    )
    if role is None:
        raise NotFound("Role not found.")
    return role


def _grantable(actor, role):
    held = set(
        actor.user_roles.filter(
            tenant_id=actor.tenant_id,
            role__tenant_id=actor.tenant_id,
            role__scope="tenant",
            role__status="active",
            role__deleted_at__isnull=True,
        ).values_list("role__role_permissions__permission__code", flat=True)
    )
    requested = set(role.role_permissions.values_list("permission__code", flat=True))
    if "manage_team" not in held or not requested.issubset(held):
        raise PermissionDenied("The role includes permissions you cannot grant.")


def _queue(invitation, raw):
    base = settings.TEAM_INVITATION_BASE_URL
    parsed = urlsplit(base)
    if (
        not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or parsed.scheme not in {"http", "https"}
        or (parsed.scheme != "https" and not settings.DEBUG)
    ):
        raise ValidationError("The invitation delivery URL is not configured safely.")
    link = base + "#" + urlencode({"token": raw})
    notification = Notification.objects.create(
        tenant=invitation.tenant,
        recipient_type="platform_user",
        recipient=invitation.email,
        channel="email",
        template_code="team.invitation",
        subject="Your IdentityCore team invitation",
        body_preview="A single-use invitation link was sent to this recipient.",
        delivery_json={
            "team_invitation": invitation.public_id,
            "token": raw,
            "body": "Accept your IdentityCore invitation: " + link,
        },
    )
    enqueue_notification_delivery(notification)


def _audit(invitation, actor, action, request):
    record_audit_event(
        tenant_id=invitation.tenant_id,
        actor=actor,
        request=request,
        action="team.invitation_" + action,
        target_type="team_invitation",
        target_id=invitation.public_id,
    )


@transaction.atomic
def create_invitation(*, actor, email, role_id, request=None):
    tenant = _tenant(actor.tenant_id)
    role = _role(tenant, role_id)
    _grantable(actor, role)
    now = timezone.now()
    TeamInvitation.objects.filter(
        tenant=tenant, email=email, status="pending", expires_at__lte=now
    ).update(status="expired", updated_at=now)
    if TeamInvitation.objects.filter(
        tenant=tenant, email=email, status="pending"
    ).exists():
        raise ValidationError("An invitation is already pending for this address.")
    account = PlatformUser.objects.filter(email__iexact=email).first()
    if account and (
        account.tenant_id != tenant.pk
        or account.is_platform_admin
        or not account.is_active
        or account.deleted_at is not None
    ):
        raise ValidationError("Invitation cannot be created for this address.")
    raw = secrets.token_urlsafe(32)
    invitation = TeamInvitation.objects.create(
        tenant=tenant,
        email=email,
        role=role,
        invited_by=actor,
        token_hash=hashlib.sha256(raw.encode()).hexdigest(),
        expires_at=now + timedelta(days=7),
    )
    _queue(invitation, raw)
    _audit(invitation, actor, "created", request)
    return invitation


@transaction.atomic
def change_invitation(*, actor, public_id, action, request=None):
    tenant = _tenant(actor.tenant_id)
    invitation = (
        TeamInvitation.objects.select_for_update()
        .filter(tenant=tenant, public_id=public_id, deleted_at__isnull=True)
        .first()
    )
    if invitation is None:
        raise NotFound("Invitation not found.")
    if invitation.status not in {"pending", "expired"}:
        raise ValidationError("This invitation is no longer available.")
    if action == "revoke":
        invitation.status = "revoked"
    elif action == "resend":
        role = _role(tenant, invitation.role.public_id)
        _grantable(actor, role)
        raw = secrets.token_urlsafe(32)
        invitation.token_hash = hashlib.sha256(raw.encode()).hexdigest()
        invitation.status = "pending"
        invitation.expires_at = timezone.now() + timedelta(days=7)
    else:
        raise ValidationError("Unsupported invitation action.")
    invitation.save()
    if action == "resend":
        _queue(invitation, raw)
    _audit(invitation, actor, "revoked" if action == "revoke" else "resent", request)
    return invitation


def accept_invitation(*, token, password, mfa_code="", request=None):
    # Only use this preliminary lookup to choose the tenant lock. Every claim is
    # revalidated under that lock before any membership or account write.
    digest = hashlib.sha256(token.encode()).hexdigest()
    tenant_id = (
        TeamInvitation.objects.filter(token_hash=digest)
        .values_list("tenant_id", flat=True)
        .first()
    )
    if tenant_id is None:
        raise ValidationError("Invitation is invalid or cannot be accepted.")
    try:
        with transaction.atomic():
            tenant = _tenant(tenant_id)
            invitation = (
                TeamInvitation.objects.select_for_update()
                .filter(
                    tenant=tenant,
                    token_hash=digest,
                    status="pending",
                    deleted_at__isnull=True,
                    expires_at__gt=timezone.now(),
                )
                .first()
            )
            if invitation is None:
                raise ValidationError("Invitation is invalid or cannot be accepted.")
            role = _role(tenant, invitation.role.public_id)
            inviter = invitation.invited_by
            if (
                not inviter.is_active
                or inviter.deleted_at is not None
                or inviter.tenant_id != tenant.pk
            ):
                raise ValidationError("Invitation is invalid or cannot be accepted.")
            _grantable(inviter, role)
            user = (
                PlatformUser.objects.select_for_update()
                .filter(email__iexact=invitation.email)
                .first()
            )
            if user:
                if (
                    user.tenant_id != tenant.pk
                    or user.is_platform_admin
                    or not user.is_active
                    or user.deleted_at is not None
                    or not user.check_password(password)
                ):
                    raise ValidationError(
                        "Invitation is invalid or cannot be accepted."
                    )
                if user.mfa_enabled and not verify_challenge(user, mfa_code):
                    raise ValidationError(
                        "Invitation is invalid or cannot be accepted."
                    )
            else:
                validate_password(password)
                user = PlatformUser.objects.create_user(
                    email=invitation.email,
                    password=password,
                    tenant=tenant,
                    status="active",
                )
            UserRole.objects.get_or_create(user=user, role=role, tenant=tenant)
            invitation.status = "accepted"
            invitation.accepted_at = timezone.now()
            invitation.save(update_fields=["status", "accepted_at", "updated_at"])
            _audit(invitation, user, "accepted", request)
            return user
    except (IntegrityError, NotFound, PermissionDenied):
        raise ValidationError("Invitation is invalid or cannot be accepted.") from None
    except DjangoValidationError as exc:
        raise ValidationError({"password": exc.messages}) from None
