"""Immutable routing references; destinations come from deployment approval."""

import re
from django.conf import settings
from django.db import transaction
from apps.audit.services import lock_audit_chain, record_audit_event
from apps.tenants.models import Tenant, TenantStorageRoute
from common.fields import environment_for_instance

ERROR = "Tenant storage reference is unavailable."
PATTERN = re.compile(
    r"^tenants/(ten_[0-9A-HJKMNP-TV-Z]{26})/environments/(sandbox|production)/routes/(tsr_[0-9A-HJKMNP-TV-Z]{26})/(.+)$"
)


def approved_destinations():
    value = getattr(settings, "TENANT_STORAGE_DESTINATIONS", {})
    if not isinstance(value, dict):
        raise ValueError(ERROR)
    return value


def validate_destination(bucket, region):
    if not isinstance(bucket, str) or not re.fullmatch(
        r"[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]", bucket
    ):
        raise ValueError(ERROR)
    effective = remapped_bucket(bucket)
    if approved_destinations().get(effective) != region or not region:
        raise ValueError(ERROR)
    return effective


def remapped_bucket(bucket):
    mapping = getattr(settings, "TENANT_STORAGE_BUCKET_REMAP", {})
    if not isinstance(mapping, dict):
        raise ValueError(ERROR)
    value = mapping.get(bucket, bucket)
    if not isinstance(value, str):
        raise ValueError(ERROR)
    return value


@transaction.atomic
def configure_route(tenant, environment, bucket, region):
    if (
        environment not in {"sandbox", "production"}
        or tenant.deleted_at
        or tenant.status != "active"
    ):
        raise ValueError(ERROR)
    if remapped_bucket(bucket) != bucket:
        raise ValueError(ERROR)
    validate_destination(bucket, region)
    lock_audit_chain(tenant.pk)
    tenant = Tenant.objects.get(pk=tenant.pk)
    if tenant.deleted_at or tenant.status != "active":
        raise ValueError(ERROR)
    TenantStorageRoute.objects.filter(
        tenant=tenant, environment=environment, active=True
    ).update(active=False)
    route = TenantStorageRoute.objects.create(
        tenant=tenant, environment=environment, bucket=bucket, residency_region=region
    )
    record_audit_event(
        tenant=tenant,
        action="storage.route_configured",
        target_type="tenant_storage_route",
        target_id=route.public_id,
        metadata={
            "environment": environment,
            "bucket": bucket,
            "residency_region": region,
        },
    )
    return route


def route_key(verification, legacy_key):
    route = TenantStorageRoute.objects.filter(
        tenant_id=verification.tenant_id,
        environment=environment_for_instance(verification),
        active=True,
        deleted_at__isnull=True,
    ).first()
    if route is None:
        if TenantStorageRoute.objects.filter(
            tenant_id=verification.tenant_id,
            environment=environment_for_instance(verification),
        ).exists():
            raise ValueError(ERROR)
        return legacy_key
    validate_destination(route.bucket, route.residency_region)
    if "/verifications/" in legacy_key:
        legacy_key = "verifications/" + legacy_key.split("/verifications/", 1)[1]
    return f"tenants/{verification.tenant.public_id}/environments/{route.environment}/routes/{route.public_id}/{legacy_key}"


def resolve_reference(key, fallback_bucket, *, tenant_scope=None, environment=None):
    if not isinstance(key, str):
        raise ValueError(ERROR)
    if not key.startswith("tenants/"):
        return {
            "bucket": fallback_bucket,
            "key": key,
            "residency_region": "",
            "route_id": None,
            "tenant_scope": None,
            "environment": None,
        }
    match = PATTERN.fullmatch(key)
    if match is None or any(part in {"", ".", ".."} for part in match[4].split("/")):
        raise ValueError(ERROR)
    if (tenant_scope is not None and tenant_scope != match[1]) or (
        environment is not None and environment != match[2]
    ):
        raise ValueError(ERROR)
    try:
        route = TenantStorageRoute.objects.select_related("tenant").get(
            public_id=match[3],
            tenant__public_id=match[1],
            environment=match[2],
            deleted_at__isnull=True,
        )
        validate_destination(route.bucket, route.residency_region)
    except Exception:
        raise ValueError(ERROR) from None
    return {
        "bucket": remapped_bucket(route.bucket),
        "key": key,
        "residency_region": route.residency_region,
        "route_id": route.public_id,
        "tenant_scope": match[1],
        "environment": match[2],
    }


class RoutedS3Client:
    """Apply routing to every application S3 operation, including direct callers."""

    def __init__(self, client):
        self.client = client

    def __getattr__(self, name):
        method = getattr(self.client, name)
        if name == "generate_presigned_url":

            def signed(operation, **kwargs):
                kwargs["Params"] = self.parameters(kwargs["Params"])
                return method(operation, **kwargs)

            return signed

        def routed(*args, **kwargs):
            return method(*args, **self.parameters(kwargs))

        return routed

    def parameters(self, params):
        params = dict(params)
        if "Bucket" in params and "Key" in params:
            ref = resolve_reference(params["Key"], params["Bucket"])
            params["Bucket"] = ref["bucket"]
            if ref["route_id"] and "Body" in params:
                params["Metadata"] = {
                    **params.get("Metadata", {}),
                    "tenant-route": ref["route_id"],
                    "residency-region": ref["residency_region"],
                }
        source = params.get("CopySource")
        if isinstance(source, dict):
            ref = resolve_reference(source["Key"], source["Bucket"])
            if "Key" in params:
                destination = resolve_reference(params["Key"], params["Bucket"])
                if (ref["tenant_scope"], ref["environment"]) != (
                    destination["tenant_scope"],
                    destination["environment"],
                ):
                    raise ValueError(ERROR)
            params["CopySource"] = {**source, "Bucket": ref["bucket"]}
        return params


def transfer_references(inputs):
    """Attach routing proof to known references without loading object contents."""
    result = dict(inputs)
    routing = {}
    for kind in ("document", "selfie"):
        key = inputs.get(kind + "_storage_key")
        if not key or not key.startswith("tenants/"):
            continue
        ref = resolve_reference(key, inputs.get(kind + "_storage_bucket", ""))
        result[kind + "_storage_bucket"] = ref["bucket"]
        routing[kind] = {name: ref[name] for name in ("route_id", "residency_region")}
    if routing:
        result["storage_routing"] = routing
    return result
