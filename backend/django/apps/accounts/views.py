import logging
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.views import APIView

from apps.audit.services import lock_audit_chain, record_audit_event
from apps.accounts.models import (
    PlatformUser,
    TeamInvitation,
)
from apps.accounts.serializers import (
    LoginSerializer,
    RefreshInputSerializer,
    serialize_user,
)
from apps.accounts.cookies import (
    clear_refresh_cookie,
    get_refresh_cookie_name,
    require_trusted_cookie_origin,
    set_refresh_cookie,
)
from apps.accounts.mfa import (
    enable_mfa,
    consume_mfa_token,
    generate_secret,
    issue_mfa_token,
    provisioning_uri,
    resolve_mfa_token,
    verify_challenge,
    verify_totp,
)
from apps.accounts.sessions import (
    issue_refresh_token,
    revoke_refresh_token,
    revoke_user_sessions,
)
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework.exceptions import ValidationError
from common.permissions import IsTenantUser
from apps.accounts.invitations import (
    create_invitation,
    change_invitation,
    accept_invitation,
)
from apps.accounts.serializers import (
    TeamInvitationCreateInput,
    TeamInvitationAcceptInput,
)
from common.responses import success_response
from common.throttling import SensitivePublicRateThrottle

logger = logging.getLogger(__name__)


class LoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [SensitivePublicRateThrottle]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        if serializer.validated_data["mfa_required"]:
            purpose = "challenge" if user.mfa_enabled else "enrollment"
            return success_response(
                {
                    "mfa_required": True,
                    "mfa_enrollment_required": not user.mfa_enabled,
                    "mfa_token": issue_mfa_token(user, purpose=purpose),
                },
                request=request,
                status=status.HTTP_202_ACCEPTED,
            )
        return complete_login(request, user)


def complete_login(request, user, *, mfa_method: str | None = None):
    refresh = issue_refresh_token(user, request=request, mfa_verified=bool(mfa_method))
    now = timezone.now()
    PlatformUser.objects.filter(pk=user.pk).update(last_login_at=now, updated_at=now)
    user.last_login_at = now
    user.updated_at = now
    if user.tenant_id is not None:
        record_audit_event(
            tenant_id=user.tenant_id,
            actor=user,
            request=request,
            action="user.login",
            target_type="platform_user",
            target_id=user.public_id,
            metadata={"mfa_method": mfa_method} if mfa_method else {},
            sensitive_metadata={"email": user.email},
        )
    response = success_response(
        {
            "tokens": {"access": str(refresh.access_token)},
            "user": serialize_user(user),
        },
        request=request,
        status=status.HTTP_200_OK,
    )
    set_refresh_cookie(
        response,
        str(refresh),
        cookie_name=get_refresh_cookie_name(request),
    )
    return response


def _mfa_user(request, purpose):
    token = str(request.data.get("mfa_token", ""))
    try:
        return resolve_mfa_token(token, purpose=purpose)
    except ValueError as exc:
        raise AuthenticationFailed(str(exc)) from exc


class MFAEnrollView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        user = _mfa_user(request, "enrollment")
        secret = generate_secret()
        user.mfa_config_json = {"pending_totp_secret": secret}
        user.save(update_fields=["mfa_config_json", "updated_at"])
        record_audit_event(
            tenant_id=user.tenant_id,
            actor=user,
            request=request,
            action="user.mfa_enrollment_started",
            target_type="platform_user",
            target_id=user.public_id,
        )
        return success_response(
            {"secret": secret, "provisioning_uri": provisioning_uri(user, secret)},
            request=request,
        )


class MFAEnrollConfirmView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        user = _mfa_user(request, "enrollment")
        secret = user.mfa_config_json.get("pending_totp_secret", "")
        if not secret or not verify_totp(secret, str(request.data.get("code", ""))):
            raise AuthenticationFailed("Invalid authentication code.")
        recovery_codes = enable_mfa(user, secret)
        record_audit_event(
            tenant_id=user.tenant_id,
            actor=user,
            request=request,
            action="user.mfa_enabled",
            target_type="platform_user",
            target_id=user.public_id,
        )
        response = complete_login(request, user, mfa_method="totp")
        response.data["data"]["recovery_codes"] = recovery_codes
        return response


class MFAChallengeView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        user = _mfa_user(request, "challenge")
        token = str(request.data.get("mfa_token", ""))
        method = verify_challenge(user, str(request.data.get("code", "")))
        if method is None or not consume_mfa_token(user, token):
            record_audit_event(
                tenant_id=user.tenant_id,
                actor=user,
                request=request,
                action="user.mfa_challenge_failed",
                target_type="platform_user",
                target_id=user.public_id,
            )
            raise AuthenticationFailed("Invalid authentication code.")
        record_audit_event(
            tenant_id=user.tenant_id,
            actor=user,
            request=request,
            action="user.mfa_challenge_succeeded",
            target_type="platform_user",
            target_id=user.public_id,
            metadata={"method": method},
        )
        return complete_login(request, user, mfa_method=method)


class MFAResetView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        lock_audit_chain(request.user.tenant_id)
        user = PlatformUser.objects.select_for_update().get(pk=request.user.pk)
        password = str(request.data.get("password", ""))
        code = str(request.data.get("code", ""))
        if authenticate(request=request, email=user.email, password=password) != user:
            raise AuthenticationFailed("Password confirmation failed.")
        if not user.mfa_enabled or verify_challenge(user, code) is None:
            raise AuthenticationFailed("Invalid authentication code.")
        user.mfa_enabled = False
        user.mfa_config_json = {}
        user.save(update_fields=["mfa_enabled", "mfa_config_json", "updated_at"])
        user.mfa_recovery_codes.all().delete()
        revoke_user_sessions(user)
        record_audit_event(
            tenant_id=user.tenant_id,
            actor=user,
            request=request,
            action="user.mfa_reset",
            target_type="platform_user",
            target_id=user.public_id,
        )
        return success_response({"mfa_enabled": False}, request=request)


class RefreshView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        require_trusted_cookie_origin(request)
        cookie_name = get_refresh_cookie_name(request)
        migrated_legacy = (
            cookie_name != settings.AUTH_REFRESH_COOKIE_NAME
            and cookie_name not in request.COOKIES
        )
        refresh_token = request.COOKIES.get(
            settings.AUTH_REFRESH_COOKIE_NAME if migrated_legacy else cookie_name, ""
        )
        serializer = RefreshInputSerializer(
            data={"refresh": refresh_token}, context={"request": request}
        )
        try:
            serializer.is_valid(raise_exception=True)
        except (TokenError, ValidationError) as exc:
            # SimpleJWT raises TokenError directly for blacklisted tokens instead of
            # consistently converting it to a DRF authentication response.
            auth_error = AuthenticationFailed(
                "Your session has expired. Please sign in again."
            )
            auth_error.clear_refresh_cookie = True
            auth_error.refresh_cookie_name = cookie_name
            raise auth_error from exc
        response = success_response(
            {"tokens": {"access": serializer.validated_data["access"]}},
            request=request,
            status=status.HTTP_200_OK,
        )
        rotated_refresh = serializer.validated_data.get("refresh")
        if rotated_refresh:
            set_refresh_cookie(response, rotated_refresh, cookie_name=cookie_name)
        if migrated_legacy:
            clear_refresh_cookie(response)
        return response


class LogoutView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        require_trusted_cookie_origin(request)
        cookie_name = get_refresh_cookie_name(request)
        raw_token = request.COOKIES.get(cookie_name, "")
        if raw_token:
            try:
                revoke_refresh_token(raw_token)
            except TokenError:
                pass
        response = success_response(
            {"logged_out": True}, request=request, status=status.HTTP_200_OK
        )
        clear_refresh_cookie(response, cookie_name=cookie_name)
        return response


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return success_response({"user": serialize_user(request.user)}, request=request)

    def patch(self, request):
        user = request.user
        for field in ("first_name", "last_name", "phone_number"):
            if field in request.data:
                setattr(user, field, str(request.data[field]).strip())
        user.save()
        if user.tenant_id:
            record_audit_event(
                tenant_id=user.tenant_id,
                actor=user,
                request=request,
                action="user.profile_updated",
                target_type="platform_user",
                target_id=user.public_id,
            )
        return success_response({"user": serialize_user(user)}, request=request)


class NotificationPreferencesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return success_response(
            {"preferences": request.user.notification_preferences_json}, request=request
        )

    def patch(self, request):
        allowed = {
            "email_verification_updates",
            "email_security_alerts",
            "email_webhook_failures",
            "in_app_verification_updates",
            "in_app_security_alerts",
        }
        values = {k: bool(v) for k, v in request.data.items() if k in allowed}
        request.user.notification_preferences_json = {
            **request.user.notification_preferences_json,
            **values,
        }
        request.user.save(update_fields=["notification_preferences_json", "updated_at"])
        return success_response(
            {"preferences": request.user.notification_preferences_json}, request=request
        )


class TeamListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant_id = request.user.tenant_id
        if tenant_id is None:
            return success_response({"results": []}, request=request)
        users = (
            PlatformUser.objects.filter(tenant_id=tenant_id)
            .prefetch_related("user_roles__role")
            .order_by("email")
        )
        return success_response(
            {"results": [serialize_user(user) for user in users]},
            request=request,
        )


def serialize_invitation(invitation):
    state = invitation.status
    if state == "pending" and invitation.expires_at <= timezone.now():
        state = "expired"
    return {
        "id": invitation.public_id,
        "email": invitation.email,
        "role": invitation.role.name,
        "status": state,
        "expires_at": invitation.expires_at.isoformat(),
        "created_at": invitation.created_at.isoformat(),
    }


class TeamInvitationListCreateView(APIView):
    permission_classes = [IsTenantUser]
    required_permission_code = "manage_team"

    def get(self, request):
        invitations = TeamInvitation.objects.filter(
            tenant_id=request.user.tenant_id, deleted_at__isnull=True
        ).select_related("role")
        return success_response(
            {"results": [serialize_invitation(x) for x in invitations]}, request=request
        )

    def post(self, request):
        serializer = TeamInvitationCreateInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        invitation = create_invitation(
            actor=request.user, request=request, **serializer.validated_data
        )
        return success_response(
            serialize_invitation(invitation), request=request, status=201
        )


class TeamInvitationActionView(APIView):
    permission_classes = [IsTenantUser]
    required_permission_code = "manage_team"

    def post(self, request, invitation_id, action):
        invitation = change_invitation(
            actor=request.user, public_id=invitation_id, action=action, request=request
        )
        return success_response(serialize_invitation(invitation), request=request)


class TeamInvitationAcceptView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [SensitivePublicRateThrottle]

    def post(self, request):
        serializer = TeamInvitationAcceptInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        accept_invitation(request=request, **serializer.validated_data)
        return success_response({"accepted": True}, request=request)
