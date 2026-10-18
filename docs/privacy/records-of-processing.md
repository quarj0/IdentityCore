# Records of processing and data-flow inventory

The machine-checked [`processing-inventory.json`](processing-inventory.json) is the
repository record of processing activities (ROPA). It groups sensitive model fields by
processing purpose and records their code/storage location, retention rule, processors,
transfer boundary, and accountable roles. Schema v2 also catalogs every declared persisted model field (including encrypted
JSON containers and inherited authentication state) by exact source, model and
field. Each catalog entry resolves to its processing activity's purpose, locations,
retention, processors, transfer notes and owner roles. This deliberately includes
non-sensitive configuration/identifiers so a future sensitive field cannot escape
coverage through a classification omission. JSON containers cover all nested
payloads; versioned provider contracts and policy schemas define their contents.
The linked owner register records accountable roles, responsibilities and actual
repository paths; deployment personnel are assigned in the controlled register.

## Data flow

1. Platform users configure a tenant, policy, project, and provider assignments in
   Django/PostgreSQL.
2. A subject opens the verification portal, exchanges a fragment credential for a
   secure portal session, reviews the immutable consent artifact, and uploads evidence.
   A server-signed metadata envelope carries reported User-Agent and, only with an
   explicitly trusted ingress header, client IP to Django. Session, consent proof
   and audit records label attribution; absent trusted IP remains unknown. The
   envelope is not logged and does not change the transport peer used for throttling.
3. New media enters the temporary object-storage bucket. Django finalizes it into the
   protected media bucket and queues only the required checks.
4. The internal AI service or a tenant-selected provider returns normalized evidence;
   Django applies policy and persists the result and audit events.
5. Authorized users receive results through the dashboard/API/webhook. Retention jobs
   delete media and records according to tenant policy; compliance exports use the
   evidence bucket.

Platform administrator invitation emails are a separate platform-scoped outbox use.
Their single-use links are encrypted in notification delivery data, excluded from
previews, delivered through deployment email configuration and cleared after terminal
delivery. They never use tenant notification credentials. See
[platform invitations](../operations/platform-invitations.md).

## Operating procedure

- The **privacy owner** reviews purpose, lawful basis, retention, data-subject rights,
  transfer mechanism, and processor contracts before a new field/provider ships.
- The **domain owner** updates the JSON in the same pull request as a sensitive model,
  flow, provider, or storage change. Never put real personal data or secrets in it.
- The **security owner** reviews encryption, access, logging, export, deletion, and
  incident controls. Deployment-specific processor names, regions, subprocessors, and
  transfer safeguards belong in the controlled deployment register.
- Run `python scripts/check_processing_inventory.py`. CI rejects missing owner keys,
  required metadata, duplicate activity IDs/fields, missing/stale persisted fields,
  owner-register drift and source/owner paths that no longer exist. Run
  `python -m unittest discover -s scripts -p test_processing_inventory.py` for
  validator regressions. Field additions/removals must update `field_catalog` in
  the same PR; choose and review the processing activity rather than silently
  auto-accepting newly discovered fields.
- Approved provider manifests supply capability, environment, processor, residency,
  retention and transfer declarations. Review those alongside provider configuration
  approvals and the deployment processor register before assigning traffic. The
  inventory links provider models/runtime/runbooks and explicitly distinguishes
  encrypted credentials, provider evidence and minimal external risk inputs.
- API quota records contain only tenant/environment/client-window counters, remain
  in PostgreSQL/dashboard, and expire after 90 days. Workflow and operational model
  fields have an explicit activity rather than falling outside the inventory.

This inventory describes repository-controlled processing, not a claim of legal
completeness for every deployment. Each controller must add lawful bases, local
statutory periods, contacts, regions, and vendor agreements to its controlled ROPA.
