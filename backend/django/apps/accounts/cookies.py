from django.conf import settings
from rest_framework.exceptions import PermissionDenied

from common.cors import is_allowed_local_origin


def require_trusted_cookie_origin(request) -> None:
    origin = request.headers.get("Origin", "")
    if origin and not is_allowed_local_origin(origin):
        raise PermissionDenied("Untrusted request origin.")


def set_refresh_cookie(response, refresh_token: str) -> None:
    response.set_cookie(
        settings.AUTH_REFRESH_COOKIE_NAME,
        refresh_token,
        httponly=True,
        secure=settings.AUTH_REFRESH_COOKIE_SECURE,
        samesite=settings.AUTH_REFRESH_COOKIE_SAMESITE,
        domain=settings.AUTH_REFRESH_COOKIE_DOMAIN,
        path=settings.AUTH_REFRESH_COOKIE_PATH,
        max_age=60 * 60 * 24 * 7,
    )


def clear_refresh_cookie(response) -> None:
    response.delete_cookie(
        settings.AUTH_REFRESH_COOKIE_NAME,
        domain=settings.AUTH_REFRESH_COOKIE_DOMAIN,
        path=settings.AUTH_REFRESH_COOKIE_PATH,
        samesite=settings.AUTH_REFRESH_COOKIE_SAMESITE,
    )
