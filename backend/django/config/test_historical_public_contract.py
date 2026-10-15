from django.test import SimpleTestCase
from jsonschema import Draft202012Validator

from common.pagination import MAX_PAGE_SIZE
from config.api_views import OPENAPI_SPEC_PATH
from config.openapi_contract import load_contract


class HistoricalPublicContractTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.contract = load_contract(OPENAPI_SPEC_PATH)
        cls.paths = cls.contract["paths"]
        cls.schemas = cls.contract["components"]["schemas"]

    def response_data(self, path, method="get", status="200"):
        return self.paths[path][method]["responses"][status]["content"][
            "application/json"
        ]["schema"]["properties"]["data"]

    def test_cursor_and_manual_review_pagination_are_separate(self):
        manual = self.response_data("/verifications/manual-reviews")["properties"][
            "pagination"
        ]["$ref"]
        public = self.response_data("/verifications/")["properties"]["pagination"][
            "$ref"
        ]
        self.assertNotEqual(manual, public)
        self.assertEqual(manual, "#/components/schemas/PagePagination")
        self.assertEqual(
            set(self.schemas["PagePagination"]["required"]),
            {"page", "page_size", "total", "total_pages"},
        )

    def test_upload_operations_require_bearer_and_session_id_together(self):
        schemes = self.contract["components"]["securitySchemes"]
        self.assertEqual(schemes["verificationSessionId"]["in"], "header")
        self.assertEqual(schemes["verificationSessionId"]["name"], "X-Session-Id")
        for path in [
            "/uploads/",
            "/uploads/{upload_id}/transfer",
            "/uploads/{upload_id}/complete",
        ]:
            with self.subTest(path=path):
                self.assertEqual(
                    self.paths[path]["post"]["security"],
                    [{"verificationSessionBearer": [], "verificationSessionId": []}],
                )

    def test_refresh_cookie_and_audit_bearer_match_their_authentication(self):
        self.assertEqual(
            self.paths["/auth/refresh"]["post"]["security"],
            [{"platformRefreshCookie": []}],
        )
        scheme = self.contract["components"]["securitySchemes"]["platformRefreshCookie"]
        self.assertEqual(scheme["in"], "cookie")
        for path, methods in self.paths.items():
            if path.startswith("/audit-events"):
                for method, operation in methods.items():
                    if method in {"get", "post"}:
                        with self.subTest(path=path, method=method):
                            self.assertEqual(
                                operation["security"], [{"platformUserBearer": []}]
                            )

    def test_audit_and_review_page_limits_match_backend(self):
        for path in ["/audit-events/", "/verifications/manual-reviews"]:
            parameters = {p["name"]: p for p in self.paths[path]["get"]["parameters"]}
            self.assertEqual(parameters["page"]["schema"]["minimum"], 1)
            self.assertEqual(
                parameters["page_size"]["schema"]["maximum"], MAX_PAGE_SIZE
            )

    def test_mfa_challenge_response_exposes_followup_credentials(self):
        data = self.response_data("/auth/login", "post", "202")
        self.assertEqual(data["$ref"], "#/components/schemas/PlatformUserMfaChallenge")
        self.assertEqual(
            set(self.schemas["PlatformUserMfaChallenge"]["required"]),
            {"mfa_required", "mfa_enrollment_required", "mfa_token"},
        )

    def test_replay_validation_and_metrics_authorization_are_documented(self):
        self.assertIn(
            "400",
            self.paths["/webhook-endpoints/events/{event_id}/replay"]["post"][
                "responses"
            ],
        )
        for method in ["get", "patch"]:
            self.assertIn(
                "403", self.paths["/analytics/product-metrics"][method]["responses"]
            )

    def test_client_scope_responses_can_represent_arbitrary_persisted_values(self):
        self.assertIn(
            "policies:read",
            self.schemas["APIClientCreateRequest"]["properties"]["scopes"]["items"][
                "enum"
            ],
        )
        schema = self.schemas["APIClientSummary"]["properties"]["scopes"]
        self.assertEqual(
            list(Draft202012Validator(schema).iter_errors(["custom:read"])), []
        )
