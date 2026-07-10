from django.conf import settings
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework.views import APIView

from apps.audit.services import record_audit_event
from apps.accounts.models import PlatformUser
from apps.accounts.serializers import LoginSerializer, RefreshInputSerializer, serialize_user
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
