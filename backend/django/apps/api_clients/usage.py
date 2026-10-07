"""Durable atomic organization/environment and client quota reservations."""

from math import ceil
from datetime import timedelta, timezone as datetime_timezone

from django.db import transaction
from django.utils import timezone

from apps.api_clients.models import APIUsageBucket, APIUsageQuota


def periods(now):
    now = now.astimezone(datetime_timezone.utc)
    minute = now.replace(second=0, microsecond=0)
    month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    next_month = (month.replace(day=28) + timedelta(days=4)).replace(day=1)
    return [
        ("minute", minute, minute + timedelta(minutes=1)),
        ("month", month, next_month),
    ]


def quota_for_client(client):
    environment = client.project.environment if client.project_id else "sandbox"
    quota, _ = APIUsageQuota.objects.get_or_create(
        tenant_id=client.tenant_id, environment=environment
    )
    return quota


@transaction.atomic
def reserve_request(client, *, now=None):
    now = now or timezone.now()
    quota = quota_for_client(client)
    quota = APIUsageQuota.objects.select_for_update(no_key=True).get(pk=quota.pk)
    windows = periods(now)
    entries = []
    for (period, start, end), limit in zip(
        windows, [quota.requests_per_minute, quota.requests_per_month]
    ):
        bucket, _ = APIUsageBucket.objects.get_or_create(
            quota=quota,
            client_key="",
            period=period,
            starts_at=start,
            defaults={"ends_at": end},
        )
        entries.append((bucket, limit))
    minute, start, end = windows[0]
    client_bucket, _ = APIUsageBucket.objects.get_or_create(
        quota=quota,
        client_key=client.public_id,
        period=minute,
        starts_at=start,
        defaults={"ends_at": end},
    )
    entries.append((client_bucket, client.rate_limit_per_minute))
    exhausted = [
        (bucket, limit) for bucket, limit in entries if bucket.accepted >= limit
    ]
    allowed = not exhausted
    for bucket, _ in entries:
        if allowed:
            bucket.accepted += 1
        else:
            bucket.denied += 1
        bucket.save(update_fields=["accepted", "denied", "updated_at"])
    limiting, limit = (
        max(exhausted, key=lambda entry: entry[0].ends_at)
        if exhausted
        else min(entries, key=lambda entry: max(0, entry[1] - entry[0].accepted))
    )
    wait = (
        max(
            1,
            ceil(
                max((bucket.ends_at - now).total_seconds() for bucket, _ in exhausted)
            ),
        )
        if exhausted
        else 0
    )
    headers = {
        "X-RateLimit-Limit": str(limit),
        "X-RateLimit-Remaining": str(max(0, limit - limiting.accepted)),
        "X-RateLimit-Reset": str(int(limiting.ends_at.timestamp())),
        "X-RateLimit-Environment": quota.environment,
        "X-RateLimit-Organization-Minute-Limit": str(quota.requests_per_minute),
        "X-RateLimit-Organization-Minute-Remaining": str(
            max(0, quota.requests_per_minute - entries[0][0].accepted)
        ),
        "X-RateLimit-Organization-Month-Limit": str(quota.requests_per_month),
        "X-RateLimit-Organization-Month-Remaining": str(
            max(0, quota.requests_per_month - entries[1][0].accepted)
        ),
        "X-RateLimit-Client-Minute-Limit": str(client.rate_limit_per_minute),
        "X-RateLimit-Client-Minute-Remaining": str(
            max(0, client.rate_limit_per_minute - client_bucket.accepted)
        ),
    }
    if wait:
        headers["Retry-After"] = str(wait)
    return allowed, headers, wait


def usage_for_tenant(tenant):
    result = []
    now = timezone.now()
    for environment in ("sandbox", "production"):
        quota = APIUsageQuota.objects.filter(
            tenant=tenant, environment=environment
        ).first()
        values = {}
        for period, start, end in periods(now):
            bucket = (
                APIUsageBucket.objects.filter(
                    quota=quota, client_key="", period=period, starts_at=start
                ).first()
                if quota
                else None
            )
            limit = (
                (
                    quota.requests_per_minute
                    if period == "minute"
                    else quota.requests_per_month
                )
                if quota
                else (6000 if period == "minute" else 1000000)
            )
            values[period] = {
                "limit": limit,
                "accepted": bucket.accepted if bucket else 0,
                "denied": bucket.denied if bucket else 0,
                "remaining": max(0, limit - (bucket.accepted if bucket else 0)),
                "resets_at": end.isoformat(),
            }
        result.append({"environment": environment, **values})
    return result
