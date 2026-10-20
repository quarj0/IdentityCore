"""Bounded local schemas: no network references, executable formats or NaN values."""

import hashlib
import json

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError
from rest_framework.exceptions import ValidationError

MAX_VALUE_BYTES = 256 * 1024
MAX_SCHEMA_BYTES = 32 * 1024
MAX_SCHEMA_NODES = 512
MAX_VALUE_DEPTH = 24


def canonical_json(value, *, maximum=MAX_VALUE_BYTES):
    try:
        encoded = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (ValueError, TypeError, RecursionError) as exc:
        raise ValidationError("Supply finite, serializable JSON.") from exc
    if len(encoded) > maximum:
        raise ValidationError("JSON content exceeds the allowed size.")
    pending = [(value, 0)]
    while pending:
        node, depth = pending.pop()
        if depth > MAX_VALUE_DEPTH:
            raise ValidationError("JSON content exceeds the allowed nesting depth.")
        if isinstance(node, dict):
            if any(not isinstance(k, str) for k in node):
                raise ValidationError("JSON object keys must be strings.")
            pending.extend((v, depth + 1) for v in node.values())
        elif isinstance(node, list):
            pending.extend((v, depth + 1) for v in node)
    return encoded


def digest(value):
    return hashlib.sha256(canonical_json(value)).hexdigest()


def validate_schema(definition):
    canonical_json(definition, maximum=MAX_SCHEMA_BYTES)
    if not isinstance(definition, dict) or definition.get("type") != "object":
        raise ValidationError("Schemas must describe an object.")
    # The supported subset deliberately excludes regex/backtracking, recursive
    # references and combinatorial applicators. Its validation work is bounded.
    forbidden = {
        "$ref",
        "$dynamicRef",
        "$recursiveRef",
        "pattern",
        "patternProperties",
        "allOf",
        "anyOf",
        "oneOf",
        "not",
        "if",
        "then",
        "else",
        "contains",
        "dependentSchemas",
        "unevaluatedProperties",
        "unevaluatedItems",
        "uniqueItems",
        "multipleOf",
    }
    pending = [definition]
    count = 0
    while pending:
        node = pending.pop()
        count += 1
        if count > MAX_SCHEMA_NODES:
            raise ValidationError("Schema exceeds the supported complexity.")
        if isinstance(node, dict):
            pending.extend(node.values())
        elif isinstance(node, list):
            pending.extend(node)
    # Only schema positions contain keywords. A data property named "pattern"
    # or a literal default containing "$ref" does not execute that keyword.
    pending = [definition]
    while pending:
        node = pending.pop()
        if not isinstance(node, dict):
            continue
        if forbidden.intersection(node):
            raise ValidationError(
                "Schema contains unsupported reference or expensive keywords."
            )
        for key in ("enum", "const"):
            if key in node:
                values = node[key] if key == "enum" else [node[key]]
                if (
                    not isinstance(values, list)
                    or len(values) > 64
                    or any(
                        isinstance(value, (dict, list))
                        or len(canonical_json(value)) > 256
                        for value in values
                    )
                ):
                    raise ValidationError(
                        "Schema constants must be bounded scalar values."
                    )
        for key in ("properties", "$defs", "definitions"):
            value = node.get(key)
            if isinstance(value, dict):
                pending.extend(value.values())
        for key in ("items", "additionalProperties", "propertyNames", "contentSchema"):
            if key in node:
                pending.append(node[key])
        if isinstance(node.get("prefixItems"), list):
            pending.extend(node["prefixItems"])
    try:
        Draft202012Validator.check_schema(definition)
    except SchemaError as exc:
        raise ValidationError("Schema is not valid Draft 2020-12 JSON Schema.") from exc
    return definition


def validate_payload(schema, value):
    encoded = canonical_json(value)
    if not isinstance(value, dict):
        raise ValidationError("Resource payload must be an object.")
    # Input schema was checked on creation, but persisted corruption must not
    # introduce remote lookups or unbounded validation during read/creation.
    validate_schema(schema.definition_json)
    if not Draft202012Validator(schema.definition_json).is_valid(value):
        raise ValidationError("Payload does not satisfy the selected schema version.")
    return hashlib.sha256(encoded).hexdigest()
