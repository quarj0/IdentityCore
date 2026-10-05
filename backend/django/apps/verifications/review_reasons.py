"""Snapshot-bound reviewer reason catalogs and plain-text note validation."""

import html
import re

from django.core.exceptions import ValidationError

OUTCOMES = frozenset({"verified", "rejected", "failed"})
CODE = re.compile(r"^[a-z][a-z0-9_]{0,79}$")


def validate_reason_rules(value):
    if value == {}:
        return value
    valid = (
        isinstance(value, dict)
        and set(value) == {"version", "outcomes", "organization_facing_codes"}
        and type(value.get("version")) is int
        and value["version"] == 1
        and isinstance(value.get("outcomes"), dict)
        and set(value["outcomes"]) == OUTCOMES
    )
    if not valid:
        raise ValidationError("Invalid version-one reviewer reason rules.")
    all_codes = set()
    for rule in value["outcomes"].values():
        if not isinstance(rule, dict) or set(rule) != {"codes", "notes_required"}:
            raise ValidationError("Each outcome requires codes and notes_required.")
        codes = rule["codes"]
        if (
            not isinstance(codes, list)
            or not 1 <= len(codes) <= 50
            or any(
                not isinstance(code, str) or not CODE.fullmatch(code) for code in codes
            )
            or len(set(codes)) != len(codes)
            or type(rule["notes_required"]) is not bool
        ):
            raise ValidationError("Invalid reviewer reason codes or note requirement.")
        all_codes.update(codes)
    approved = value["organization_facing_codes"]
    if (
        not isinstance(approved, list)
        or len(approved) > 150
        or any(not isinstance(code, str) or code not in all_codes for code in approved)
        or len(set(approved)) != len(approved)
    ):
        raise ValidationError("Organization-facing reasons must come from the catalog.")
    return value


def validate_reviewer_input(verification, outcome, code, notes):
    rules = verification.policy_snapshot_json.get("review_reason_rules", {})
    validate_reason_rules(rules)
    if outcome not in OUTCOMES or not isinstance(code, str) or not CODE.fullmatch(code):
        raise ValidationError("Choose a valid reviewer reason code.")
    if not isinstance(notes, str) or len(notes) > 4000:
        raise ValidationError("Reviewer notes must be at most 4000 characters.")
    decoded = notes
    for _ in range(8):
        previous = decoded
        decoded = html.unescape(decoded)
        if decoded == previous:
            break
    if (
        decoded != html.unescape(decoded)
        or "<" in decoded
        or ">" in decoded
        or any(ord(char) < 32 and char not in "\n\t\r" for char in decoded)
    ):
        raise ValidationError("Reviewer notes must contain plain text without markup.")
    if rules:
        rule = rules["outcomes"][outcome]
        if code not in rule["codes"]:
            raise ValidationError("This reason is not configured for the outcome.")
        if rule["notes_required"] and not notes.strip():
            raise ValidationError("Notes are required for this outcome.")


def organization_reason_codes(verification, decision):
    if decision.decision_type != "manual":
        return None
    rules = verification.policy_snapshot_json.get("review_reason_rules", {})
    try:
        validate_reason_rules(rules)
    except ValidationError:
        return []
    approved = set(rules.get("organization_facing_codes", []))
    return [code for code in decision.reason_codes_json if code in approved]
