#!/usr/bin/env python3
"""Generate typed SDK models from the public OpenAPI contract."""

from __future__ import annotations
import argparse
import difflib
from pathlib import Path
from typing import Any
import yaml

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "docs/openapi/identitycore-public-api.yaml"
OUTPUTS = {
    "python": ROOT / "sdk/python/identitycore/models.py",
    "typescript": ROOT / "sdk/javascript/src/models.d.ts",
    "java": ROOT / "sdk/java/src/main/java/io/identitycore/models/GeneratedModels.java",
    "dotnet": ROOT / "sdk/dotnet/src/IdentityCore/GeneratedModels.cs",
}
FIXTURES = {
    "VerificationCreateResponse": ROOT
    / "sdk/fixtures/verification-create-response.json"
}
HEADER = "Generated from docs/openapi/identitycore-public-api.yaml. DO NOT EDIT."


def resolve(schema: dict[str, Any], schemas: dict[str, Any]) -> dict[str, Any]:
    if "allOf" not in schema:
        return schema
    result: dict[str, Any] = {"type": "object", "properties": {}, "required": []}
    for item in schema["allOf"]:
        item = schemas[item["$ref"].rsplit("/", 1)[-1]] if "$ref" in item else item
        item = resolve(item, schemas)
        result["properties"].update(item.get("properties", {}))
        result["required"].extend(item.get("required", []))
    return result


def kind(s: dict[str, Any]) -> tuple[str, bool]:
    value = s.get("type", "object")
    return (
        (next((x for x in value if x != "null"), "object"), "null" in value)
        if isinstance(value, list)
        else (value, False)
    )


def ref(s: dict[str, Any]) -> str | None:
    return s.get("$ref", "").rsplit("/", 1)[-1] or None


def pytype(s: dict[str, Any]) -> str:
    if r := ref(s):
        return r
    k, n = kind(s)
    base = {
        "string": "str",
        "integer": "int",
        "number": "float",
        "boolean": "bool",
    }.get(k)
    if k == "array":
        base = f"list[{pytype(s.get('items',{}))}]"
    base = base or "dict[str, Any]"
    return f"Optional[{base}]" if n else base


def tstype(s: dict[str, Any]) -> str:
    if r := ref(s):
        return r
    k, n = kind(s)
    base = {
        "string": "string",
        "integer": "number",
        "number": "number",
        "boolean": "boolean",
    }.get(k)
    if k == "array":
        base = f"Array<{tstype(s.get('items',{}))}>"
    base = base or "Record<string, unknown>"
    return f"{base} | null" if n else base


def jtype(s: dict[str, Any]) -> str:
    if r := ref(s):
        return r
    k, _ = kind(s)
    if k == "array":
        return f"List<{jtype(s.get('items',{}))}>"
    return {
        "string": "String",
        "integer": "Integer",
        "number": "Double",
        "boolean": "Boolean",
    }.get(k, "JsonNode")


def cstype(s: dict[str, Any]) -> str:
    if r := ref(s):
        return r
    k, _ = kind(s)
    if k == "array":
        return f"IReadOnlyList<{cstype(s.get('items',{}))}>"
    return {
        "string": "string",
        "integer": "int",
        "number": "double",
        "boolean": "bool",
    }.get(k, "JsonElement")


def pascal(v: str) -> str:
    return "".join(x[:1].upper() + x[1:] for x in v.split("_"))


def generate(schemas: dict[str, Any]) -> dict[str, str]:
    objects = [(n, resolve(s, schemas)) for n, s in schemas.items()]
    py = [f'"""{HEADER}"""', "", "from typing import Any, Optional, TypedDict", "", ""]
    ts = [f"// {HEADER}", ""]
    java = [
        f"// {HEADER}",
        "package io.identitycore.models;",
        "",
        "import com.fasterxml.jackson.annotation.JsonProperty;",
        "import com.fasterxml.jackson.databind.JsonNode;",
        "import java.util.List;",
        "",
        "public final class GeneratedModels {",
        "",
        "    private GeneratedModels() {",
        "    }",
        "",
    ]
    cs = [
        f"// {HEADER}",
        "using System.Text.Json;",
        "using System.Text.Json.Serialization;",
        "",
        "namespace IdentityCore.Models;",
        "",
    ]
    for name, schema in objects:
        props = schema.get("properties", {})
        required = set(schema.get("required", []))
        required_props = [(k, v) for k, v in props.items() if k in required]
        optional_props = [(k, v) for k, v in props.items() if k not in required]
        py += (
            [f"class _{name}Required(TypedDict):"]
            + ([f"    {k}: {pytype(v)}" for k, v in required_props] or ["    pass"])
            + ["", ""]
        )
        optional_header = f"class {name}(_{name}Required, total=False):"
        if len(optional_header) > 88:
            optional_header = f"class {name}(\n    _{name}Required, total=False\n):"
        py += (
            [optional_header]
            + ([f"    {k}: {pytype(v)}" for k, v in optional_props] or ["    pass"])
            + ["", ""]
        )
        ts += (
            [f"export interface {name} {{"]
            + [
                f"  {k}{'' if k in required else '?'}: {tstype(v)};"
                for k, v in props.items()
            ]
            + ["}", ""]
        )
        fields = ", ".join(
            f'@JsonProperty("{k}") {jtype(v)} {k}' for k, v in props.items()
        )
        java += [f"    public record {name}({fields}) {{", "", "    }", ""]
        cs += [f"public sealed record {name}", "{"]
        for k, v in props.items():
            optional = k not in required or kind(v)[1]
            cs += [
                f'    [JsonPropertyName("{k}")]',
                f"    public {cstype(v)}{'?' if optional else ''} {pascal(k)} {{ get; init; }}",
            ]
        cs += ["}", ""]
    java += ["}", ""]
    return {
        "python": "\n".join(py).rstrip() + "\n",
        "typescript": "\n".join(ts),
        "java": "\n".join(java),
        "dotnet": "\n".join(cs),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    schemas = yaml.safe_load(SPEC.read_text())["components"]["schemas"]
    generated = generate(schemas)
    stale = False
    for language, path in OUTPUTS.items():
        content = generated[language]
        if args.check:
            actual = path.read_text() if path.exists() else ""
            if actual != content:
                stale = True
                print(
                    "".join(
                        difflib.unified_diff(
                            actual.splitlines(True),
                            content.splitlines(True),
                            fromfile=str(path),
                            tofile=f"generated:{path}",
                        )
                    )
                )
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
    import json

    for schema_name, path in FIXTURES.items():
        payload = json.loads(path.read_text())
        schema = resolve(schemas[schema_name], schemas)
        missing = set(schema.get("required", [])) - payload.keys()
        unknown = payload.keys() - schema.get("properties", {}).keys()
        if missing or unknown:
            stale = True
            print(f"{path}: missing={sorted(missing)}, unknown={sorted(unknown)}")
    return int(stale)


if __name__ == "__main__":
    raise SystemExit(main())
