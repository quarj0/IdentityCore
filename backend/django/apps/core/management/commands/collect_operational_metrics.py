"""Export durable queue age even when every processing worker has stopped."""

import time
from django.core.management.base import BaseCommand
from django.db import close_old_connections
from django.db.models import Min, Q
from django.utils import timezone
from common.observability import configure, metrics, process_instance
from apps.verifications.models import ProcessingJob
from apps.webhooks.models import WebhookEvent


def backlog_samples():
    now = timezone.now()
    for environment in ("production", "sandbox"):
        project = Q(verification__project__environment=environment)
        endpoint = Q(webhook_endpoint__project__environment=environment)
        if environment == "sandbox":
            project |= Q(verification__project__isnull=True)
            endpoint |= Q(webhook_endpoint__project__isnull=True)
        for queue, queryset in (
            (
                "processing",
                ProcessingJob.objects.filter(
                    project, status__in=["queued", "processing"]
                ),
            ),
            ("webhooks", WebhookEvent.objects.filter(endpoint, status="pending")),
        ):
            oldest = queryset.aggregate(oldest=Min("created_at"))["oldest"]
            yield queue, environment, (
                max(0, (now - oldest).total_seconds()) if oldest else 0
            )


class Command(BaseCommand):
    help = "Export aggregate queue age via OTLP from an independent operations process."

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true")

    def handle(self, *args, **options):
        configure("identitycore-operations")
        gauge = metrics.get_meter("identitycore").create_gauge(
            "identitycore.backlog.oldest", unit="s"
        )
        heartbeat = metrics.get_meter("identitycore").create_gauge(
            "identitycore.backlog.heartbeat", unit="s"
        )
        while True:
            close_old_connections()
            for queue, environment, age in backlog_samples():
                gauge.set(
                    age,
                    {
                        "queue": queue,
                        "environment": environment,
                        "process_instance": process_instance(),
                    },
                )
            heartbeat.set(time.time(), {"process_instance": process_instance()})
            if options["once"]:
                return
            time.sleep(15)
