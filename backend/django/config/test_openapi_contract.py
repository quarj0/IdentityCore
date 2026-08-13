from copy import deepcopy

from django.http import HttpResponse
from django.test import SimpleTestCase
from django.urls import get_resolver, path

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
        changed.setdefault("components", {}).setdefault("pathItems", {})[
            "Health"
        ] = changed["paths"]["/health"]
        changed["paths"]["/health"] = {
            "$ref": "#/components/pathItems/Health"
        }

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
            if (resource["method"], resource["path"])
            == ("POST", "/verifications/")
        )
        self.assertEqual(create_verification["slug"], "create-verification")

    def test_docs_overview_preserves_effective_security(self):
        resources = public_resources(self.contract)
        by_operation = {
            (resource["method"], resource["path"]): resource
            for resource in resources
        }

        self.assertEqual(by_operation[("GET", "/countries")]["security"], [])
        self.assertEqual(
            by_operation[("POST", "/verifications/")]["security"],
            self.contract["security"],
        )
