"""Start or resume bounded tenant/environment encryption rotation."""

from django.core.management.base import BaseCommand, CommandError

from common.tenant_key_rotation import (
    resume_database_batch,
    resume_object_batch,
    start_rotation,
)


class Command(BaseCommand):
    help = "Start or resume a tenant/environment key rotation; output contains counts and IDs only."

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument("--tenant", help="Tenant public ID for a new rotation.")
        group.add_argument("--resume", help="Existing rotation public ID.")
        parser.add_argument(
            "--environment", choices=["sandbox", "production", "shared"]
        )
        parser.add_argument("--batch-size", type=int, default=100)
        parser.add_argument("--max-batches", type=int, default=1)

    def handle(self, *args, **options):
        if (
            not 1 <= options["batch_size"] <= 1000
            or not 1 <= options["max_batches"] <= 1000
        ):
            raise CommandError("Batch size and max-batches must be between 1 and 1000.")
        if options["tenant"] and not options["environment"]:
            raise CommandError("A new rotation requires --environment.")
        if options["resume"] and options["environment"]:
            raise CommandError("Resumption uses the rotation's stored environment.")
        try:
            if options["tenant"]:
                job = start_rotation(options["tenant"], options["environment"])
            else:
                from apps.tenants.models import TenantKeyRotation

                job = TenantKeyRotation.objects.get(public_id=options["resume"])
            for _ in range(options["max_batches"]):
                if job.status == "completed":
                    break
                if job.status == "objects_pending":
                    job = resume_object_batch(
                        job.public_id, batch_size=min(options["batch_size"], 100)
                    )
                else:
                    job = resume_database_batch(
                        job.public_id, batch_size=options["batch_size"]
                    )
        except Exception:
            raise CommandError(
                "Tenant rotation could not complete this batch. Retain old keys and resume after correcting the dependency."
            ) from None
        self.stdout.write(
            f"rotation={job.public_id} environment={job.environment} state={job.status} migrated={job.migrated_count} conflicts={job.conflict_count}"
        )
