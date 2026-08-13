"""Validation for the implemented IdentityCore public REST contract."""

from __future__ import annotations

import re
from collections.abc import Mapping
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from django.urls import URLPattern, URLResolver, get_resolver

from common.public_api import API_VISIBILITY_ATTRIBUTE, PUBLIC_METHODS_ATTRIBUTE

HTTP_METHODS = frozenset({"delete", "get", "head", "options", "patch", "post", "put"})
DJANGO_PARAMETER = re.compile(r"<(?:(?:[^:>]+):)?([^>]+)>")
OPENAPI_PARAMETER = re.compile(r"{([^}]+)}")
CONTRACT_MANAGED_PREFIXES = (
    "api/v1/api-clients/",
    "api/v1/organization/",
    "api/v1/policies/",
    "api/v1/projects/",
    "api/v1/uploads/",
    "api/v1/verifications/",
    "api/v1/webhook-endpoints/",
)
CONTRACT_MANAGED_ROUTES = frozenset(
    {
        "api/v1/countries",
        "api/v1/country-profiles",
        "api/v1/document-types",
        "api/v1/health",
    }
)


class OpenApiContractError(ValueError):
    """Raised when the OpenAPI document and implemented public API diverge."""


@lru_cache(maxsize=1)
def load_contract(path: Path) -> dict[str, Any]:
    contract = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(contract, dict):
        raise OpenApiContractError("The OpenAPI document must be a mapping.")
    return contract


def documented_operations(contract: Mapping[str, Any]) -> set[tuple[str, str]]:
    operations: set[tuple[str, str]] = set()
    for route, path_item in contract.get("paths", {}).items():
        if not isinstance(path_item, Mapping):
            continue
        for method in path_item:
            if method.lower() in HTTP_METHODS:
                operations.add((method.upper(), route))
    return operations


def _route_to_openapi(route: str) -> str:
    route = DJANGO_PARAMETER.sub(lambda match: "{" + match.group(1) + "}", route)
    prefix = "api/v1"
    if not route.startswith(prefix):
        raise OpenApiContractError(f"Public route is outside /api/v1: {route}")
    return "/" + route[len(prefix) :].lstrip("/")


def registered_public_operations() -> set[tuple[str, str]]:
    operations: set[tuple[str, str]] = set()

    def visit(patterns: list[Any], prefix: str = "") -> None:
        for pattern in patterns:
            route = prefix + str(pattern.pattern)
            if isinstance(pattern, URLResolver):
                visit(pattern.url_patterns, route)
                continue
            if not isinstance(pattern, URLPattern):
                continue
            visibility = getattr(pattern.callback, API_VISIBILITY_ATTRIBUTE, None)
            managed = route in CONTRACT_MANAGED_ROUTES or route.startswith(
                CONTRACT_MANAGED_PREFIXES
            )
            if managed and visibility not in {"internal", "public"}:
                raise OpenApiContractError(
                    f"Contract-managed API route has no public/internal marker: {route}"
                )
            methods = getattr(pattern.callback, PUBLIC_METHODS_ATTRIBUTE, ())
            view_class = getattr(pattern.callback, "view_class", None)
            if view_class is not None:
                missing_handlers = [
                    method
                    for method in methods
                    if not callable(getattr(view_class, method.lower(), None))
                ]
                if missing_handlers:
                    raise OpenApiContractError(
                        f"Public route {route} declares methods without view handlers: "
                        f"{sorted(missing_handlers)}"
                    )
            operations.update((method, _route_to_openapi(route)) for method in methods)

    visit(get_resolver().url_patterns)
    return operations


def _resolve_ref(contract: Mapping[str, Any], reference: str) -> Any:
    if not reference.startswith("#/"):
        raise OpenApiContractError(
            f"Only local OpenAPI references are supported: {reference}"
        )
    value: Any = contract
    for raw_part in reference[2:].split("/"):
        part = raw_part.replace("~1", "/").replace("~0", "~")
        if not isinstance(value, Mapping) or part not in value:
            raise OpenApiContractError(f"Unresolved OpenAPI reference: {reference}")
        value = value[part]
    return value


def _example_schema(
    contract: Mapping[str, Any], schema: Mapping[str, Any]
) -> Mapping[str, Any]:
    if "$ref" in schema:
        resolved = _resolve_ref(contract, str(schema["$ref"]))
        if isinstance(resolved, Mapping):
            siblings = {key: value for key, value in schema.items() if key != "$ref"}
            return {**resolved, **siblings}
    return schema


def _validate_example(
    value: Any,
    schema: Mapping[str, Any],
    contract: Mapping[str, Any],
    location: str,
) -> list[str]:
    schema = _example_schema(contract, schema)
    errors: list[str] = []
    for combined_schema in schema.get("allOf", []):
        if isinstance(combined_schema, Mapping):
            errors.extend(_validate_example(value, combined_schema, contract, location))
    expected = schema.get("type")
    allowed_types = set(expected) if isinstance(expected, list) else {expected}
    allowed_types.discard(None)
    if value is None and "null" in allowed_types:
        return errors
    type_matches = {
        "array": lambda item: isinstance(item, list),
        "boolean": lambda item: isinstance(item, bool),
        "integer": lambda item: isinstance(item, int) and not isinstance(item, bool),
        "number": lambda item: isinstance(item, (int, float))
        and not isinstance(item, bool),
        "object": lambda item: isinstance(item, Mapping),
        "string": lambda item: isinstance(item, str),
    }
    if allowed_types and not any(
        type_matches[kind](value) for kind in allowed_types if kind in type_matches
    ):
        errors.append(f"{location}: example {value!r} does not match type {expected!r}")
        return errors
    if "const" in schema and value != schema["const"]:
        errors.append(
            f"{location}: example {value!r} does not match const {schema['const']!r}"
        )
    if "enum" in schema and value not in schema["enum"]:
        errors.append(
            f"{location}: example {value!r} is not in enum {schema['enum']!r}"
        )
    if isinstance(value, Mapping):
        required = set(schema.get("required", []))
        missing = sorted(required - value.keys())
        if missing:
            errors.append(f"{location}: example is missing required fields {missing}")
        properties = schema.get("properties", {})
        for key, child in value.items():
            child_schema = properties.get(key)
            if isinstance(child_schema, Mapping):
                errors.extend(
                    _validate_example(
                        child, child_schema, contract, f"{location}/{key}"
                    )
                )
            elif schema.get("additionalProperties") is False:
                errors.append(f"{location}: example has unknown field {key!r}")
    if isinstance(value, list) and isinstance(schema.get("items"), Mapping):
        for index, child in enumerate(value):
            errors.extend(
                _validate_example(
                    child, schema["items"], contract, f"{location}/{index}"
                )
            )
    return errors


def _validate_tree(contract: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []

    def visit(node: Any, location: str) -> None:
        if isinstance(node, list):
            for index, value in enumerate(node):
                visit(value, f"{location}/{index}")
            return
        if not isinstance(node, Mapping):
            return
        if "$ref" in node:
            try:
                _resolve_ref(contract, str(node["$ref"]))
            except OpenApiContractError as exc:
                errors.append(f"{location}: {exc}")
        schema = node.get("schema", node)
        if "example" in node and isinstance(schema, Mapping):
            errors.extend(
                _validate_example(node["example"], schema, contract, location)
            )
        if "examples" in node and isinstance(schema, Mapping):
            for name, example in node["examples"].items():
                if isinstance(example, Mapping) and "value" in example:
                    errors.extend(
                        _validate_example(
                            example["value"],
                            schema,
                            contract,
                            f"{location}/examples/{name}",
                        )
                    )
        for key, value in node.items():
            if key != "example":
                visit(value, f"{location}/{key}")

    visit(contract, "#")
    return errors


def _validate_path_parameters(contract: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    for route, path_item in contract.get("paths", {}).items():
        expected = set(OPENAPI_PARAMETER.findall(route))
        shared = (
            path_item.get("parameters", []) if isinstance(path_item, Mapping) else []
        )
        for method, operation in path_item.items():
            if method.lower() not in HTTP_METHODS or not isinstance(operation, Mapping):
                continue
            parameters = [*shared, *operation.get("parameters", [])]
            resolved_parameters = []
            for parameter in parameters:
                if not isinstance(parameter, Mapping):
                    continue
                resolved = _example_schema(contract, parameter)
                resolved_parameters.append(resolved)
            declared = {
                parameter.get("name")
                for parameter in resolved_parameters
                if parameter.get("in") == "path"
            }
            if declared != expected:
                errors.append(
                    f"{method.upper()} {route}: path parameters are {sorted(declared)}; "
                    f"expected {sorted(expected)}"
                )
            for parameter in resolved_parameters:
                if (
                    parameter.get("in") == "path"
                    and parameter.get("required") is not True
                ):
                    errors.append(
                        f"{method.upper()} {route}: path parameter "
                        f"{parameter.get('name')!r} must be required"
                    )
    return errors


def validate_contract(
    contract: Mapping[str, Any],
    *,
    implemented_operations: set[tuple[str, str]],
) -> None:
    errors: list[str] = []
    if contract.get("openapi") != "3.1.0":
        errors.append("The public contract must use OpenAPI 3.1.0.")
    documented = documented_operations(contract)
    undocumented = sorted(implemented_operations - documented)
    stale = sorted(documented - implemented_operations)
    if undocumented:
        errors.append(
            f"Implemented public operations missing from OpenAPI: {undocumented}"
        )
    if stale:
        errors.append(f"Stale OpenAPI operations without public routes: {stale}")
    errors.extend(_validate_path_parameters(contract))
    errors.extend(_validate_tree(contract))
    if errors:
        raise OpenApiContractError("\n".join(errors))


def public_resources(
    contract: Mapping[str, Any],
    *,
    slug_overrides: Mapping[tuple[str, str], str] | None = None,
) -> list[dict[str, str]]:
    """Build the docs overview from the validated OpenAPI operations."""

    resources: list[dict[str, str]] = []
    for route, path_item in contract.get("paths", {}).items():
        for method, operation in path_item.items():
            if method.lower() not in HTTP_METHODS or not isinstance(operation, Mapping):
                continue
            summary = str(operation.get("summary", f"{method.upper()} {route}")).rstrip(
                "."
            )
            segment = next((part for part in route.split("/") if part), "System")
            operation_key = (method.upper(), route)
            fallback_slug = (
                slug_overrides.get(operation_key)
                if slug_overrides is not None
                else None
            ) or f"{method}-{route}"
            resources.append(
                {
                    "slug": str(operation.get("operationId", fallback_slug))
                    .strip("/")
                    .replace("/", "-")
                    .replace("{", "")
                    .replace("}", "")
                    .replace(":", "-"),
                    "name": summary,
                    "method": method.upper(),
                    "path": route,
                    "category": str(operation.get("tags", [segment.title()])[0]),
                    "description": str(operation.get("description", summary)),
                }
            )
    return resources


def contract_with_operation_removed(
    contract: Mapping[str, Any], method: str, route: str
) -> dict[str, Any]:
    """Test helper used to prove undocumented-route failures."""

    changed = deepcopy(contract)
    del changed["paths"][route][method.lower()]
    return changed
