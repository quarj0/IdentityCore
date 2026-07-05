from django.contrib import admin
from django.urls import include, path
from django.views.decorators.csrf import csrf_exempt

from config.api_views import CountryProfileListView, DocumentTypeListView
from config.graphql import schema
from config.graphql_view import AuthenticatedGraphQLView
from common.responses import success_json_response


def healthcheck(request):
    return success_json_response(
        {"status": "ok", "service": "django", "version": "1.0.0"},
        request=request,
    )


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/health", healthcheck),
    path(
        "api/v1/document-types",
        DocumentTypeListView.as_view(),
        name="document-type-list",
    ),
    path(
        "api/v1/country-profiles",
        CountryProfileListView.as_view(),
        name="country-profile-list",
    ),
    path("api/v1/audit-events/", include("apps.audit.urls")),
    path("api/v1/auth/", include("apps.accounts.urls")),
    path("api/v1/api-clients/", include("apps.api_clients.urls")),
    path("api/v1/access-control/", include("apps.access_control.urls")),
    path("api/v1/consent/", include("apps.consent.urls")),
    path("api/v1/document-captures/", include("apps.document_captures.urls")),
    path("api/v1/biometrics/", include("apps.biometrics.urls")),
    path("api/v1/notifications/", include("apps.notifications.urls")),
    path("api/v1/organization/", include("apps.organizations.urls")),
    path("api/v1/policies/", include("apps.verification_policies.urls")),
    path("api/v1/providers/", include("apps.providers.urls")),
    path("api/v1/risk-assessments/", include("apps.risk.urls")),
    path("api/v1/tenant/", include("apps.tenants.urls")),
    path("api/v1/webhook-endpoints/", include("apps.webhooks.urls")),
    path("api/v1/uploads/", include("apps.uploads.urls")),
    path("api/v1/sessions/", include("apps.verification_sessions.urls")),
    path("api/v1/verifications/", include("apps.verifications.urls")),
    path("api/graphql", csrf_exempt(AuthenticatedGraphQLView.as_view(schema=schema))),
]
