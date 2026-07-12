from django.contrib.auth import authenticate
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import PlatformUser


def serialize_user(user: PlatformUser) -> dict:
    user_roles = user.user_roles.select_related("role", "tenant").all()
    tenant_public_id = user.tenant.public_id if user.tenant else None
    return {
        "public_id": user.public_id,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "phone_number": user.phone_number,
        "status": user.status,
        "tenant_public_id": tenant_public_id,
        "tenant_name": user.tenant.name if user.tenant else None,
        "tenant_status": user.tenant.status if user.tenant else None,
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
            raise AuthenticationFailed(self.error_messages["authentication_failed"])

        if not user.is_active:
            raise AuthenticationFailed(self.error_messages["account_inactive"])

        refresh = RefreshToken.for_user(user)
        now = timezone.now()
        PlatformUser.objects.filter(pk=user.pk).update(last_login_at=now, updated_at=now)
        user.last_login_at = now
        user.updated_at = now
        attrs["user"] = user
        attrs["tokens"] = {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }
        return attrs


class RefreshInputSerializer(TokenRefreshSerializer):
    pass
