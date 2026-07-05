from rest_framework import status
from rest_framework.exceptions import (
    AuthenticationFailed,
    NotAuthenticated,
    PermissionDenied,
)
from rest_framework.views import exception_handler

from common.responses import error_payload


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

    message = response.data.get("detail", "The request could not be processed.")
    details = (
        response.data if isinstance(response.data, dict) else {"detail": response.data}
    )
    response.data = error_payload(code, str(message), details=details, request=request)
    return response
