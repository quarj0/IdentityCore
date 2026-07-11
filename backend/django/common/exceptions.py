from rest_framework import status
from rest_framework.exceptions import (
    AuthenticationFailed,
    NotAuthenticated,
    PermissionDenied,
)
from rest_framework.views import exception_handler

from common.responses import error_payload


def _plain(value):
    if isinstance(value, dict):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(item) for item in value]
    return str(value)


def _first_message(value):
    if isinstance(value, dict):
        if "detail" in value:
            return _first_message(value["detail"])
        for item in value.values():
            message = _first_message(item)
            if message:
                return message
    elif isinstance(value, (list, tuple)):
        for item in value:
            message = _first_message(item)
            if message:
                return message
    elif value:
        return str(value)
    return "The request could not be processed."


ERROR_CODE_MAP = {
    AuthenticationFailed: "authentication_failed",
    NotAuthenticated: "authentication_failed",
    PermissionDenied: "permission_denied",
}


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return response

    request = context.get("request")
    code = ERROR_CODE_MAP.get(type(exc), "validation_error")
    if isinstance(exc, (AuthenticationFailed, NotAuthenticated)):
        response.status_code = status.HTTP_401_UNAUTHORIZED
    if response.status_code >= status.HTTP_500_INTERNAL_SERVER_ERROR:
        code = "internal_error"
    elif response.status_code == status.HTTP_404_NOT_FOUND:
        code = "resource_not_found"

    details = _plain(response.data if isinstance(response.data, dict) else {"detail": response.data})
    message = _first_message(response.data)
    response.data = error_payload(code, message, details=details, request=request)
    if getattr(exc, "clear_refresh_cookie", False):
        from apps.accounts.cookies import clear_refresh_cookie
        clear_refresh_cookie(response)
    return response
