import json
from django.core.management.base import BaseCommand, CommandError
from common.backup import restore_backup


class Command(BaseCommand):
    help = (
        "Restore authenticated backups into empty isolated PostgreSQL/object targets."
    )

    def add_arguments(self, parser):
        parser.add_argument("--archive-directory", required=True)
        parser.add_argument("--staging-root", required=True)

    def handle(self, *args, **options):
        try:
            report = restore_backup(
                options["archive_directory"], options["staging_root"]
            )
        except Exception:
            raise CommandError(
                "Isolated restore failed; retain isolation and inspect restricted diagnostics."
            ) from None
        self.stdout.write(json.dumps(report))
