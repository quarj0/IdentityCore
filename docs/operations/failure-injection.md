# Failure injection and recovery

Run the synthetic matrix with:

```sh
DJANGO_SETTINGS_MODULE=config.settings.testing python backend/django/manage.py test apps.verifications.test_failure_injection --noinput
```

The matrix injects concrete broker, database, object-storage transport, AI and
provider failures at their application boundaries, then checks persisted state and
recovery. It uses synthetic records and no production identities or credentials.
CI's backend suite discovers this module; the PostgreSQL suite also runs it against
real transactional storage. Adapter timeout/response tests and processing ownership
races remain part of their existing dedicated suites.

| Failure | Expected observable state | Recovery and runbook |
| --- | --- | --- |
| Redis/Celery publishing unavailable | Durable queued job, zero consumed attempts, `dispatch_unavailable`, expired dispatch window | Restore broker; the recovery sweep republishes once. [Processing recovery](processing-job-recovery.md) and [Incident response](incident-response.md). |
| Database write unavailable | Creation/finalization transaction rolls back; no partial job or decision is published | Restore database/readiness, retry the original operation. [Backup and restore](backup-restore.md) and [Processing ownership](processing-job-ownership.md). |
| Storage promotion unavailable | Valid biometric stage results and original upload remain retained; no final decision | Restore storage, recover the expired lease; finalization resumes without repeating biometric calls. [Processing recovery](processing-job-recovery.md). |
| AI unavailable | One manual-review system decision and safe `biometric_provider_unavailable` reason; submitted evidence remains available | Restore AI and resolve through review or a fresh policy-authorized attempt. Late workers cannot replace the review decision. [Processing recovery](processing-job-recovery.md). |
| Third-party provider unavailable | Bounded safe timeout attempts, fallback selection, open circuit | Restore provider; a single half-open probe closes the circuit after success. [Provider resilience](provider-route-resilience.md). |

Check queued job lease age and dispatch error codes, provider health/attempt records,
and safe decision reason codes. Never attach raw provider responses, document data,
signed URLs, credentials or exception messages to an incident record. Dispatch logs
retain only job ID and exception class. Worker error handlers preserve fixed public
messages and codes instead of copying raw exception text into provider checks or
review evidence.

A broker outage cannot remove a database-committed processing job. An unavailable
AI or provider cannot approve a case. A failed storage transfer cannot create a final
decision. Recovery must preserve one decision per case and respect current human
review ownership; the concurrent ownership regression suites verify those fences.
