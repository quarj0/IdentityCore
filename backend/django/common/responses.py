import uuid

from django.http import JsonResponse
from rest_framework.response import Response


def get_request_id(request=None) -> str:
    if request is None:
        return f"req_{uuid.uuid4().hex}"

    existing = getattr(request, "_request_id", None)
    if existing:
        return existing

    header_value = request.headers.get("X-Request-Id")
    request_id = header_value or f"req_{uuid.uuid4().hex}"
    setattr(request, "_request_id", request_id)
    return request_id


def success_payload(data, request=None) -> dict:
    return {
        "success": True,
        "data": data,
        "request_id": get_request_id(request),
    }


def error_payload(code: str, message: str, details=None, request=None) -> dict:
    return {
        "success": False,
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
        },
        "request_id": get_request_id(request),
    }


def success_response(data, request=None, status=200):
    return Response(success_payload(data, request=request), status=status)


def error_response(code: str, message: str, details=None, request=None, status=400):
    return Response(
        error_payload(code, message, details=details, request=request),
        status=status,
    )


def success_json_response(data, request=None, status=200):
    return JsonResponse(success_payload(data, request=request), status=status)
