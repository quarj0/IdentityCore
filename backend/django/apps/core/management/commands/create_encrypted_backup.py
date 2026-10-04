import json
from django.core.management.base import BaseCommand, CommandError
from common.backup import create_backup, publish_backup, record_backup_result


class Command(BaseCommand):
    help = (
        "Create a client-encrypted PostgreSQL/object backup with paired writer hooks."
    )

    def add_arguments(self, parser):
        parser.add_argument("--output-root", required=True)
        parser.add_argument("--quiesce-command", required=True)
        parser.add_argument("--resume-command", required=True)
        parser.add_argument("--destination-bucket", required=True)

    def handle(self, *args, **options):
        try:
            directory, report = create_backup(
                options["output_root"],
                json.loads(options["quiesce_command"]),
                json.loads(options["resume_command"]),
            )
            publish_backup(directory, options["destination_bucket"])
        except Exception:
            record_backup_result(True)
            raise CommandError(
                "Encrypted backup failed; inspect restricted infrastructure diagnostics and verify writers resumed."
            ) from None
        record_backup_result(False)
        self.stdout.write(json.dumps({**report, "archive_publication": "pass"}))
