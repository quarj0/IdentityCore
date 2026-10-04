"""Public, bounded capability declarations; credentials never belong in manifests."""

import json
import re

from django.core.exceptions import ValidationError

REQUIRED = {
    "manifest_version",
    "contract_version",
    "capabilities",
    "environments",
    "residency",
    "retention_days",
    "processor",
    "transfer_notes",
}
CAPABILITY_FIELDS = {"countries", "document_types", "input_schema", "output_schema"}
NOTIFICATION_CAPABILITIES = {
    "notification_email",
    "notification_sms",
    "notification_in_app",
}


def validate_manifest(manifest, *, provider_type):
    from apps.providers.models import CHECK_TYPE_PROVIDER_TYPES, ProviderType

    def invalid():
        raise ValidationError(
            {"manifest_json": "Invalid or incompatible provider manifest."}
        )

    if not isinstance(manifest, dict) or set(manifest) != REQUIRED:
        invalid()
    if manifest["manifest_version"] != "1" or manifest["contract_version"] != "1":
        invalid()
    if len(json.dumps(manifest)) > 16384:
        invalid()
    for name in ("processor", "transfer_notes"):
        if not isinstance(manifest[name], str) or not 1 <= len(manifest[name]) <= 1000:
            invalid()
    days = manifest["retention_days"]
    if type(days) is not int or not 0 <= days <= 36500:
        invalid()
    for name in ("residency", "environments"):
        values = manifest[name]
        if (
            not isinstance(values, list)
            or not values
            or len(values) > 32
            or any(
                not isinstance(v, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", v)
                for v in values
            )
            or len(set(values)) != len(values)
        ):
            invalid()
    if not set(manifest["environments"]) <= {"sandbox", "production"}:
        invalid()
    capabilities = manifest["capabilities"]
    if not isinstance(capabilities, dict) or not capabilities or len(capabilities) > 20:
        invalid()
    for key, coverage in capabilities.items():
        allowed = CHECK_TYPE_PROVIDER_TYPES.get(
            key,
            {ProviderType.NOTIFICATION} if key in NOTIFICATION_CAPABILITIES else set(),
        )
        if (
            provider_type not in allowed
            or not isinstance(coverage, dict)
            or set(coverage) != CAPABILITY_FIELDS
        ):
            invalid()
        for field in ("countries", "document_types"):
            values = coverage[field]
            if (
                not isinstance(values, list)
                or len(values) > 256
                or any(
                    not isinstance(v, str)
                    or not re.fullmatch(r"[A-Za-z0-9_-]{1,120}|\*", v)
                    for v in values
                )
                or len(set(values)) != len(values)
            ):
                invalid()
        if any(
            len(v) != 2 or not v.isupper() for v in coverage["countries"] if v != "*"
        ):
            invalid()
        for field in ("input_schema", "output_schema"):
            expected = f"{key}.{'input' if field == 'input_schema' else 'output'}/v1"
            if coverage[field] != expected:
                invalid()


def validate_compatibility(
    provider, capability, *, environment=None, countries=(), document_types=()
):
    """Legacy declarations remain usable; declared coverage always fails closed."""
    manifest = provider.manifest_json
    if not manifest:
        return
    validate_manifest(manifest, provider_type=provider.provider_type)
    if environment is None and not {"sandbox", "production"} <= set(
        manifest["environments"]
    ):
        raise ValidationError(
            "Global assignments require sandbox and production support."
        )
    coverage = manifest["capabilities"].get(capability)
    if coverage is None or (
        environment and environment not in manifest["environments"]
    ):
        raise ValidationError(
            "Provider manifest does not support this capability/environment."
        )
    for requested, field in (
        (countries, "countries"),
        (document_types, "document_types"),
    ):
        offered = coverage[field]
        # Empty route restrictions mean all countries/types, requiring wildcard coverage.
        if "*" not in offered and (not requested or not set(requested) <= set(offered)):
            raise ValidationError(
                "Provider manifest coverage is incompatible with route conditions."
            )
