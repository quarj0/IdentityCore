# ADR 047: Tenant data envelopes and resumable key rotation

Status: Accepted

Tenant-owned encrypted database fields and encrypted evidence objects use random per-tenant, per-environment data encryption keys (DEKs), versioned independently of the platform wrapping key. Stored key records contain only authenticated wrapped DEKs. AES-256-GCM envelope associated data binds the tenant public ID, environment, key version and field/object purpose. Readers supply the expected tenant; copied ciphertext cannot decrypt in another tenant's row or object path. Existing platform-encrypted version-one envelopes remain readable while retained platform keys are available.

A tenant public ID is the key namespace so a tenant's first database save can encrypt its settings before an integer primary key exists. Key records use a unique tenant/environment/version and a unique active-key constraint per tenant/environment. New writes select the active version at encryption time. Old versions remain decryptable during rotation. Platform-global records and historical migration models retain their platform envelope; customer-owned content uses tenant envelopes.

Database fields encrypt in instance-aware pre-save and decrypt through an instance-aware descriptor. Raw values queries do not decrypt tenant envelopes without expected row ownership. Backup inventory reads instances with ownership context. Bulk writes of tenant-owned encrypted values require explicitly bound values; privacy erasure uses instance-aware writes. Arbitrary input dictionaries cannot masquerade as already-prepared ciphertext.

Encrypted object storage callers pass the expected tenant explicitly; encryption never infers ownership from client metadata. Evidence JSON/PDF objects preserve content type inside authenticated envelopes. Rotation runs in bounded resumable batches and uses compare-and-swap so concurrent content changes are not overwritten. It reports counts and opaque identifiers, never plaintext keys or content. Operators retain old keys until database and evidence objects are verified migrated and outstanding old-version writes are drained.

Customer KMS integration supplies a wrapping-provider interface around the same DEKs, with tenant-bound authenticated context. Provider outages and disabled keys fail closed. A later storage-routing change reuses explicit tenant object context. Database expansion must install the key-record tables before this application code starts; staged rollout must retain readers for old envelopes and all referenced wrapping keys.

Sandbox and production have separate key versions and authenticated environment context. Tenant administration records (for example staff authentication and tenant settings) use a distinct shared administration key scope. Environment is derived from authoritative project/verification relations, never request or applicant metadata. Legacy project-less verification cases belong to sandbox.
