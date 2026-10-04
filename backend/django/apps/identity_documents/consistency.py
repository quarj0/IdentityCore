"""Versioned document signals, with decisions delegated to policy actions."""

from datetime import date, timedelta
import unicodedata

from django.utils import timezone
from django_countries import countries
from django_countries.fields import Country

VERSION = "document-consistency-v1"
ISSUES = frozenset(
    {
        "document_expired",
        "document_issue_date_future",
        "document_birth_date_future",
        "document_date_order_invalid",
        "document_validity_too_long",
        "document_age_below_minimum",
        "document_birth_date_ambiguous",
        "document_birth_date_unavailable",
        "document_date_invalid",
        "document_birth_date_mismatch",
        "document_name_mismatch",
        "document_number_mismatch",
        "mrz_country_mismatch",
        "mrz_checksum_invalid",
        "document_rules_invalid",
    }
)


def validate_rules(value):
    if value == {}:
        return value
    if (
        not isinstance(value, dict)
        or set(value) != {"version", "countries"}
        or type(value.get("version")) is not int
        or value["version"] != 1
    ):
        raise ValueError("Use version 1 and country rules.")
    configured = value["countries"]
    if not isinstance(configured, dict) or len(configured) > 250:
        raise ValueError("Country rules must be a bounded object.")
    for code, rules in configured.items():
        if code != "*" and code not in dict(countries):
            raise ValueError("Choose an ISO country code or the default *.")
        if not isinstance(rules, dict) or set(rules) - {
            "minimum_age",
            "maximum_document_years",
            "expiry_grace_days",
            "actions",
        }:
            raise ValueError("Unknown document rule.")
        for key, low, high in [
            ("minimum_age", 0, 120),
            ("maximum_document_years", 1, 50),
            ("expiry_grace_days", 0, 365),
        ]:
            if key in rules and (
                type(rules[key]) is not int or not low <= rules[key] <= high
            ):
                raise ValueError("Document rule is outside its supported range.")
        actions = rules.get("actions", {})
        if (
            not isinstance(actions, dict)
            or set(actions) - ISSUES
            or any(
                not isinstance(action, str)
                or action not in {"ignore", "manual_review", "reject"}
                for action in actions.values()
            )
        ):
            raise ValueError("Choose supported signal actions.")
    return value


def _iso(value):
    if isinstance(value, date):
        return value
    if not isinstance(value, str) or len(value) != 10:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _mrz_date(value, today, *, birth=False, claimed=None):
    if (
        not isinstance(value, str)
        or len(value) != 6
        or not value.isascii()
        or not value.isdigit()
    ):
        return None, False
    if claimed and claimed.strftime("%y%m%d") == value:
        return claimed, False
    candidates = []
    for century in (today.year // 100 - 1, today.year // 100, today.year // 100 + 1):
        try:
            candidate = date(
                century * 100 + int(value[:2]), int(value[2:4]), int(value[4:])
            )
        except ValueError:
            continue
        age = (
            today.year
            - candidate.year
            - ((today.month, today.day) < (candidate.month, candidate.day))
        )
        if (birth and 0 <= age <= 120) or (
            not birth and abs(candidate.year - today.year) <= 50
        ):
            candidates.append(candidate)
    return (candidates[0] if len(candidates) == 1 else None), len(candidates) > 1


def _name(value):
    if not isinstance(value, str):
        return ""
    value = unicodedata.normalize("NFKD", value)
    return " ".join(
        "".join(
            char if char.isalnum() else " "
            for char in value
            if not unicodedata.combining(char)
        )
        .casefold()
        .split()
    )


def collect_consistency(document, verification, *, today=None):
    today = (
        today or timezone.now().date()
    )  # A fixed UTC date, independent of worker locale.
    snapshot = verification.policy_snapshot_json or {}
    configuration = snapshot.get("document_consistency_rules", {})
    try:
        validate_rules(configuration)
    except (ValueError, TypeError):
        return {
            "version": VERSION,
            "policy_version": snapshot.get("version"),
            "country": document.country_profile_id,
            "issues": ["document_rules_invalid"],
            "recommended_action": "manual_review",
        }
    code = document.country_profile_id
    rules = configuration.get("countries", {}).get(
        code, configuration.get("countries", {}).get("*", {})
    )
    extracted = document.extracted_data_json or {}
    if not isinstance(extracted, dict):
        extracted = {}
    mrz = extracted.get("mrz_evidence") or {}
    valid_mrz = isinstance(mrz, dict) and mrz.get("status") == "valid"
    fields = mrz.get("fields", {}) if valid_mrz else {}
    if not isinstance(fields, dict):
        fields = {}
    issues = set()

    def value(name):
        field = fields.get(name, {})
        result = field.get("value") if isinstance(field, dict) else None
        return result if isinstance(result, str) and len(result) <= 128 else None

    claimed_birth = verification.verification_subject.date_of_birth
    visual = extracted.get("visual_ocr_fields") or extracted
    if not isinstance(visual, dict):
        visual = extracted
    visible_birth = _iso(visual.get("date_of_birth"))
    birth, ambiguous = _mrz_date(
        value("date_of_birth_mrz"), today, birth=True, claimed=claimed_birth
    )
    if ambiguous:
        issues.add("document_birth_date_ambiguous")
    if birth is None and not ambiguous:
        birth = visible_birth
    expiry, expiry_ambiguous = _mrz_date(value("expiry_date_mrz"), today)
    expiry = document.expires_at or expiry or _iso(extracted.get("expiry_date"))
    issued = document.issued_at or _iso(extracted.get("issue_date"))
    if expiry_ambiguous:
        issues.add("document_date_invalid")
    for key in ("date_of_birth", "issue_date", "expiry_date"):
        if extracted.get(key) and _iso(extracted[key]) is None:
            issues.add("document_date_invalid")
    if valid_mrz:
        for key in ("date_of_birth_mrz", "expiry_date_mrz"):
            raw = value(key)
            if (
                raw
                and "<" not in raw
                and _mrz_date(
                    raw,
                    today,
                    birth=key.startswith("date_of_birth"),
                    claimed=claimed_birth if key.startswith("date_of_birth") else None,
                )
                == (None, False)
            ):
                issues.add("document_date_invalid")
        if (
            code in dict(countries)
            and value("issuing_country")
            and value("issuing_country")
            != ("D" if code == "DE" else Country(code).alpha3)
        ):
            issues.add("mrz_country_mismatch")
        if (
            claimed_birth
            and birth
            and claimed_birth != birth
            or visible_birth
            and birth
            and visible_birth != birth
        ):
            issues.add("document_birth_date_mismatch")
        visible_name = _name(visual.get("full_name"))
        mrz_name = _name(value("name"))
        claimed_name = _name(verification.verification_subject.full_name)
        if mrz_name and any(
            name and sorted(name.split()) != sorted(mrz_name.split())
            for name in (visible_name, claimed_name)
        ):
            issues.add("document_name_mismatch")
        if (
            visual.get("document_number")
            and value("document_number")
            and str(visual["document_number"]).strip().upper()
            != value("document_number")
        ):
            issues.add("document_number_mismatch")
    elif isinstance(mrz, dict) and "mrz_checksum_invalid" in (mrz.get("issues") or []):
        issues.add("mrz_checksum_invalid")
    if any(value and value > today for value in (birth, visible_birth, claimed_birth)):
        issues.add("document_birth_date_future")
    if issued and issued > today:
        issues.add("document_issue_date_future")
    if expiry and expiry < today - timedelta(days=rules.get("expiry_grace_days", 0)):
        issues.add("document_expired")
    if issued and expiry and expiry < issued or issued and birth and issued < birth:
        issues.add("document_date_order_invalid")
    if issued and expiry and "maximum_document_years" in rules:
        years = expiry.year - issued.year
        if (
            years > rules["maximum_document_years"]
            or years == rules["maximum_document_years"]
            and (expiry.month, expiry.day) > (issued.month, issued.day)
        ):
            issues.add("document_validity_too_long")
    age = (
        today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
        if birth and birth <= today
        else None
    )
    if age is None and "minimum_age" in rules:
        issues.add("document_birth_date_unavailable")
    if age is not None and age < rules.get("minimum_age", 0):
        issues.add("document_age_below_minimum")
    actions = {rules.get("actions", {}).get(issue, "ignore") for issue in issues}
    action = (
        "reject"
        if "reject" in actions
        else "manual_review" if "manual_review" in actions else "ignore"
    )
    return {
        "version": VERSION,
        "policy_version": snapshot.get("version"),
        "rules_version": configuration.get("version"),
        "country": code,
        "issues": sorted(issues),
        "recommended_action": action,
        "age_years": age,
    }
