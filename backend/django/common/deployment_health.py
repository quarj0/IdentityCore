"""Instance readiness and operator-controlled draining without public mutation."""

from pathlib import Path

import redis
from django.conf import settings
from django.db import connection, transaction


def is_draining():
    try:
        return Path(settings.DEPLOYMENT_DRAIN_FILE).exists()
    except OSError:
        return True


def dependencies_ready():
    try:
        with transaction.atomic():
            with connection.cursor() as cursor:
                if connection.vendor == "postgresql":
                    cursor.execute("SET LOCAL statement_timeout = '2000ms'")
                cursor.execute("SELECT 1")
                if cursor.fetchone()[0] != 1:
                    return False
        client = redis.Redis.from_url(
            settings.CELERY_BROKER_URL, socket_connect_timeout=2, socket_timeout=2
        )
        try:
            return bool(client.ping())
        finally:
            client.close()
    except Exception:
        # Dependency exceptions can contain DSNs, broker passwords and request data.
        return False


def ready():
    return not is_draining() and dependencies_ready()
