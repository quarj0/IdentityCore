import math
from collections import Counter, defaultdict
from datetime import timedelta

from django.db.models import Prefetch, Q
from django.utils import timezone

from apps.providers.models import (
    ProviderCheck,
    ProviderCheckStatus,
    ProviderCircuitState,
    ProviderCircuitStatus,
    ProviderRoute,
    ProviderRouteStep,
    ProviderRouteStatus,
    ProviderStatus,
)


TERMINAL_HEALTH_STATUSES = {
    ProviderCheckStatus.COMPLETED,
    ProviderCheckStatus.FAILED,
    ProviderCheckStatus.TIMEOUT,
}
SAFE_ERROR_CODES = frozenset(
    {
        "provider_circuit_open",
        "provider_contract_version_unsupported",
        "provider_invalid_content_type",
        "provider_invalid_json",
        "provider_invalid_response",
        "provider_network_error",
        "provider_redirect_blocked",
        "provider_response_too_large",
        "provider_route_exhausted",
        "provider_timeout",
    }
)


def _percentile(values: list[int], percentile: float) -> int | None:
    if not values:
        return None
    ordered = sorted(values)
    rank = max(1, math.ceil(percentile * len(ordered)))
    return ordered[rank - 1]


def _metric_status(*, total: int, availability: float, error_rate: float) -> str:
    if total == 0:
        return "no_data"
    if availability == 0:
        return "unavailable"
    if error_rate >= 5:
        return "degraded"
    return "healthy"


def _safe_error_code(value: str) -> str:
    if value in SAFE_ERROR_CODES:
        return value
    if (
        value.startswith("provider_http_")
        and value.removeprefix("provider_http_").isdigit()
    ):
        return value
    return "provider_error"


def _provider_metric(provider, checks: list[ProviderCheck]) -> dict:
    terminal = [check for check in checks if check.status in TERMINAL_HEALTH_STATUSES]
    completed = sum(check.status == ProviderCheckStatus.COMPLETED for check in terminal)
    failed = len(terminal) - completed
    availability = round((completed / len(terminal)) * 100, 2) if terminal else 0.0
    error_rate = round((failed / len(terminal)) * 100, 2) if terminal else 0.0
    durations = [
        check.duration_ms for check in terminal if check.duration_ms is not None
    ]
    error_codes = Counter(
        _safe_error_code(check.error_code)
        for check in terminal
        if check.status != ProviderCheckStatus.COMPLETED and check.error_code
    )
    return {
        "provider_id": provider.public_id,
        "provider_code": provider.code,
        "provider_name": provider.name,
        "capabilities": sorted({check.check_type for check in terminal}),
        "status": _metric_status(
            total=len(terminal),
            availability=availability,
            error_rate=error_rate,
        ),
        "total_attempts": len(terminal),
        "successful_attempts": completed,
        "failed_attempts": failed,
        "availability_percent": availability,
        "error_rate_percent": error_rate,
        "latency_ms": {
            "p50": _percentile(durations, 0.50),
            "p95": _percentile(durations, 0.95),
            "maximum": max(durations) if durations else None,
        },
        "error_codes": [
            {"code": code, "count": count}
            for code, count in sorted(error_codes.items())
        ],
    }


def provider_health_scope(
    *, tenant, environment: str, window_hours: int = 24, provider_id: str = ""
) -> dict:
    """Return payload-free health metrics for one tenant and environment."""
    since = timezone.now() - timedelta(hours=window_hours)
    routes = list(
        ProviderRoute.objects.filter(
            tenant=tenant,
            environment=environment,
            status=ProviderRouteStatus.ACTIVE,
        )
        .prefetch_related(
            Prefetch(
                "steps",
                queryset=ProviderRouteStep.objects.select_related(
                    "provider", "circuit_state"
                ).only(
                    "id",
                    "route_id",
                    "provider_id",
                    "position",
                    "provider__id",
                    "provider__public_id",
                    "provider__code",
                    "provider__status",
                    "circuit_state__id",
                    "circuit_state__status",
                    "circuit_state__retry_after",
                ),
            )
        )
        .order_by("capability", "priority", "route_key")
    )
    if provider_id:
        routes = [
            route
            for route in routes
            if any(step.provider.public_id == provider_id for step in route.steps.all())
        ]
    route_provider_ids = {
        step.provider_id for route in routes for step in route.steps.all()
    }
    provider_filter_ids = set(route_provider_ids)
    if provider_id:
        selected_provider = (
            ProviderCheck.objects.filter(tenant=tenant, provider__public_id=provider_id)
            .values_list("provider_id", flat=True)
            .first()
        )
        if selected_provider is not None:
            provider_filter_ids.add(selected_provider)
    checks_query = ProviderCheck.objects.filter(
        tenant=tenant,
        started_at__gte=since,
    )
    if environment == "sandbox":
        checks_query = checks_query.filter(
            Q(verification__project__environment="sandbox")
            | Q(verification__project__isnull=True)
        )
    else:
        checks_query = checks_query.filter(
            verification__project__environment=environment
        )
    if provider_id:
        checks_query = checks_query.filter(provider_id__in=provider_filter_ids)
    checks = list(
        checks_query.select_related("provider")
        .only(
            "id",
            "provider_id",
            "check_type",
            "status",
            "error_code",
            "duration_ms",
            "started_at",
            "provider__public_id",
            "provider__code",
            "provider__name",
            "provider__status",
        )
        .order_by("started_at", "id")
    )

    checks_by_provider = defaultdict(list)
    checks_by_provider_capability = defaultdict(list)
    providers = {}
    for check in checks:
        checks_by_provider[check.provider_id].append(check)
        checks_by_provider_capability[(check.provider_id, check.check_type)].append(
            check
        )
        providers[check.provider_id] = check.provider
    provider_metrics = {
        provider_pk: _provider_metric(provider, checks_by_provider[provider_pk])
        for provider_pk, provider in providers.items()
    }

    route_metrics = []
    for route in routes:
        steps = []
        for step in route.steps.all():
            try:
                circuit = step.circuit_state
                circuit_status = circuit.status
                retry_after = circuit.retry_after
            except ProviderCircuitState.DoesNotExist:
                circuit_status = ProviderCircuitStatus.CLOSED
                retry_after = None
            effective_circuit_status = circuit_status
            if (
                circuit_status == ProviderCircuitStatus.OPEN
                and retry_after is not None
                and retry_after <= timezone.now()
            ):
                effective_circuit_status = ProviderCircuitStatus.HALF_OPEN
            capability_metric = _provider_metric(
                step.provider,
                checks_by_provider_capability[(step.provider_id, route.capability)],
            )
            step_health = capability_metric["status"]
            if step.provider.status != ProviderStatus.ACTIVE:
                step_health = "unavailable"
            steps.append(
                {
                    "position": step.position,
                    "provider_id": step.provider.public_id,
                    "provider_code": step.provider.code,
                    "eligible": (
                        step.provider.status == ProviderStatus.ACTIVE
                        and effective_circuit_status != ProviderCircuitStatus.OPEN
                    ),
                    "circuit_status": effective_circuit_status,
                    "circuit_retry_after": (
                        retry_after.isoformat() if retry_after is not None else None
                    ),
                    "health": step_health,
                }
            )
        route_status = "no_data"
        if steps:
            if all(not step["eligible"] for step in steps):
                route_status = "unavailable"
            elif any(
                step["circuit_status"] != ProviderCircuitStatus.CLOSED
                or step["health"] in {"degraded", "unavailable"}
                for step in steps
            ):
                route_status = "degraded"
            elif any(step["health"] == "healthy" for step in steps):
                route_status = "healthy"
        for step in steps:
            step.pop("eligible")
        route_metrics.append(
            {
                "route_id": route.public_id,
                "route_key": route.route_key,
                "route_version": route.version,
                "capability": route.capability,
                "status": route_status,
                "steps": steps,
            }
        )

    return {
        "scope": {
            "tenant_id": tenant.public_id,
            "environment": environment,
            "window_hours": window_hours,
            "window_started_at": since.isoformat(),
        },
        "providers": sorted(
            (
                metric
                for metric in provider_metrics.values()
                if not provider_id or metric["provider_id"] == provider_id
            ),
            key=lambda item: item["provider_code"],
        ),
        "routes": route_metrics,
    }


def grouped_platform_provider_health(
    *, provider_id: str, window_hours: int = 24
) -> list[dict]:
    """Return separately scoped groups for a platform-admin provider view."""
    from apps.providers.models import Provider
    from apps.tenants.models import Tenant

    provider = Provider.objects.filter(public_id=provider_id).first()
    if provider is None:
        return []
    tenant_ids = set(
        ProviderCheck.objects.filter(provider=provider).values_list(
            "tenant_id", flat=True
        )
    )
    tenant_ids.update(
        ProviderRouteStep.objects.filter(provider=provider).values_list(
            "route__tenant_id", flat=True
        )
    )
    if provider.tenant_id:
        tenant_ids.add(provider.tenant_id)
    groups = []
    for tenant in Tenant.objects.filter(pk__in=tenant_ids).order_by("public_id"):
        for environment in ("sandbox", "production"):
            snapshot = provider_health_scope(
                tenant=tenant,
                environment=environment,
                window_hours=window_hours,
                provider_id=provider_id,
            )
            if snapshot["providers"] or snapshot["routes"]:
                groups.append(snapshot)
    return groups
