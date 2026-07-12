from rest_framework.permissions import AllowAny
from django_countries import countries
from rest_framework.views import APIView

from common.catalog import COUNTRY_PROFILES, DOCUMENT_TYPES
from common.responses import success_response


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
        return success_response(
            {
                "api_version": "1.0",
                "base_urls": {
                    "production": "https://api.identitycore.com/api/v1",
                    "development": "http://localhost:8000/api/v1",
                },
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
                        "status": "not_started",
                        "notes": "Directory is present, but there is no SDK implementation yet.",
                    },
                    {
                        "language": "csharp",
                        "path": "sdk/C#",
                        "status": "not_started",
                        "notes": "Directory is present, but there is no SDK implementation yet.",
                    },
                ],
            },
            request=request,
        )
