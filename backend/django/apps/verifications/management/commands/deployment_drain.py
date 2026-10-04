import re
import time
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from common.deployment_health import dependencies_ready
from config.celery import app


class Command(BaseCommand):
    help = "Drain one explicitly named instance worker without killing in-flight work."

    def add_arguments(self, parser):
        parser.add_argument("--worker")
        parser.add_argument("--timeout", type=int, default=60)
        parser.add_argument("--resume", action="store_true")

    def handle(self, *args, **options):
        try:
            return self._handle(options)
        except CommandError:
            raise
        except Exception:
            raise CommandError(
                "Deployment drain failed; the instance remains unready."
            ) from None

    def _handle(self, options):
        marker = Path(settings.DEPLOYMENT_DRAIN_FILE)
        if not marker.is_absolute():
            raise CommandError(
                "DEPLOYMENT_DRAIN_FILE must be an absolute instance-local path."
            )
        if options["resume"]:
            if not dependencies_ready():
                raise CommandError(
                    "Dependencies are unavailable; the drain marker is retained."
                )
            marker.unlink(missing_ok=True)
            self.stdout.write(
                "Instance resumed. Start replacement consumers before routing traffic."
            )
            return
        worker = options.get("worker")
        if not worker or not re.fullmatch(r"[A-Za-z0-9_.@-]{1,200}", worker):
            raise CommandError("An explicit worker name is required.")
        timeout = options["timeout"]
        if not 1 <= timeout <= 600:
            raise CommandError("Drain timeout must be between 1 and 600 seconds.")
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.touch(mode=0o600, exist_ok=True)
        inspect = app.control.inspect(destination=[worker], timeout=2)
        if worker not in (inspect.ping() or {}):
            raise CommandError(
                "Worker did not acknowledge drain; the marker is retained."
            )
        queues = (inspect.active_queues() or {}).get(worker)
        if not isinstance(queues, list):
            raise CommandError("Worker queues are unavailable; the marker is retained.")
        for queue in queues:
            name = queue.get("name", "")
            if not re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", name):
                raise CommandError("Worker queue configuration is unsupported.")
            replies = app.control.cancel_consumer(
                name, destination=[worker], reply=True, timeout=2
            )
            if not any(
                isinstance(reply.get(worker), dict)
                and "ok" in reply[worker]
                and "error" not in reply[worker]
                for reply in replies or []
            ):
                raise CommandError(
                    "Consumer cancellation was not acknowledged; the marker is retained."
                )
        deadline = time.monotonic() + timeout
        empty_snapshots = 0
        while time.monotonic() < deadline:
            pending = 0
            for method in (inspect.active, inspect.reserved, inspect.scheduled):
                tasks = (method() or {}).get(worker)
                if not isinstance(tasks, list):
                    raise CommandError(
                        "Worker drain state is unavailable; the marker is retained."
                    )
                pending += len(tasks)
            empty_snapshots = empty_snapshots + 1 if pending == 0 else 0
            if empty_snapshots >= 2:
                self.stdout.write(
                    "Instance drained. Stop the worker gracefully before replacing it."
                )
                return
            time.sleep(0.25)
        raise CommandError(
            "Drain timed out; in-flight work and the drain marker are retained."
        )
