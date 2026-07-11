import hashlib
import secrets
from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.password_validation import validate_password
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework.views import APIView

from apps.audit.services import record_audit_event
from apps.accounts.models import (
    PlatformUser,
    PlatformUserStatus,
    TeamInvitation,
    TeamInvitationStatus,
)
from apps.access_control.models import Role, UserRole
from apps.accounts.serializers import (
    LoginSerializer,
    RefreshInputSerializer,
    serialize_user,
)
from apps.accounts.cookies import (
    clear_refresh_cookie,
    require_trusted_cookie_origin,
    set_refresh_cookie,
)
from common.responses import success_response


class LoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        if user.tenant is not None:
            record_audit_event(
                tenant=user.tenant,
                actor=user,
                request=request,
                action="user.login",
                target_type="platform_user",
                target_id=user.public_id,
                metadata={"email": user.email},
                sensitive_metadata={"email": user.email},
            )
        response = success_response(
            {
                "tokens": {"access": serializer.validated_data["tokens"]["access"]},
                "user": serialize_user(user),
            },
            request=request,
            status=status.HTTP_200_OK,
        )
        set_refresh_cookie(response, serializer.validated_data["tokens"]["refresh"])
        return response


class RefreshView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        require_trusted_cookie_origin(request)
        refresh_token = request.COOKIES.get(settings.AUTH_REFRESH_COOKIE_NAME, "")
        serializer = RefreshInputSerializer(data={"refresh": refresh_token})
        serializer.is_valid(raise_exception=True)
        response = success_response(
            {"tokens": {"access": serializer.validated_data["access"]}},
            request=request,
            status=status.HTTP_200_OK,
        )
        rotated_refresh = serializer.validated_data.get("refresh")
        if rotated_refresh:
            set_refresh_cookie(response, rotated_refresh)
        return response


class LogoutView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        require_trusted_cookie_origin(request)
        raw_token = request.COOKIES.get(settings.AUTH_REFRESH_COOKIE_NAME, "")
        if raw_token:
            try:
                RefreshToken(raw_token).blacklist()
            except TokenError:
                pass
        response = success_response(
            {"logged_out": True}, request=request, status=status.HTTP_200_OK
        )
        clear_refresh_cookie(response)
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
                tenant=user.tenant,
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
        tenant = getattr(request.user, "tenant", None)
        if tenant is None:
            return success_response({"results": []}, request=request)
        users = (
            PlatformUser.objects.filter(tenant=tenant)
            .prefetch_related("user_roles__role")
            .order_by("email")
        )
        return success_response(
            {"results": [serialize_user(user) for user in users]},
            request=request,
        )


def serialize_invitation(invitation):
    return {
        "id": invitation.public_id,
        "email": invitation.email,
        "role": invitation.role.name,
        "status": invitation.status,
        "expires_at": invitation.expires_at.isoformat(),
        "created_at": invitation.created_at.isoformat(),
    }


class TeamInvitationListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return success_response(
            {
                "results": [
                    serialize_invitation(x)
                    for x in request.user.tenant.team_invitations.select_related("role")
                ]
            },
            request=request,
        )

    def post(self, request):
        email = str(request.data.get("email", "")).strip().lower()
        role_id = request.data.get("role_id")
        if PlatformUser.objects.filter(
            tenant=request.user.tenant, email=email
        ).exists():
            return success_response(
                {"detail": "This user is already a team member."},
                request=request,
                status=400,
            )
        role = Role.objects.get(
            tenant=request.user.tenant, public_id=role_id, status="active"
        )
        raw = secrets.token_urlsafe(32)
        invitation = TeamInvitation.objects.create(
            tenant=request.user.tenant,
            email=email,
            role=role,
            token_hash=hashlib.sha256(raw.encode()).hexdigest(),
            expires_at=timezone.now() + timedelta(days=7),
            invited_by=request.user,
        )
        record_audit_event(
            tenant=request.user.tenant,
            actor=request.user,
            request=request,
            action="team.invitation_created",
            target_type="team_invitation",
            target_id=invitation.public_id,
        )
        payload = serialize_invitation(invitation)
        if settings.DEBUG:
            payload["debug_accept_token"] = raw
        return success_response(payload, request=request, status=201)


class TeamInvitationActionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, invitation_id, action):
        invitation = request.user.tenant.team_invitations.get(public_id=invitation_id)
        if action == "revoke":
            invitation.status = TeamInvitationStatus.REVOKED
        elif action == "resend":
            invitation.expires_at = timezone.now() + timedelta(days=7)
        else:
            return success_response(
                {"detail": "Unsupported action."}, request=request, status=400
            )
        invitation.save()
        return success_response(serialize_invitation(invitation), request=request)


class TeamInvitationAcceptView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        token = str(request.data.get("token", ""))
        password = str(request.data.get("password", ""))
        digest = hashlib.sha256(token.encode()).hexdigest()
        invitation = (
            TeamInvitation.objects.select_related("role", "tenant")
            .filter(
                token_hash=digest,
                status=TeamInvitationStatus.PENDING,
                expires_at__gt=timezone.now(),
            )
            .first()
        )
        if not invitation:
            return success_response(
                {"detail": "Invitation is invalid or expired."},
                request=request,
                status=400,
            )
        validate_password(password)
        user = PlatformUser.objects.create_user(
            email=invitation.email,
            password=password,
            tenant=invitation.tenant,
            status=PlatformUserStatus.ACTIVE,
        )
        UserRole.objects.create(
            user=user, role=invitation.role, tenant=invitation.tenant
        )
        invitation.status = TeamInvitationStatus.ACCEPTED
        invitation.accepted_at = timezone.now()
        invitation.save()
        return success_response({"accepted": True}, request=request)
