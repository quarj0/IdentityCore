from django.contrib import admin
from django.urls import include, path

from common.responses import success_json_response


def healthcheck(request):
    return success_json_response(
        {"status": "ok", "service": "django", "version": "1.0.0"},
        request=request,
    )


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/health", healthcheck),
    path("api/v1/auth/", include("apps.accounts.urls")),
    path("api/v1/api-clients/", include("apps.api_clients.urls")),
    path("api/v1/sessions/", include("apps.verification_sessions.urls")),
    path("api/v1/verifications/", include("apps.verifications.urls")),
]
