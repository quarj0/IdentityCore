from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory

from django.http import HttpResponse
from django.test import SimpleTestCase
from django.urls import get_resolver, path

from common.catalog import COUNTRY_PROFILES, DOCUMENT_TYPES
from config.api_views import OPENAPI_SPEC_PATH
from config.openapi_contract import (
    OpenApiContractError,
    contract_with_operation_removed,
    documented_operations,
    load_contract,
    public_resources,
    registered_public_operations,
    validate_contract,
)


class OpenApiParityTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.contract = load_contract(OPENAPI_SPEC_PATH)
        cls.implemented = registered_public_operations()

    def test_current_public_routes_match_openapi_in_both_directions(self):
        validate_contract(self.contract, implemented_operations=self.implemented)
        self.assertEqual(documented_operations(self.contract), self.implemented)

    def test_implemented_operation_missing_from_openapi_fails(self):
        changed = contract_with_operation_removed(
            self.contract, "POST", "/verifications/"
        )

        with self.assertRaisesRegex(
            OpenApiContractError,
            "Implemented public operations missing from OpenAPI",
        ):
            validate_contract(changed, implemented_operations=self.implemented)

    def test_stale_openapi_operation_without_route_fails(self):
        changed = deepcopy(self.contract)
        changed["paths"]["/removed-resource"] = {
            "get": {
                "summary": "Removed resource",
                "responses": {"200": {"description": "Never implemented"}},
            }
        }

        with self.assertRaisesRegex(
            OpenApiContractError,
            "Stale OpenAPI operations without public routes",
        ):
            validate_contract(changed, implemented_operations=self.implemented)

    def test_unclassified_route_inside_public_prefix_fails(self):
        pattern = path(
            "api/v1/projects/unclassified-contract-route",
            lambda request: HttpResponse(),
        )
        patterns = get_resolver().url_patterns
        patterns.append(pattern)
        try:
            with self.assertRaisesRegex(
                OpenApiContractError,
                "has no public/internal marker",
            ):
                registered_public_operations()
        finally:
            patterns.remove(pattern)

    def test_invalid_schema_example_fails(self):
        changed = deepcopy(self.contract)
        changed["components"]["schemas"]["Policy"]["properties"]["id"]["example"] = 123

        with self.assertRaisesRegex(OpenApiContractError, "is not of type"):
            validate_contract(changed, implemented_operations=self.implemented)

    def test_example_schema_constraints_are_enforced(self):
        changed = deepcopy(self.contract)
        changed["paths"]["/countries"]["get"]["responses"]["200"]["content"][
            "application/json"
        ]["example"]["data"][0]["code"] = "GHA"

        with self.assertRaisesRegex(OpenApiContractError, "is too long"):
            validate_contract(changed, implemented_operations=self.implemented)

    def test_referenced_path_parameter_is_resolved(self):
        changed = deepcopy(self.contract)
        changed.setdefault("components", {}).setdefault("parameters", {})[
            "PolicyId"
        ] = {
            "name": "policy_id",
            "in": "path",
            "required": True,
            "schema": {"type": "string"},
        }
        changed["paths"]["/policies/{policy_id}"]["get"]["parameters"] = [
            {"$ref": "#/components/parameters/PolicyId"}
        ]

        validate_contract(changed, implemented_operations=self.implemented)

    def test_referenced_path_item_is_resolved(self):
        changed = deepcopy(self.contract)
        changed.setdefault("components", {}).setdefault("pathItems", {})["Health"] = (
            changed["paths"]["/health"]
        )
        changed["paths"]["/health"] = {"$ref": "#/components/pathItems/Health"}

        validate_contract(changed, implemented_operations=self.implemented)
        self.assertIn(("GET", "/health"), documented_operations(changed))

    def test_docs_overview_is_derived_from_every_documented_operation(self):
        resources = public_resources(self.contract)

        self.assertEqual(
            {(resource["method"], resource["path"]) for resource in resources},
            self.implemented,
        )

    def test_docs_overview_can_preserve_curated_slugs(self):
        resources = public_resources(
            self.contract,
            slug_overrides={("POST", "/verifications/"): "create-verification"},
        )

        create_verification = next(
            resource
            for resource in resources
            if (resource["method"], resource["path"]) == ("POST", "/verifications/")
        )
        self.assertEqual(create_verification["slug"], "create-verification")

    def test_docs_overview_preserves_effective_security(self):
        resources = public_resources(self.contract)
        by_operation = {
            (resource["method"], resource["path"]): resource for resource in resources
        }

        self.assertEqual(by_operation[("GET", "/countries")]["security"], [])
        self.assertEqual(
            by_operation[("POST", "/verifications/")]["security"],
            self.contract["security"],
        )

    def test_docs_overview_includes_request_body_examples(self):
        resources = public_resources(self.contract)
        by_operation = {
            (resource["method"], resource["path"]): resource for resource in resources
        }

        self.assertEqual(
            by_operation[("POST", "/auth/login")]["request_body"],
            {
                "required": True,
                "content_type": "application/json",
                "example": {"email": "user@example.com", "password": "string"},
            },
        )
        self.assertEqual(
            by_operation[("POST", "/uploads/{upload_id}/transfer")]["request_body"],
            {
                "required": True,
                "content_type": "multipart/form-data",
                "example": {"file": "/path/to/file"},
            },
        )

    def test_docs_overview_preserves_required_operation_headers(self):
        resources = public_resources(self.contract)
        by_operation = {
            (resource["method"], resource["path"]): resource for resource in resources
        }

        self.assertEqual(
            by_operation[("POST", "/projects/{project_id}/workflows:instantiate")][
                "required_headers"
            ],
            ["Idempotency-Key"],
        )
        self.assertEqual(by_operation[("GET", "/countries")]["required_headers"], [])

    def test_policy_document_types_match_the_accepted_catalog(self):
        expected = {item["code"] for item in DOCUMENT_TYPES}
        schemas = self.contract["components"]["schemas"]

        self.assertEqual(
            set(
                schemas["VerificationPolicyCreateRequest"]["properties"][
                    "required_document_types"
                ]["items"]["enum"]
            ),
            expected,
        )
        self.assertEqual(
            set(
                schemas["Policy"]["properties"]["required_document_types"]["items"][
                    "enum"
                ]
            ),
            expected,
        )
        create_policy = next(
            resource
            for resource in public_resources(self.contract)
            if (resource["method"], resource["path"]) == ("POST", "/policies/")
        )
        self.assertEqual(
            create_policy["request_body"]["example"]["required_document_types"],
            ["national_id"],
        )

    def test_policy_threshold_ordering_constraint_is_documented(self):
        schema = self.contract["components"]["schemas"][
            "VerificationPolicyCreateRequest"
        ]

        self.assertIn(
            "manual_review_threshold must be less than or equal to face_match_threshold",
            schema["description"],
        )

    def test_public_mfa_flow_and_refresh_origin_failure_are_documented(self):
        for route in (
            "/auth/mfa/enroll",
            "/auth/mfa/enroll/confirm",
            "/auth/mfa/challenge",
        ):
            with self.subTest(route=route):
                operation = self.contract["paths"][route]["post"]
                self.assertEqual(operation["security"], [])
                self.assertIn("200", operation["responses"])
                self.assertIn("401", operation["responses"])
                self.assertIn(("POST", route), self.implemented)

        self.assertIn(
            "403",
            self.contract["paths"]["/auth/refresh"]["post"]["responses"],
        )

    def test_policy_create_is_part_of_public_parity(self):
        self.assertIn(("POST", "/policies/"), self.implemented)
        self.assertIn(("POST", "/policies/"), documented_operations(self.contract))

    def test_session_success_responses_are_typed(self):
        expected = {
            (
                "/sessions/mobile-handoff/redeem",
                "VerificationMobileHandoffRedeemResponse",
            ),
            ("/sessions/{session_id}", "VerificationSessionResponse"),
            ("/sessions/{session_id}/consent", "VerificationSessionConsentResponse"),
            ("/sessions/{session_id}/documents", "VerificationSessionDocumentResponse"),
            ("/sessions/{session_id}/selfies", "VerificationSessionSelfieResponse"),
            ("/sessions/{session_id}/liveness", "VerificationSessionLivenessResponse"),
            (
                "/sessions/{session_id}/liveness/challenge",
                "VerificationSessionLivenessChallengeResponse",
            ),
            ("/sessions/{session_id}/status", "VerificationSessionStatusResponse"),
            (
                "/sessions/{session_id}/mobile-handoff",
                "VerificationMobileHandoffResponse",
            ),
        }
        for route, schema_name in expected:
            method = (
                "get"
                if route.endswith("{session_id}") or route.endswith("/status")
                else "post"
            )
            schema = self.contract["paths"][route][method]["responses"]["200"][
                "content"
            ]["application/json"]["schema"]
            self.assertEqual(
                schema["properties"]["data"]["$ref"],
                f"#/components/schemas/{schema_name}",
            )

    def test_trace_is_included_in_stale_operation_detection(self):
        changed = deepcopy(self.contract)
        changed["paths"]["/health"]["trace"] = {
            "summary": "Trace health",
            "security": [],
            "responses": {"200": {"description": "Trace result"}},
        }

        with self.assertRaisesRegex(
            OpenApiContractError, "Stale OpenAPI operations without public routes"
        ):
            validate_contract(changed, implemented_operations=self.implemented)

    def test_empty_tags_use_path_category_fallback(self):
        changed = deepcopy(self.contract)
        changed["paths"]["/health"]["get"]["tags"] = []

        health = next(
            resource
            for resource in public_resources(changed)
            if (resource["method"], resource["path"]) == ("GET", "/health")
        )

        self.assertEqual(health["category"], "Health")

    def test_unknown_security_scheme_fails_document_validation(self):
        changed = deepcopy(self.contract)
        changed["paths"]["/health"]["get"]["security"] = [{"missingSecurityScheme": []}]

        with self.assertRaisesRegex(OpenApiContractError, "unknown security scheme"):
            validate_contract(changed, implemented_operations=self.implemented)

    def test_schema_examples_array_is_validated_without_crashing(self):
        changed = deepcopy(self.contract)
        changed["components"]["schemas"]["Policy"]["properties"]["id"]["examples"] = [
            "pol_123",
            "pol_456",
        ]

        validate_contract(changed, implemented_operations=self.implemented)

    def test_invalid_schema_examples_array_value_fails(self):
        changed = deepcopy(self.contract)
        changed["components"]["schemas"]["Policy"]["properties"]["id"]["examples"] = [
            123
        ]

        with self.assertRaisesRegex(OpenApiContractError, "is not of type"):
            validate_contract(changed, implemented_operations=self.implemented)

    def test_duplicate_yaml_mapping_key_fails_loading(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "duplicate.yaml"
            path.write_text("openapi: 3.1.0\npaths: {}\npaths: {}\n", encoding="utf-8")

            with self.assertRaisesRegex(
                OpenApiContractError, "Duplicate YAML mapping key 'paths'"
            ):
                load_contract(path)

    def test_verification_session_request_schemas_match_required_inputs(self):
        schemas = self.contract["components"]["schemas"]

        self.assertEqual(
            set(schemas["VerificationSessionConsentRequest"]["required"]),
            {"accepted"},
        )
        self.assertIs(
            schemas["VerificationSessionConsentRequest"]["properties"]["accepted"][
                "const"
            ],
            True,
        )
        self.assertEqual(
            set(schemas["VerificationSessionDocumentRequest"]["required"]),
            {"document_type", "country_code", "captures"},
        )
        self.assertEqual(
            set(schemas["VerificationSessionSelfieRequest"]["required"]),
            {"capture_type", "upload_id"},
        )
        self.assertEqual(
            set(schemas["VerificationSessionLivenessRequest"]["required"]),
            {"liveness_type", "selfie_capture_id"},
        )
        document_example = schemas["VerificationSessionDocumentRequest"]["example"]
        country = next(
            profile
            for profile in COUNTRY_PROFILES
            if profile["code"] == document_example["country_code"]
        )
        document = next(
            item
            for item in country["supported_document_types"]
            if item["document_type"] == document_example["document_type"]
        )
        self.assertIn(
            document_example["captures"][0]["side"], document["capture_sides"]
        )
        document_resource = next(
            resource
            for resource in public_resources(self.contract)
            if (resource["method"], resource["path"])
            == ("POST", "/sessions/{session_id}/documents")
        )
        self.assertEqual(document_resource["request_body"]["example"], document_example)

    def test_referenced_media_example_is_validated_against_its_schema(self):
        changed = deepcopy(self.contract)
        changed.setdefault("components", {}).setdefault("examples", {})[
            "InvalidCountry"
        ] = {"value": {"code": "GHA", "name": "Ghana"}}
        media_type = changed["paths"]["/countries"]["get"]["responses"]["200"][
            "content"
        ]["application/json"]
        media_type["schema"] = {
            "type": "object",
            "required": ["code", "name"],
            "properties": {
                "code": {"type": "string", "maxLength": 2},
                "name": {"type": "string"},
            },
        }
        media_type.pop("example", None)
        media_type["examples"] = {
            "invalid": {"$ref": "#/components/examples/InvalidCountry"}
        }

        with self.assertRaisesRegex(OpenApiContractError, "is too long"):
            validate_contract(changed, implemented_operations=self.implemented)
