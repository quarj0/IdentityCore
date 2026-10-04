#!/bin/sh
set -eu
umask 077
: "${BACKUP_OUTPUT_ROOT:?}"
: "${BACKUP_QUIESCE_COMMAND:?}"
: "${BACKUP_RESUME_COMMAND:?}"
: "${BACKUP_DESTINATION_BUCKET:?}"
exec /opt/identitycore/backend/.venv/bin/python /opt/identitycore/backend/django/manage.py \
  create_encrypted_backup --output-root "$BACKUP_OUTPUT_ROOT" \
  --quiesce-command "$BACKUP_QUIESCE_COMMAND" --resume-command "$BACKUP_RESUME_COMMAND" \
  --destination-bucket "$BACKUP_DESTINATION_BUCKET"
