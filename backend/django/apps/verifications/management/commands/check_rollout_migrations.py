from django.core.management.base import BaseCommand, CommandError
from django.contrib.postgres.operations import AddIndexConcurrently
from django.db import connection
from django.db.migrations.executor import MigrationExecutor

from common.rollout_migrations import expand_safe


class Command(BaseCommand):
    help = "Block pending migrations that cannot automatically establish old/new code overlap."

    def handle(self, *args, **options):
        try:
            executor = MigrationExecutor(connection)
            plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
            unsafe = sum(
                1
                for migration, backwards in plan
                for operation in migration.operations
                if backwards
                or not expand_safe(operation)
                or (isinstance(operation, AddIndexConcurrently) and migration.atomic)
            )
        except Exception:
            raise CommandError(
                "Migration compatibility could not be established."
            ) from None
        if unsafe:
            raise CommandError(
                f"Promotion blocked: {unsafe} pending operations require a staged compatibility design."
            )
        self.stdout.write("Pending migrations support an additive rollout.")
