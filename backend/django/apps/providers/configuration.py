"""Tenant/environment provider configuration, connection evidence and promotion."""

import hashlib
import hmac
import json
import secrets
from datetime import timedelta
from urllib.parse import urlsplit

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from apps.audit.services import record_audit_event
from apps.providers.adapters import ProviderContractError, normalize_provider_result
from apps.providers.http_adapter import (
    SecureHTTPProviderAdapter,
    SecureHTTPAdapterError,
)
from apps.providers.manifests import validate_manifest
from apps.tenants.models import Tenant
from apps.providers.models import (
    Provider,
    ProviderEnvironmentConfiguration,
    ProviderRoute,
    ProviderRouteStep,
)
from apps.providers.services import publish_provider_route
from common.authorization import AuthorizationAction, decide_user_access

PUBLIC_FIELDS = {"endpoint_url", "allowed_hosts", "timeout_seconds"}
TEST_FRESHNESS = timedelta(minutes=15)


def _require(user, tenant, permission="manage_providers"):
    if not decide_user_access(
        user,
        action=AuthorizationAction.TENANT_ACCESS,
        tenant=tenant,
        permission_code=permission,
    ).allowed:
        raise PermissionError("Provider configuration permission required.")


def _audit(config, user, action, **metadata):
    record_audit_event(
        actor=user,
        tenant_id=config.provider.tenant_id,
        action=action,
        target_type="provider_configuration",
        target_id=config.public_id,
        metadata={
            "environment": config.environment,
            "version": config.version,
            **metadata,
        },
    )


def validate_public_configuration(value):
    if not isinstance(value, dict) or set(value) != PUBLIC_FIELDS:
        raise ValidationError(
            "Supply endpoint_url, allowed_hosts and timeout_seconds only."
        )
    if (
        type(value["timeout_seconds"]) is not int
        or not 1 <= value["timeout_seconds"] <= 30
    ):
        raise ValidationError("Connection timeout must be 1–30 seconds.")
    hosts = value["allowed_hosts"]
    if (
        not isinstance(hosts, list)
        or not 1 <= len(hosts) <= 10
        or any(not isinstance(h, str) or len(h) > 253 for h in hosts)
    ):
        raise ValidationError("Supply bounded destination hostnames.")
    url = value["endpoint_url"]
    if not isinstance(url, str) or len(url) > 2048:
        raise ValidationError("Invalid provider endpoint.")
    parsed = urlsplit(url)
    if parsed.query or parsed.fragment:
        raise ValidationError(
            "Provider endpoints cannot contain query credentials or fragments."
        )
    SecureHTTPProviderAdapter(value)._validate_destination(url)


def _credentials(value):
    if (
        not isinstance(value, dict)
        or set(value) != {"api_key"}
        or not isinstance(value["api_key"], str)
        or not 16 <= len(value["api_key"]) <= 4096
        or any(not 33 <= ord(c) <= 126 for c in value["api_key"])
    ):
        raise ValidationError(
            "Supply a separate provider API credential of 16–4096 characters."
        )
    return value


def configuration_digest(config):
    payload = json.dumps(
        {
            "public": config.public_configuration_json,
            "credentials": config.credentials_json,
            "manifest": config.manifest_snapshot_json,
            "environment": config.environment,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return hmac.new(settings.SECRET_KEY.encode(), payload, hashlib.sha256).hexdigest()


@transaction.atomic
def create_configuration(
    *, provider, user, environment, public_configuration, credentials, source=None
):
    _require(user, provider)
    Tenant.objects.select_for_update(no_key=True).get(pk=provider.tenant_id)
    locked = Provider.objects.select_for_update(no_key=True).get(pk=provider.pk)
    if locked.deleted_at or environment not in {"sandbox", "production"}:
        raise ValidationError("Invalid provider/environment.")
    validate_manifest(locked.manifest_json, provider_type=locked.provider_type)
    if environment not in locked.manifest_json["environments"]:
        raise ValidationError("The provider does not declare this environment.")
    validate_public_configuration(public_configuration)
    _credentials(credentials)
    if environment == "production":
        if locked.tenant.organization.status != "active":
            raise ValidationError("Production requires an approved organization.")
        if (
            source is None
            or source.provider_id != locked.id
            or source.environment != "sandbox"
            or source.status != "active"
        ):
            raise ValidationError("Production requires an active sandbox source.")
        if hmac.compare_digest(
            credentials["api_key"], source.credentials_json["api_key"]
        ):
            raise ValidationError("Production must use an independent credential.")
    elif source is not None:
        raise ValidationError("Sandbox configurations cannot be promotions.")
    version = (
        locked.environment_configurations.filter(environment=environment).aggregate(
            value=Max("version")
        )["value"]
        or 0
    ) + 1
    previous = source.public_configuration_json if source else {}
    diff = {
        key: {"before": previous.get(key), "after": public_configuration[key]}
        for key in sorted(PUBLIC_FIELDS)
        if previous.get(key) != public_configuration[key]
    }
    config = ProviderEnvironmentConfiguration.objects.create(
        provider=locked,
        environment=environment,
        version=version,
        public_configuration_json=public_configuration,
        credentials_json=credentials,
        manifest_snapshot_json=locked.manifest_json,
        source=source,
        diff_json=diff,
        requested_by=user,
    )
    _audit(
        config,
        user,
        "provider.configuration_requested",
        source_id=source.public_id if source else None,
    )
    return config


def test_configuration(*, config, user):
    _require(user, config.provider)
    if config.status != "draft":
        raise ValidationError("Only draft configurations can be tested.")
    digest = configuration_digest(config)
    challenge = secrets.token_urlsafe(32)
    passed = False
    try:
        response = SecureHTTPProviderAdapter(
            config.public_configuration_json
        ).post_json(
            url=config.public_configuration_json["endpoint_url"],
            payload={
                "contract_version": "1",
                "operation": "connection_test",
                "environment": config.environment,
                "challenge": challenge,
                "capabilities": sorted(config.manifest_snapshot_json["capabilities"]),
            },
            headers={"Authorization": "Bearer " + config.credentials_json["api_key"]},
        )
        passed = (
            isinstance(response, dict)
            and response.get("contract_version") == "1"
            and response.get("challenge") == challenge
            and response.get("status") == "completed"
            and isinstance(response.get("capabilities"), list)
            and set(response["capabilities"])
            == set(config.manifest_snapshot_json["capabilities"])
        )
    except (SecureHTTPAdapterError, ValueError, TypeError):
        passed = False
    with transaction.atomic():
        Tenant.objects.select_for_update(no_key=True).get(pk=config.provider.tenant_id)
        locked = (
            ProviderEnvironmentConfiguration.objects.select_for_update(
                of=("self",), no_key=True
            )
            .select_related("provider")
            .get(pk=config.pk)
        )
        if locked.status != "draft" or configuration_digest(locked) != digest:
            raise ValidationError("Configuration changed during the connection test.")
        locked.tested_at = timezone.now()
        locked.tested_digest = digest
        locked.test_succeeded = passed
        locked.save(
            update_fields=["tested_at", "tested_digest", "test_succeeded", "updated_at"]
        )
        _audit(locked, user, "provider.connection_tested", succeeded=passed)
    return locked


@transaction.atomic
def activate_configuration(*, config, user):
    _require(
        user,
        config.provider,
        (
            "approve_provider_promotion"
            if config.environment == "production"
            else "manage_providers"
        ),
    )
    Tenant.objects.select_for_update(no_key=True).get(pk=config.provider.tenant_id)
    Provider.objects.select_for_update(no_key=True).get(pk=config.provider_id)
    locked = (
        ProviderEnvironmentConfiguration.objects.select_for_update(
            of=("self",), no_key=True
        )
        .select_related("provider")
        .get(pk=config.pk)
    )
    if locked.environment == "production" and locked.requested_by_id == user.pk:
        raise ValidationError(
            "A different privileged user must approve production promotion."
        )
    if (
        locked.status != "draft"
        or not locked.test_succeeded
        or locked.tested_digest != configuration_digest(locked)
        or not locked.tested_at
        or locked.tested_at < timezone.now() - TEST_FRESHNESS
    ):
        raise ValidationError(
            "Activation requires a successful connection test within 15 minutes."
        )
    if locked.manifest_snapshot_json != locked.provider.manifest_json:
        raise ValidationError(
            "Provider declarations changed; create and test a new configuration."
        )
    if (
        locked.environment == "production"
        and locked.provider.tenant.organization.status != "active"
    ):
        raise ValidationError("Production requires an approved organization.")
    if locked.environment == "production":
        source = (
            ProviderEnvironmentConfiguration.objects.select_for_update(no_key=True)
            .filter(
                pk=locked.source_id,
                provider_id=locked.provider_id,
                environment="sandbox",
                status="active",
            )
            .first()
        )
        if source is None:
            raise ValidationError(
                "Production promotion requires its active sandbox source."
            )
    locked.provider.environment_configurations.filter(
        environment=locked.environment, status="active"
    ).update(status="retired", updated_at=timezone.now())
    locked.status = "active"
    locked.approved_by = user
    locked.save(update_fields=["status", "approved_by", "updated_at"])
    _audit(locked, user, "provider.configuration_activated")
    return locked


@transaction.atomic
def assign_configuration(*, config, user, capability, countries=(), document_types=()):
    _require(user, config.provider)
    if capability not in {
        "document_quality",
        "document_classification",
        "document_ocr",
        "face_match",
        "liveness",
    }:
        raise ValidationError("This capability has no supported verification runtime.")
    Tenant.objects.select_for_update(no_key=True).get(pk=config.provider.tenant_id)
    Provider.objects.select_for_update(no_key=True).get(pk=config.provider_id)
    config.refresh_from_db()
    if config.status != "active":
        raise ValidationError("Assignments require an activated configuration.")
    key = "configured-" + capability
    version = (
        ProviderRoute.objects.filter(
            tenant_id=config.provider.tenant_id,
            route_key=key,
            environment=config.environment,
        ).aggregate(value=Max("version"))["value"]
        or 0
    ) + 1
    route = ProviderRoute.objects.create(
        tenant_id=config.provider.tenant_id,
        route_key=key,
        name="Configured " + capability,
        environment=config.environment,
        version=version,
        capability=capability,
        country_codes_json=list(countries),
        document_type_ids_json=list(document_types),
        timeout_seconds=config.public_configuration_json["timeout_seconds"],
    )
    ProviderRouteStep.objects.create(route=route, provider=config.provider, position=1)
    route = publish_provider_route(route)
    _audit(
        config,
        user,
        "provider.configuration_assigned",
        capability=capability,
        route_id=route.public_id,
    )
    return route


def serialize_configuration(config):
    return {
        "id": config.public_id,
        "provider_id": config.provider.public_id,
        "environment": config.environment,
        "version": config.version,
        "status": config.status,
        "configuration": config.public_configuration_json,
        "diff": config.diff_json,
        "source_id": config.source.public_id if config.source else None,
        "credentials_configured": bool(config.credentials_json),
        "tested_at": config.tested_at.isoformat() if config.tested_at else None,
        "test_succeeded": config.test_succeeded,
        "requested_by": config.requested_by.public_id,
        "approved_by": config.approved_by.public_id if config.approved_by else None,
    }


def invoke_configured_provider(
    *, provider, environment, capability, inputs, timeout_seconds
):
    config = provider.environment_configurations.filter(
        environment=environment, status="active"
    ).first()
    if (
        config is None
        or config.manifest_snapshot_json != provider.manifest_json
        or capability not in config.manifest_snapshot_json["capabilities"]
    ):
        raise SecureHTTPAdapterError(
            "No approved provider configuration is available.",
            error_code="provider_configuration_unavailable",
        )
    public = {
        **config.public_configuration_json,
        "timeout_seconds": min(
            timeout_seconds, config.public_configuration_json["timeout_seconds"]
        ),
    }
    result = SecureHTTPProviderAdapter(public).post_json(
        url=public["endpoint_url"],
        payload={
            "contract_version": "1",
            "capability": capability,
            "environment": environment,
            "inputs": inputs,
        },
        headers={"Authorization": "Bearer " + config.credentials_json["api_key"]},
    )
    if (
        not isinstance(result, dict)
        or result.get("capability") != capability
        or result.get("contract_version") != "1"
    ):
        raise ProviderContractError(
            "Provider result does not match the requested capability."
        )
    return normalize_provider_result(capability, result)
