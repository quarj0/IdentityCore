#!/usr/bin/env python3
"""Reject undocumented persisted fields and stale processing/owner references."""

from __future__ import annotations
import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "docs/privacy/processing-inventory.json"
REQUIRED = {
    "id",
    "fields",
    "purpose",
    "locations",
    "retention",
    "processors",
    "transfers",
    "owners",
}


def model_fields(root):
    result = set()
    sources = []
    for source in sorted((root / "backend/django/apps").rglob("*.py")):
        relative = source.relative_to(root).as_posix()
        if (
            "migrations" in source.parts
            or "tests" in source.parts
            or source.name == "tests.py"
            or source.name.startswith("test_")
        ):
            continue
        tree = ast.parse(source.read_text())
        sources.append((relative, tree))
    known_models = {"AbstractBaseUser", "PermissionsMixin"}
    while True:
        before = set(known_models)
        for _, tree in sources:
            for model in (node for node in tree.body if isinstance(node, ast.ClassDef)):
                if any(
                    (isinstance(base, ast.Name) and base.id in known_models)
                    or (
                        isinstance(base, ast.Attribute)
                        and base.attr == "Model"
                        and isinstance(base.value, ast.Name)
                        and base.value.id == "models"
                    )
                    for base in model.bases
                ):
                    known_models.add(model.name)
        if known_models == before:
            break
    for relative, tree in sources:
        for model in (
            node
            for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name in known_models
        ):
            for node in model.body:
                value = getattr(node, "value", None)
                if not isinstance(value, ast.Call):
                    continue
                name = (
                    value.func.attr
                    if isinstance(value.func, ast.Attribute)
                    else value.func.id if isinstance(value.func, ast.Name) else ""
                )
                if not (
                    name.endswith("Field")
                    or name in {"ForeignKey", "OneToOneField", "ManyToManyField"}
                ):
                    continue
                targets = (
                    node.targets
                    if isinstance(node, ast.Assign)
                    else [node.target] if isinstance(node, ast.AnnAssign) else []
                )
                for target in targets:
                    if isinstance(target, ast.Name):
                        result.add((relative, model.name + "." + target.id))
            # Framework-inherited authentication state is persisted too.
            base_names = {base.id for base in model.bases if isinstance(base, ast.Name)}
            inherited = []
            if "AbstractBaseUser" in base_names:
                inherited += ["password", "last_login"]
            if "PermissionsMixin" in base_names:
                inherited += ["is_superuser", "groups", "user_permissions"]
            result.update((relative, model.name + "." + field) for field in inherited)
    return result


def existing_path(root, value):
    if not isinstance(value, str):
        return False
    path = (root / value).resolve()
    return path.is_relative_to(root.resolve()) and path.exists()


def validate(data, root):
    errors = []
    if data.get("schema_version") != 2:
        return ["schema_version must be 2"]
    owners = data.get("owners", {})
    register_path = data.get("owner_register")
    if not existing_path(root, register_path):
        return ["owner register path does not exist"]
    register = json.loads((root / register_path).read_text())
    if set(register) != set(owners):
        errors.append("owner register must cover exactly the declared owners")
    for key, owner in register.items():
        if (
            not isinstance(owner, dict)
            or not owner.get("role")
            or not owner.get("responsibility")
            or not owner.get("paths")
        ):
            errors.append(f"{key}: owner metadata is incomplete")
            continue
        if owner["role"] != owners.get(key):
            errors.append(f"{key}: owner role does not match the declared register")
        for path in owner["paths"]:
            if not existing_path(root, path):
                errors.append(f"{key}: owner reference does not exist: {path}")
    activities = {}
    for activity in data.get("activities", []):
        key = activity.get("id", "<missing>")
        if key in activities:
            errors.append(f"{key}: duplicate activity")
        activities[key] = activity
        for field in REQUIRED:
            if not activity.get(field):
                errors.append(f"{key}: missing {field}")
        for owner in activity.get("owners", []):
            if owner not in owners:
                errors.append(f"{key}: unknown owner {owner}")
        for path in activity.get("locations", []):
            if not existing_path(root, path):
                errors.append(f"{key}: source path does not exist: {path}")
    if not activities:
        errors.append("no processing activities")
    documented = set()
    for entry in data.get("field_catalog", []):
        if not isinstance(entry, dict) or set(entry) != {"source", "field", "activity"}:
            errors.append("invalid field catalog entry")
            continue
        reference = (entry["source"], entry["field"])
        if reference in documented:
            errors.append(f"duplicate field: {reference}")
        documented.add(reference)
        activity = activities.get(entry["activity"])
        if activity is None:
            errors.append(f"unknown field processing activity: {reference}")
        elif entry["source"] not in activity.get("locations", []):
            errors.append(f"field source must be linked in its activity: {reference}")
    actual = model_fields(root)
    for source, field in sorted(actual - documented):
        errors.append(f"undocumented persisted field: {source}:{field}")
    for source, field in sorted(documented - actual):
        errors.append(f"stale field reference: {source}:{field}")
    return errors


def main():
    data = json.loads(INVENTORY.read_text())
    errors = validate(data, ROOT)
    if errors:
        raise SystemExit("processing inventory invalid:\n- " + "\n- ".join(errors))
    print(
        f"processing inventory valid: {len(data['activities'])} activities, {len(data['field_catalog'])} persisted fields, {len(data['owners'])} linked owners"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
