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
from jsonschema import Draft202012Validator, FormatChecker
from openapi_spec_validator import validate as validate_openapi
from openapi_spec_validator.validation.exceptions import OpenAPIValidationError

from common.public_api import API_VISIBILITY_ATTRIBUTE, PUBLIC_METHODS_ATTRIBUTE

HTTP_METHODS = frozenset(
    {"delete", "get", "head", "options", "patch", "post", "put", "trace"}
)
DJANGO_PARAMETER = re.compile(r"<(?:(?:[^:>]+):)?([^>]+)>")
OPENAPI_PARAMETER = re.compile(r"{([^}]+)}")
CONTRACT_MANAGED_PREFIXES = (
    "api/v1/api-clients/",
    "api/v1/audit-events/",
    "api/v1/auth/",
    "api/v1/organization/",
    "api/v1/policies/",
    "api/v1/projects/",
    "api/v1/sessions/",
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


class _UniqueKeyLoader(yaml.SafeLoader):
    """Safe YAML loader that rejects ambiguous duplicate mapping keys."""


def _construct_unique_mapping(loader, node, deep=False):
    mapping = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise OpenApiContractError(
                f"Duplicate YAML mapping key {key!r} at line {key_node.start_mark.line + 1}."
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


@lru_cache(maxsize=1)
def load_contract(path: Path) -> dict[str, Any]:
    contract = yaml.load(path.read_text(encoding="utf-8"), Loader=_UniqueKeyLoader)
    if not isinstance(contract, dict):
        raise OpenApiContractError("The OpenAPI document must be a mapping.")
    return contract


def documented_operations(contract: Mapping[str, Any]) -> set[tuple[str, str]]:
    operations: set[tuple[str, str]] = set()
    for route, raw_path_item in contract.get("paths", {}).items():
        path_item = _resolve_mapping(contract, raw_path_item)
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


def _resolve_mapping(contract: Mapping[str, Any], value: Any) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    if "$ref" not in value:
        return value
    resolved = _resolve_ref(contract, str(value["$ref"]))
    if not isinstance(resolved, Mapping):
        raise OpenApiContractError(
            f"OpenAPI reference does not resolve to a mapping: {value['$ref']}"
        )
    siblings = {key: item for key, item in value.items() if key != "$ref"}
    return {**resolved, **siblings}


def _validate_example(
    value: Any,
    schema: Mapping[str, Any],
    contract: Mapping[str, Any],
    location: str,
) -> list[str]:
    schema = _example_schema(contract, schema)
    validator = Draft202012Validator(
        dict(contract),
        format_checker=FormatChecker(),
    ).evolve(schema=dict(schema))
    errors = []
    for error in sorted(validator.iter_errors(value), key=lambda item: list(item.path)):
        suffix = "/".join(str(part) for part in error.absolute_path)
        error_location = f"{location}/{suffix}" if suffix else location
        errors.append(f"{error_location}: example {error.message}")
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
        examples = node.get("examples")
        if schema is node and isinstance(examples, list):
            for index, example in enumerate(examples):
                errors.extend(
                    _validate_example(
                        example,
                        schema,
                        contract,
                        f"{location}/examples/{index}",
                    )
                )
        elif isinstance(examples, Mapping) and isinstance(schema, Mapping):
            for name, example in examples.items():
                resolved_example = _resolve_mapping(contract, example)
                if "value" in resolved_example:
                    errors.extend(
                        _validate_example(
                            resolved_example["value"],
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
    for route, raw_path_item in contract.get("paths", {}).items():
        path_item = _resolve_mapping(contract, raw_path_item)
        expected = set(OPENAPI_PARAMETER.findall(route))
        shared = path_item.get("parameters", [])
        for method, operation in path_item.items():
            if method.lower() not in HTTP_METHODS or not isinstance(operation, Mapping):
                continue
            parameters = [*shared, *operation.get("parameters", [])]
            resolved_parameters = []
            for parameter in parameters:
                if not isinstance(parameter, Mapping):
                    continue
                resolved = _resolve_mapping(contract, parameter)
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


def _validate_security_requirements(contract: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    declared = set(contract.get("components", {}).get("securitySchemes", {}))

    def validate(requirements: Any, location: str) -> None:
        if not isinstance(requirements, list):
            return
        for index, requirement in enumerate(requirements):
            if not isinstance(requirement, Mapping):
                continue
            for scheme in requirement:
                if scheme not in declared:
                    errors.append(
                        f"{location}/{index}: unknown security scheme {scheme!r}"
                    )

    validate(contract.get("security", []), "#/security")
    for route, raw_path_item in contract.get("paths", {}).items():
        path_item = _resolve_mapping(contract, raw_path_item)
        for method, operation in path_item.items():
            if method.lower() not in HTTP_METHODS or not isinstance(operation, Mapping):
                continue
            if "security" in operation:
                validate(operation["security"], f"#/paths/{route}/{method}/security")
    return errors


def validate_contract(
    contract: Mapping[str, Any],
    *,
    implemented_operations: set[tuple[str, str]],
) -> None:
    errors: list[str] = []
    if contract.get("openapi") != "3.1.0":
        errors.append("The public contract must use OpenAPI 3.1.0.")
    try:
        validate_openapi(dict(contract))
    except OpenAPIValidationError as exc:
        errors.append(f"Invalid OpenAPI document: {exc}")
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
    errors.extend(_validate_security_requirements(contract))
    errors.extend(_validate_tree(contract))
    if errors:
        raise OpenApiContractError("\n".join(errors))


def public_resources(
    contract: Mapping[str, Any],
    *,
    slug_overrides: Mapping[tuple[str, str], str] | None = None,
) -> list[dict[str, Any]]:
    """Build the docs overview from the validated OpenAPI operations."""

    resources: list[dict[str, Any]] = []
    for route, raw_path_item in contract.get("paths", {}).items():
        path_item = _resolve_mapping(contract, raw_path_item)
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
            tags = operation.get("tags") or [segment.title()]
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
                    "category": str(tags[0]),
                    "description": str(operation.get("description", summary)),
                    "security": operation.get("security", contract.get("security", [])),
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
