from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import connection


class Command(BaseCommand):
    help = "Apply compatible expansion migrations with a bounded PostgreSQL lock wait."

    def handle(self, *args, **options):
        if connection.vendor != "postgresql":
            raise CommandError("Production rollout migrations require PostgreSQL.")
        call_command("check_rollout_migrations", stdout=self.stdout)
        with connection.cursor() as cursor:
            cursor.execute("SHOW lock_timeout")
            previous = cursor.fetchone()[0]
            cursor.execute("SELECT set_config('lock_timeout', '3000ms', false)")
        try:
            call_command("migrate", interactive=False, stdout=self.stdout)
        except Exception:
            raise CommandError(
                "Rollout migration failed; promotion is blocked and committed schema is retained."
            ) from None
        finally:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT set_config('lock_timeout', %s, false)", [previous]
                )
