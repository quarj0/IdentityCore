# ADR 049: Tenant and environment object storage routing

Status: Accepted

Tenant storage routing uses immutable route records per tenant and environment. Each record names a deployment-approved bucket and residency region and contributes an opaque route identifier to every new upload and evidence key. An active route affects new objects only; old keys resolve through their original retained route. The application uses its configured S3 endpoint and credential identity and never accepts a tenant-provided endpoint or arbitrary bucket outside the deployment allowlist.

Canonical routed keys bind tenant, environment and route. Storage operations resolve the bucket from this authoritative record and reject malformed, conflicting or deleted routing references. Upload grants remain single-object PUT grants with bounded expiry and declared content type and size. Read grants permit only a single authorized object, with bounded expiry. Internal provider and AI transfers use storage references and required minimal purpose-bound attributes rather than embedding applicant evidence bytes in requests or logs.

Upload and evidence reads, writes, promotion, retry, deletion, rotation and backup inventory must all use the same route resolution. Residency and routing remain available through retained records, including after route replacement. Route records cannot be mutated in place or removed while retained object references exist. Legacy object keys continue using the existing configured storage buckets until an explicit audited migration is performed; legacy keys are not treated as routed objects.

Operators provision routes through a permission-restricted management command after approving the destination region, bucket access policy, encryption, retention and processor safeguards. Tests cover tenant/environment substitution, route replacement, signed grant bounds, reference-only transfers, deletion and backup routing.
