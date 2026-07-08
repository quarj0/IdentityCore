from urllib.parse import urlparse

from django.conf import settings
from django.http import HttpResponse


LOCAL_HOSTS = {"localhost", "127.0.0.1", "[::1]"}


def is_allowed_local_origin(origin: str) -> bool:
    if not origin:
        return False

    parsed = urlparse(origin)
    if parsed.scheme not in {"http", "https"}:
        return False

    hostname = parsed.hostname or parsed.netloc
    if hostname in LOCAL_HOSTS:
        return True

    return origin in set(getattr(settings, "CORS_ALLOWED_ORIGINS", []))


class LocalCorsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        origin = request.headers.get("Origin", "")

        if request.method == "OPTIONS" and is_allowed_local_origin(origin):
            response = HttpResponse(status=200)
        else:
            response = self.get_response(request)

        if is_allowed_local_origin(origin):
            response["Access-Control-Allow-Origin"] = origin
            response["Access-Control-Allow-Credentials"] = "true"
            response["Access-Control-Allow-Headers"] = ", ".join(
                getattr(
                    settings,
                    "CORS_ALLOW_HEADERS",
                    [
                        "Accept",
                        "Authorization",
                        "Content-Type",
                        "X-Requested-With",
                        "X-Session-Id",
                        "X-Device-Fingerprint",
                        "X-Request-Id",
                    ],
                )
            )
            response["Access-Control-Allow-Methods"] = ", ".join(
                getattr(
                    settings,
                    "CORS_ALLOW_METHODS",
                    ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
                )
            )
            response["Access-Control-Max-Age"] = str(
                getattr(settings, "CORS_PREFLIGHT_MAX_AGE", 86400)
            )
            vary = response.get("Vary")
            response["Vary"] = f"{vary}, Origin" if vary else "Origin"

        return response
