# Encrypted backup and isolated restore

The initial pilot targets are **RPO 24 hours** and **RTO 4 hours**, matching
[deployment planning](../architecture/deployment.md). The supplied systemd timer
runs twice daily, leaving recovery headroom for a missed attempt. The service
must complete within two hours. Alert on failed jobs immediately and on a last
successful archive older than 18 hours; stop a traffic ramp if freshness reaches
24 hours. Account for detection, provisioning, key access, object copying,
database restore and tenant validation when measuring production RTO.

## Install automation

Provision the backup service account and PostgreSQL client tools at the deployed
major version. Install `ops/backups/identitycore-backup.service` and `.timer`,
then enable the timer and run the first backup manually. The service account needs
read access to source storage/database, a separate write-only archive grant,
permission to execute the approved quiesce/resume hooks and private backup output.
Install `/etc/identitycore/backup.env` owner-only with:

- Normal Django database and source-storage settings, plus application/media key
  access from the approved secret manager.
- `IDENTITYCORE_BACKUP_KEY_FILE`: an owner-only file with a base64 32-byte random
  key. Keep a versioned escrow copy separately; rotation retains old restore keys.
- `BACKUP_OUTPUT_ROOT=/var/lib/identitycore-backups`.
- `BACKUP_QUIESCE_COMMAND` and `BACKUP_RESUME_COMMAND`: JSON argv arrays. No shell
  evaluation occurs. Quiesce must drain/stop API and processing, retention and
  webhook workers, block direct storage writes (including outstanding upload
  grants), and wait for in-flight writes to finish. Resume must reverse even a
  partially failed quiesce. An empty hook or non-zero hook result fails the job. Resume must be idempotent;
  systemd also runs it with ExecStopPost after timeout or process termination.
- `BACKUP_S3_ENDPOINT_URL`, `BACKUP_S3_ACCESS_KEY_ID`,
  `BACKUP_S3_SECRET_ACCESS_KEY`, `BACKUP_S3_REGION`, and
  `BACKUP_DESTINATION_BUCKET`: a separate restricted archive repository.
  Set `BACKUP_S3_KMS_KEY_ID` when archive policy requires KMS SSE rather than AES256.

Hooks are environment-specific deployment controls; the repository cannot safely
invent production container names or storage grant changes. Exercise hooks and
failure/resume paths with the environment owner before enabling the schedule.
The example service is not ready until those hooks and failure notifications are
configured. Integrate systemd failure and freshness into the approved on-call
system; do not count a local encrypted file as success if remote publication fails.

Enable `IDENTITYCORE_TELEMETRY_ENABLED=1` and configure the private OTLP endpoint
for backup freshness/failure alerts in the monitoring stack. Success is exported
only after remote publication, and failures export a timestamp for immediate
alerting. The systemd unit fixes the deployment environment to production; use
a distinct sandbox unit/environment for non-production backups.

Configure archive bucket versioning, deny replacement/deletion to the backup
writer, and apply `ops/backups/lifecycle.json` (14-day expiry) only after privacy
approval of the retention period. Keep restore/deletion grants separate. Remove
local encrypted spool copies under the same approved period. Restrict encryption
key access, logs, output and restore evidence. Never put keys or archives in GitHub
artifacts. Escrow application key versions outside the archive; media and encrypted
fields cannot be decoded without them. Backups can contain previously deleted
records: reconcile deletion requests and legal holds before any restored service
returns to production, and expire backup copies under the approved policy.

## Restore into isolation

Provision an empty PostgreSQL database with a name ending `_restore` or `_drill`,
empty bucket targets preserving media/temp/evidence/public aliasing, and a private
encrypted-volume or tmpfs staging root. Block outbound provider, webhook, mail and
SMS access, and keep workers stopped. Use least-privilege target storage/database
credentials, separately escrowed application keys and the correct backup key.

Set `IDENTITYCORE_RESTORE_ISOLATED=1`. In this mode storage routing ignores restored
platform overrides and uses explicit target environment settings. Download a
completed backup prefix with `common.backup.download_backup`; success is published
last. Use the isolated management command:

```sh
python backend/django/manage.py restore_encrypted_backup \
  --archive-directory /private/archive/BACKUP_ID \
  --staging-root /private/encrypted-staging
```

The command authenticates every member before mutation, restores original object
headers with target encryption policy, restores PostgreSQL in one transaction,
and verifies all recorded database/object references and object checksums.
Any failure leaves the target isolated; discard the failed **synthetic/isolated**
target through the approved procedure and retry into a new empty target. It never
restores over a populated database or source bucket. These controls support a
restore drill, not automatic production promotion.

Record backup age, total recovery time, data consistency, application-key access,
two-tenant allow/deny access checks, deletion/hold reconciliation, owner and UTC
completion. Run monthly and after encryption/schema/storage changes. Retain
payload-free drill reports for 90 days in the restricted readiness system.

## Reproduce the synthetic drill

```sh
python scripts/prepare_operational_drill.py --directory /tmp/identitycore-drill
docker compose --env-file /tmp/identitycore-drill/drill.env \
  -p identitycore-drill -f ops/drills/compose.yaml up -d
backend/.venv/bin/python scripts/run_restore_drill.py \
  --env-file /tmp/identitycore-drill/drill.env \
  --backup-key-file /tmp/identitycore-drill/backup.key \
  --report /tmp/restore-report.json
```

Use new dedicated volumes/databases for each run. The drill uses real PostgreSQL
17 and a Moto HTTP S3 fixture, not production data or real storage IAM. It proves
client-encryption, remote archive round-trip, restore/reference/checksum behavior,
application field decryption and tenant API isolation. Validate actual S3/KMS
permissions, production volume, quiesce controls and pager delivery separately in
the deployment readiness record. Checked-in reports state these limits explicitly.
