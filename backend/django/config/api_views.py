from pathlib import Path

from django.http import HttpResponse
from rest_framework.permissions import AllowAny
from django_countries import countries
from rest_framework.views import APIView

from common.catalog import COUNTRY_PROFILES, DOCUMENT_TYPES
from common.responses import success_response
from config.openapi_contract import load_contract, public_resources

PROJECT_ROOT = Path(__file__).resolve().parents[3]
OPENAPI_SPEC_PATH = PROJECT_ROOT / "docs" / "openapi" / "identitycore-public-api.yaml"


class DocumentTypeListView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        return success_response(DOCUMENT_TYPES, request=request)


class CountryProfileListView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        return success_response(COUNTRY_PROFILES, request=request)


class CountryListView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        data = [{"code": code, "name": str(name)} for code, name in countries]
        return success_response(data, request=request)


class PublicDocsOverviewView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        overview = {
                "api_version": "1.0",
                "base_urls": {
                    "production": "https://api.identitycore.com/api/v1",
                    "development": "http://localhost:8000/api/v1",
                },
                "spec_url": "/api/v1/docs/openapi.yaml",
                "authentication": {
                    "public_rest": {
                        "headers": [
                            "Authorization: Bearer <api_secret>",
                            "X-Client-Id: <client_id>",
                            "X-Request-Id: <unique_request_id>",
                        ],
                        "optional_headers": [
                            "X-Signature: <request_signature>",
                            "X-Timestamp: <unix_timestamp>",
                        ],
                    }
                },
                "response_envelope": {
                    "success": True,
                    "data": {},
                    "request_id": "req_01JABC...",
                },
                "resources": [
                    {
                        "slug": "health",
                        "name": "Health",
                        "method": "GET",
                        "path": "/health",
                        "category": "System",
                        "description": "Service availability check.",
                    },
                    {
                        "slug": "list-policies",
                        "name": "Policies",
                        "method": "GET",
                        "path": "/policies/",
                        "category": "Policies",
                        "description": "List active verification policies/templates.",
                    },
                    {
                        "slug": "get-policy",
                        "name": "Policy detail",
                        "method": "GET",
                        "path": "/policies/{policy_id}",
                        "category": "Policies",
                        "description": "Retrieve a single active verification policy/template.",
                    },
                    {
                        "slug": "list-verifications",
                        "name": "Verifications",
                        "method": "GET",
                        "path": "/verifications/",
                        "category": "Verifications",
                        "description": "List tenant-scoped verifications.",
                    },
                    {
                        "slug": "create-verification",
                        "name": "Verification create",
                        "method": "POST",
                        "path": "/verifications/",
                        "category": "Verifications",
                        "description": "Create a hosted verification request.",
                    },
                    {
                        "slug": "get-verification",
                        "name": "Verification detail",
                        "method": "GET",
                        "path": "/verifications/{verification_id}",
                        "category": "Verifications",
                        "description": "Retrieve verification status and evidence metadata.",
                    },
                    {
                        "slug": "get-verification-result",
                        "name": "Verification result",
                        "method": "GET",
                        "path": "/verifications/{verification_id}/result",
                        "category": "Verifications",
                        "description": "Retrieve the stable, versioned verification result and check provenance.",
                    },
                    {
                        "slug": "cancel-verification",
                        "name": "Verification cancel",
                        "method": "POST",
                        "path": "/verifications/{verification_id}/cancel",
                        "category": "Verifications",
                        "description": "Cancel an in-flight verification.",
                    },
                    {
                        "slug": "resend-verification-link",
                        "name": "Verification resend link",
                        "method": "POST",
                        "path": "/verifications/{verification_id}/resend-link",
                        "category": "Verifications",
                        "description": "Issue a fresh hosted verification link.",
                    },
                    {
                        "slug": "evidence-report",
                        "name": "Evidence report",
                        "method": "GET",
                        "path": "/verifications/{verification_id}/evidence-report",
                        "category": "Verifications",
                        "description": "Get evidence-report download URLs.",
                    },
                    {
                        "slug": "create-upload",
                        "name": "Create upload",
                        "method": "POST",
                        "path": "/uploads/",
                        "category": "Uploads",
                        "description": "Create a temporary upload transfer.",
                    },
                    {
                        "slug": "transfer-upload",
                        "name": "Transfer upload",
                        "method": "POST",
                        "path": "/uploads/{upload_id}/transfer",
                        "category": "Uploads",
                        "description": "Transfer file bytes into temporary storage.",
                    },
                    {
                        "slug": "complete-upload",
                        "name": "Complete upload",
                        "method": "POST",
                        "path": "/uploads/{upload_id}/complete",
                        "category": "Uploads",
                        "description": (
                            "Validate and finalize a direct object-storage upload."
                        ),
                    },
                    {
                        "slug": "organization-profile",
                        "name": "Organization profile",
                        "method": "GET",
                        "path": "/organization/me/",
                        "category": "Organization",
                        "description": "Get the current organization profile.",
                    },
                    {
                        "slug": "organization-branding-upload",
                        "name": "Upload organization branding",
                        "method": "POST",
                        "path": "/organization/me/branding/assets/upload/",
                        "category": "Organization",
                        "description": "Upload an organization branding asset.",
                    },
                    {
                        "slug": "organization-document-upload",
                        "name": "Upload verification document",
                        "method": "POST",
                        "path": "/organization/me/verification-documents/upload/",
                        "category": "Organization",
                        "description": "Create an organization verification document upload.",
                    },
                    {
                        "slug": "organization-document-complete",
                        "name": "Complete verification document",
                        "method": "POST",
                        "path": "/organization/me/verification-documents/{document_id}/complete/",
                        "category": "Organization",
                        "description": "Complete an organization verification document upload.",
                    },
                    {
                        "slug": "organization-document-delete",
                        "name": "Delete verification document",
                        "method": "DELETE",
                        "path": "/organization/me/verification-documents/{document_id}/",
                        "category": "Organization",
                        "description": "Delete an organization verification document.",
                    },
                    {
                        "slug": "organization-document-content-upload",
                        "name": "Transfer verification document bytes",
                        "method": "PUT",
                        "path": "/organization/me/verification-documents/{document_id}/content/",
                        "category": "Organization",
                        "description": "Transfer PDF bytes for an initiated verification document.",
                    },
                    {
                        "slug": "suspend-workspace",
                        "name": "Suspend workspace",
                        "method": "POST",
                        "path": "/organization/me/suspend",
                        "category": "Organization",
                        "description": "Suspend the current workspace and revoke active credentials and sessions.",
                    },
                    {
                        "slug": "list-projects",
                        "name": "List projects",
                        "method": "GET",
                        "path": "/projects/",
                        "category": "Projects",
                        "description": "List workspace projects and environments.",
                    },
                    {
                        "slug": "get-project",
                        "name": "Retrieve project",
                        "method": "GET",
                        "path": "/projects/{project_id}",
                        "category": "Projects",
                        "description": "Retrieve a project.",
                    },
                    {
                        "slug": "project-action",
                        "name": "Update project status",
                        "method": "POST",
                        "path": "/projects/{project_id}/{action}",
                        "category": "Projects",
                        "description": "Suspend or reactivate a project.",
                    },
                    {
                        "slug": "instantiate-project-workflow",
                        "name": "Instantiate project workflow",
                        "method": "POST",
                        "path": "/projects/{project_id}/workflows:instantiate",
                        "category": "Projects",
                        "description": "Create an idempotent workflow from a published template.",
                    },
                    {
                        "slug": "list-api-clients",
                        "name": "List API clients",
                        "method": "GET",
                        "path": "/api-clients/",
                        "category": "API clients",
                        "description": "List workspace API clients.",
                    },
                    {
                        "slug": "get-api-client",
                        "name": "Retrieve API client",
                        "method": "GET",
                        "path": "/api-clients/{client_id}",
                        "category": "API clients",
                        "description": "Retrieve an API client.",
                    },
                    {
                        "slug": "api-client-action",
                        "name": "Update API client status",
                        "method": "POST",
                        "path": "/api-clients/{client_id}/{action}",
                        "category": "API clients",
                        "description": "Rotate, revoke, or reactivate an API client.",
                    },
                    {
                        "slug": "list-webhook-endpoints",
                        "name": "List webhook endpoints",
                        "method": "GET",
                        "path": "/webhook-endpoints/",
                        "category": "Webhooks",
                        "description": "List configured webhook endpoints.",
                    },
                    {
                        "slug": "get-webhook-endpoint",
                        "name": "Retrieve webhook endpoint",
                        "method": "GET",
                        "path": "/webhook-endpoints/{webhook_id}",
                        "category": "Webhooks",
                        "description": "Retrieve a webhook endpoint.",
                    },
                    {
                        "slug": "test-webhook-endpoint",
                        "name": "Test webhook endpoint",
                        "method": "POST",
                        "path": "/webhook-endpoints/{webhook_id}/test",
                        "category": "Webhooks",
                        "description": "Queue a test webhook delivery.",
                    },
                    {
                        "slug": "webhook-endpoint-action",
                        "name": "Update webhook endpoint status",
                        "method": "POST",
                        "path": "/webhook-endpoints/{webhook_id}/{action}",
                        "category": "Webhooks",
                        "description": "Enable, disable, or rotate a webhook endpoint.",
                    },
                    {
                        "slug": "list-manual-reviews",
                        "name": "List manual reviews",
                        "method": "GET",
                        "path": "/verifications/manual-reviews",
                        "category": "Manual reviews",
                        "description": "List verifications awaiting manual review.",
                    },
                    {
                        "slug": "decide-manual-review",
                        "name": "Decide manual review",
                        "method": "POST",
                        "path": "/verifications/manual-reviews/{verification_id}/decision",
                        "category": "Manual reviews",
                        "description": "Record a manual review decision.",
                    },
                    {
                        "slug": "download-evidence-report",
                        "name": "Download evidence report",
                        "method": "GET",
                        "path": "/verifications/{verification_id}/evidence-report/download",
                        "category": "Verifications",
                        "description": "Download a verification evidence report.",
                    },
                    {
                        "slug": "download-evidence-report-pdf",
                        "name": "Download evidence report PDF",
                        "method": "GET",
                        "path": "/verifications/{verification_id}/evidence-report/download.pdf",
                        "category": "Verifications",
                        "description": "Download a verification evidence report as PDF.",
                    },
                ],
                "sdk_status": [
                    {
                        "language": "python",
                        "path": "sdk/python",
                        "status": "ready",
                        "notes": "Implemented and covered by tests for policies and verifications.",
                    },
                    {
                        "language": "javascript",
                        "path": "sdk/javascript",
                        "status": "ready",
                        "notes": "Implemented and covered by tests for policies and verifications.",
                    },
                    {
                        "language": "java",
                        "path": "sdk/java",
                        "status": "ready",
                        "notes": "Implemented with retries, pagination, idempotency, webhook verification, and tests.",
                    },
                    {
                        "language": "csharp",
                        "path": "sdk/dotnet",
                        "status": "ready",
                        "notes": "Implemented with retries, pagination, idempotency, webhook verification, and tests.",
                    },
                ],
            }
        curated_slugs = {
            (resource["method"], resource["path"]): resource["slug"]
            for resource in overview["resources"]
        }
        overview["resources"] = public_resources(
            load_contract(OPENAPI_SPEC_PATH), slug_overrides=curated_slugs
        )
        return success_response(overview, request=request)


class OpenApiSpecView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        spec = OPENAPI_SPEC_PATH.read_text(encoding="utf-8")
        return HttpResponse(spec, content_type="text/yaml; charset=utf-8")
