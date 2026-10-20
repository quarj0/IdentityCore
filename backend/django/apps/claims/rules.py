"""Small, versioned deterministic rules; no uploaded expressions or remote code."""

from datetime import date, datetime, time, timedelta, timezone
import re

from rest_framework.exceptions import ValidationError

from apps.evidence.validation import canonical_json

RULE_VERSION = 1


def _field(source, parameters, key="field"):
    field = parameters.get(key)
    if not isinstance(field, str) or field not in source:
        raise ValidationError("The rule input field is unavailable.")
    return source[field]


def _date(value):
    if not isinstance(value, str) or not re.fullmatch(
        r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value
    ):
        raise ValidationError("The rule requires an ISO calendar date.")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValidationError("The rule requires a valid calendar date.") from exc


def apply_rule(name, version, sources, parameters, *, now):
    if version != RULE_VERSION or not isinstance(parameters, dict):
        raise ValidationError("The rule version or parameters are unsupported.")
    canonical_json(parameters, maximum=8192)
    if not sources or any(not isinstance(source, dict) for source in sources):
        raise ValidationError("The rule requires source object values.")
    supported = {
        "copy": set(),
        "field": {"field", "output_field"},
        "normalize_name": {"field", "output_field"},
        "iso_date": {"field", "output_field"},
        "age_over": {"field", "output_field", "threshold"},
        "document_current": {"field", "output_field"},
        "exact_corroboration": set(),
    }
    if name not in supported or set(parameters) - supported[name]:
        raise ValidationError("The rule name or parameter names are unsupported.")
    if name == "exact_corroboration":
        if len(sources) < 2:
            raise ValidationError(
                "Corroboration requires at least two independent sources."
            )
        encoded = [canonical_json(source) for source in sources]
        if any(value != encoded[0] for value in encoded[1:]):
            raise ValidationError(
                "Conflicting sources cannot be silently corroborated."
            )
        return dict(sources[0]), "corroborated", None
    if len(sources) != 1:
        raise ValidationError("This rule requires exactly one source.")
    if name == "copy":
        return dict(sources[0]), "normalized", None
    output = parameters.get("output_field", "value")
    if not isinstance(output, str) or not re.fullmatch(
        r"[A-Za-z][A-Za-z0-9_]{0,119}", output
    ):
        raise ValidationError("Choose a bounded output field name.")
    value = _field(sources[0], parameters)
    deadline = None
    if name == "normalize_name":
        if not isinstance(value, str) or not value.strip():
            raise ValidationError("Name normalization requires nonempty text.")
        value = " ".join(value.split())
    elif name == "iso_date":
        value = _date(value).isoformat()
    elif name == "age_over":
        born = _date(value)
        today = now.astimezone(timezone.utc).date()
        threshold = parameters.get("threshold")
        if type(threshold) is not int or not 0 <= threshold <= 120 or born > today:
            raise ValidationError("Choose a valid age threshold and birth date.")
        age = (
            today.year - born.year - ((today.month, today.day) < (born.month, born.day))
        )
        value = age >= threshold
        # A currently false age predicate can change at the next UTC date.
        deadline = datetime.combine(
            today + timedelta(days=1), time.min, tzinfo=timezone.utc
        )
    elif name == "document_current":
        expiry = _date(value)
        today = now.astimezone(timezone.utc).date()
        value = expiry >= today
        deadline = datetime.combine(
            today + timedelta(days=1), time.min, tzinfo=timezone.utc
        )
    claim_class = (
        "derived" if name in {"age_over", "document_current"} else "normalized"
    )
    return {output: value}, claim_class, deadline
