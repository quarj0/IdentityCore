import math
import re
from collections import Counter, defaultdict
from datetime import timedelta

from django.utils import timezone

from apps.providers.models import (
    ProviderCheck,
    ProviderCheckStatus,
    ProviderCircuitState,
    ProviderCircuitStatus,
    ProviderRoute,
    ProviderRouteStatus,
)


TERMINAL_HEALTH_STATUSES = {
    ProviderCheckStatus.COMPLETED,
    ProviderCheckStatus.FAILED,
    ProviderCheckStatus.TIMEOUT,
}
SAFE_ERROR_CODE = re.compile(r"^provider_[a-z0-9_]{1,55}$")


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
    return value if SAFE_ERROR_CODE.fullmatch(value) else "provider_error"


def _environment_for_check(check: ProviderCheck) -> str:
    return (
        check.verification.project.environment
        if check.verification.project_id
        else "sandbox"
    )


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
    checks = list(
        ProviderCheck.objects.filter(
            tenant=tenant,
            started_at__gte=since,
        )
        .select_related("provider", "verification", "verification__project")
        .order_by("started_at", "id")
    )
    checks = [check for check in checks if _environment_for_check(check) == environment]
    if provider_id:
        checks = [check for check in checks if check.provider.public_id == provider_id]

    checks_by_provider = defaultdict(list)
    providers = {}
    for check in checks:
        checks_by_provider[check.provider_id].append(check)
        providers[check.provider_id] = check.provider
    provider_metrics = {
        provider_pk: _provider_metric(provider, checks_by_provider[provider_pk])
        for provider_pk, provider in providers.items()
    }

    routes = (
        ProviderRoute.objects.filter(
            tenant=tenant,
            environment=environment,
            status=ProviderRouteStatus.ACTIVE,
        )
        .prefetch_related("steps__provider", "steps__circuit_state")
        .order_by("capability", "priority", "route_key")
    )
    route_metrics = []
    for route in routes:
        steps = []
        for step in route.steps.all():
            if provider_id and step.provider.public_id != provider_id:
                continue
            try:
                circuit = step.circuit_state
                circuit_status = circuit.status
                retry_after = circuit.retry_after
            except ProviderCircuitState.DoesNotExist:
                circuit_status = ProviderCircuitStatus.CLOSED
                retry_after = None
            steps.append(
                {
                    "position": step.position,
                    "provider_id": step.provider.public_id,
                    "provider_code": step.provider.code,
                    "circuit_status": circuit_status,
                    "circuit_retry_after": (
                        retry_after.isoformat() if retry_after is not None else None
                    ),
                    "health": provider_metrics.get(step.provider_id, {}).get(
                        "status", "no_data"
                    ),
                }
            )
        if provider_id and not steps:
            continue
        route_status = "no_data"
        if steps:
            if all(
                step["circuit_status"] == ProviderCircuitStatus.OPEN for step in steps
            ):
                route_status = "unavailable"
            elif any(
                step["circuit_status"] != ProviderCircuitStatus.CLOSED
                or step["health"] in {"degraded", "unavailable"}
                for step in steps
            ):
                route_status = "degraded"
            elif any(step["health"] == "healthy" for step in steps):
                route_status = "healthy"
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
            provider_metrics.values(), key=lambda item: item["provider_code"]
        ),
        "routes": route_metrics,
    }


def grouped_platform_provider_health(
    *, provider_id: str, window_hours: int = 24
) -> list[dict]:
    """Return separately scoped groups for a platform-admin provider view."""
    from apps.providers.models import Provider, ProviderRouteStep
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
