# Customer-managed KMS and HSM keys

Install the expand-only `tenants.0005` migration before starting this application version. Complete the tenant-envelope cutover in [tenant-key-rotation.md](tenant-key-rotation.md) first. Keep platform wrapping keys: tenant administration and encrypted grant tokens remain platform-wrapped so recovery does not require decrypting customer-controlled applicant data.

Use an enabled symmetric AWS KMS customer key's immutable key ARN. CloudHSM custom key stores and imported key material are supported through KMS. Grant the service's AWS IAM identity `kms:DescribeKey`, `kms:Encrypt` and `kms:Decrypt` on that key, with the corresponding key policy or grant. The normal AWS credential chain supplies service credentials; do not send AWS access keys to these endpoints. Optional grant tokens support newly created grants and are encrypted at rest and write-only. Record the approved KMS region and processor safeguards in deployment records. Only random 256-bit DEKs and random connection probes reach KMS; applicant plaintext does not.

An operator must explicitly provision the `manage_encryption` permission on the tenant's designated administration role through the existing permission-management process. The local seed includes it for Organization Administrator. Existing production roles do not acquire it automatically. Platform administrators and users holding only `manage_team` cannot administer customer keys.

Authenticated internal administration endpoints:

- `POST /api/v1/tenant/kms-bindings` with `environment` (`sandbox` or `production`), `key_arn`, and optional `grant_tokens` creates a pending binding. Sandbox and production are independent.
- `POST /api/v1/tenant/kms-bindings/{binding_id}/activate` checks enabled symmetric customer-key metadata and an Encrypt/Decrypt round trip with effective grants and authenticated tenant, environment, binding, version and purpose context. On success it activates the binding and returns a `rotation_id`. Failed validation rolls back activation and keeps the existing active key.
- `GET /api/v1/tenant/kms-bindings` returns bounded configuration summaries without tokens, DEKs or wrapped blobs.
- `POST /api/v1/tenant/kms-bindings/{binding_id}/disable` immediately rejects subsequent wrapping and unwrapping through that binding. It intentionally retains the active pointer so writes cannot silently fall back to platform encryption.

Resume the returned rotation with `rotate_tenant_keys --resume "$ROTATION_PUBLIC_ID" --batch-size 100 --max-batches 10`. New writes use the new version immediately; the resumable database/evidence scan re-encrypts existing content. Earlier binding versions remain available for old ciphertext reads. Do not disable or delete old customer keys until live data, evidence, backups and recovery requirements have been verified against retained versions. Rotation does not automatically retire key material.

KMS outages, disabled remote keys, revoked grants and explicitly disabled bindings fail closed. Requests have two-second connection/read timeouts and one attempt; errors contain no provider payload. Restore KMS availability and grants before resuming processing. To recover an explicitly disabled binding, activate it again: validation must pass and a fresh DEK rotation starts. Retain old binding records and customer key material for recovery. Backups contain wrapped DEKs and still require the corresponding customer key and permissions when restored.

Contract tests use an in-memory KMS fixture. Activation performs the live probe using the deployment's configured identity; passing contract tests does not certify an unconfigured real customer key.

To bound KMS load, unwrapped DEKs are reused only within one request or rotation batch, with at most 16 entries and a five-second TTL. The cache clears when the operation ends. Application disablement is checked on every use; remote grant/key revocation can take up to five seconds to affect an already unwrapped DEK within the current operation. New operations always contact KMS.
