# Records of processing and data-flow inventory

The machine-checked [`processing-inventory.json`](processing-inventory.json) is the
repository record of processing activities (ROPA). It groups sensitive model fields by
processing purpose and records their code/storage location, retention rule, processors,
transfer boundary, and accountable roles. The grouping is intentional: migrations may
split one logical attribute into several columns without changing its processing purpose.

## Data flow

1. Platform users configure a tenant, policy, project, and provider assignments in
   Django/PostgreSQL.
2. A subject opens the verification portal, exchanges a fragment credential for a
   secure portal session, reviews the immutable consent artifact, and uploads evidence.
3. New media enters the temporary object-storage bucket. Django finalizes it into the
   protected media bucket and queues only the required checks.
4. The internal AI service or a tenant-selected provider returns normalized evidence;
   Django applies policy and persists the result and audit events.
5. Authorized users receive results through the dashboard/API/webhook. Retention jobs
   delete media and records according to tenant policy; compliance exports use the
   evidence bucket.

## Operating procedure

- The **privacy owner** reviews purpose, lawful basis, retention, data-subject rights,
  transfer mechanism, and processor contracts before a new field/provider ships.
- The **domain owner** updates the JSON in the same pull request as a sensitive model,
  flow, provider, or storage change. Never put real personal data or secrets in it.
- The **security owner** reviews encryption, access, logging, export, deletion, and
  incident controls. Deployment-specific processor names, regions, subprocessors, and
  transfer safeguards belong in the controlled deployment register.
- Run `python scripts/check_processing_inventory.py`. CI rejects missing owner keys,
  required metadata, duplicate activity IDs, and source paths that no longer exist.

This inventory describes repository-controlled processing, not a claim of legal
completeness for every deployment. Each controller must add lawful bases, local
statutory periods, contacts, regions, and vendor agreements to its controlled ROPA.
