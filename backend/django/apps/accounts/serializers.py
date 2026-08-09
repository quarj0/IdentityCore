import logging

from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.exceptions import TokenError

from apps.accounts.models import PlatformUser
from apps.accounts.mfa import is_mfa_required
from apps.tenants.models import Tenant
from apps.accounts.sessions import rotate_refresh_token

logger = logging.getLogger(__name__)


def serialize_user(user: PlatformUser) -> dict:
    user_roles = user.user_roles.select_related("role").all()
    tenant_public_id = user.tenant_id
    tenant_name = None
    tenant_status = None
    if tenant_public_id is not None:
        tenant_payload = (
            Tenant.objects.filter(pk=tenant_public_id)
            .values("public_id", "name", "status")
            .first()
        )
        if tenant_payload is not None:
            tenant_public_id = tenant_payload["public_id"]
            tenant_name = tenant_payload["name"]
            tenant_status = tenant_payload["status"]
    return {
        "public_id": user.public_id,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "phone_number": user.phone_number,
        "status": user.status,
        "tenant_public_id": tenant_public_id,
        "tenant_name": tenant_name,
        "tenant_status": tenant_status,
        "is_platform_admin": user.is_platform_admin,
        "mfa_enabled": user.mfa_enabled,
        "roles": [assignment.role.name for assignment in user_roles],
        "notification_preferences": user.notification_preferences_json,
        "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
        "created_at": user.created_at.isoformat(),
        "updated_at": user.updated_at.isoformat(),
    }


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    default_error_messages = {
        "authentication_failed": "Invalid email or password.",
        "account_inactive": "This account is not active.",
    }

    def validate(self, attrs):
        email = attrs["email"]
        password = attrs["password"]
        request = self.context.get("request")
        user = authenticate(request=request, email=email, password=password)

        if user is None:
            logger.info("Login rejected.", extra={"reason": "credentials_rejected"})
            raise AuthenticationFailed(self.error_messages["authentication_failed"])

        if not user.is_active:
            raise AuthenticationFailed(self.error_messages["account_inactive"])

        attrs["user"] = user
        attrs["mfa_required"] = is_mfa_required(user) or user.mfa_enabled
        return attrs


class RefreshInputSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def validate(self, attrs):
        try:
            access, refresh = rotate_refresh_token(attrs["refresh"])
        except TokenError as exc:
            raise serializers.ValidationError(
                "Invalid or expired refresh token."
            ) from exc
        return {"access": access, "refresh": refresh}
