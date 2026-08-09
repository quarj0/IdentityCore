# Processing job recovery

Identity document and biometric processing are recorded in the database before
they are dispatched to Celery. Each worker execution acquires a time-bounded
lease and refreshes its heartbeat between provider stages. A duplicate delivery
cannot run while that lease is active.

Celery Beat runs `recover_stale_processing_jobs_task` every 60 seconds by
default. It redispatches queued messages whose dispatch window elapsed and jobs
whose processing lease expired after worker loss or deployment. Attempts are
counted only when a worker acquires a job, so repeated recovery scans do not
consume the retry budget.

The defaults are configured through:

- `PROCESSING_JOB_LEASE_SECONDS=300`
- `PROCESSING_JOB_MAX_ATTEMPTS=3`
- `CELERY_PROCESSING_RECOVERY_BEAT_SECONDS=60`
- `PROCESSING_RECOVERY_BATCH_SIZE=100`

Set the lease longer than the expected maximum duration of one provider stage.
Alert when `ProcessingJob` rows remain queued or processing beyond one recovery
interval, or when any job reaches `exhausted`.

After the final attempt, the job is not silently retried. The related
verification is routed to Manual Review with reason code
`processing_retries_exhausted`, and an audit event records only the job ID, job
type, and attempt count. Submitted documents, biometric data, subject details,
and provider errors are not written to that audit metadata.

To validate recovery safely in a staging environment:

1. Submit a verification and stop an AI-processing worker after it acquires the
   job.
2. Wait for the lease and recovery interval to expire.
3. Start a worker and confirm the same durable job resumes with one additional
   attempt and no duplicate final decision.
4. Repeat until the configured attempt limit and confirm the verification moves
   to Manual Review with the exhaustion audit event.
