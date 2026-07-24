from django.conf import settings
from rest_framework.exceptions import PermissionDenied

from common.cors import is_allowed_local_origin


def require_trusted_cookie_origin(request) -> None:
    origin = request.headers.get("Origin", "")
    if origin and not is_allowed_local_origin(origin):
        raise PermissionDenied("Untrusted request origin.")


SESSION_SCOPE_HEADER = "X-IdentityCore-Session-Scope"
SESSION_SCOPE_COOKIE_SUFFIXES = {
    "dashboard": "dashboard",
    "platform_admin": "platform_admin",
}


def get_refresh_cookie_name(request) -> str:
    """Return a first-party app-specific refresh cookie name when requested."""
    scope = request.headers.get(SESSION_SCOPE_HEADER, "")
    suffix = SESSION_SCOPE_COOKIE_SUFFIXES.get(scope)
    if not suffix:
        return settings.AUTH_REFRESH_COOKIE_NAME
    return f"{settings.AUTH_REFRESH_COOKIE_NAME}_{suffix}"


def set_refresh_cookie(response, refresh_token: str, *, cookie_name: str | None = None) -> None:
    response.set_cookie(
        cookie_name or settings.AUTH_REFRESH_COOKIE_NAME,
        refresh_token,
        httponly=True,
        secure=settings.AUTH_REFRESH_COOKIE_SECURE,
        samesite=settings.AUTH_REFRESH_COOKIE_SAMESITE,
        domain=settings.AUTH_REFRESH_COOKIE_DOMAIN,
        path=settings.AUTH_REFRESH_COOKIE_PATH,
        max_age=60 * 60 * 24 * 7,
    )


def clear_refresh_cookie(response, *, cookie_name: str | None = None) -> None:
    response.delete_cookie(
        cookie_name or settings.AUTH_REFRESH_COOKIE_NAME,
        domain=settings.AUTH_REFRESH_COOKIE_DOMAIN,
        path=settings.AUTH_REFRESH_COOKIE_PATH,
        samesite=settings.AUTH_REFRESH_COOKIE_SAMESITE,
    )
