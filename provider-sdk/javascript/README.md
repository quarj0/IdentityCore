# IdentityCore Provider SDK for JavaScript / TypeScript

Requires Node.js 24 LTS or later. No runtime npm dependencies are required;
`node:sqlite` supplies the encrypted transactional reference store. TypeScript
applications should install the Node.js type declarations for their runtime.

The package exports `SigningKey`, `ProviderRuntime`, `SQLiteStore`, exact-wire
`sign`/`verify` helpers and the negotiated operation contracts. `handle`, `workOnce`
and `callback` are asynchronous and accept asynchronous custom database adapters
or capability/lifecycle handlers. The bundled SQLite store is for processes on
one host and a private local filesystem; use a shared transactional adapter for
multiple hosts. Supply a separate random 32-byte storage encryption key.

The runtime authenticates exact body bytes before parsing, rejects duplicate JSON
fields, enforces key tenant/environment/capability scope and atomically claims
replay nonces. HTTP adapters must enforce the 256 KiB limit before buffering.
Pending work persists before admission; worker leases fence late completion.
Business side effects and lifecycle handlers must be idempotent by operation ID.
Cancel preserves content while stopping work; delete acknowledges only after the
explicit deletion handler succeeds, then clears values and raw lease material.
Retention, legal holds, backups and storage-key rotation require deployment policy.

Signing keys and worker leases hide credentials and subject data from default
inspection. Never log raw requests, responses, callbacks, input values or errors
from underlying business handlers. A callback consists of exact bytes and headers;
send it only to the preconfigured IdentityCore HTTPS origin, with normal TLS
verification, fresh nonces on retry and redirects disabled.

This is the provider SDK, separate from the customer API client. Shared fixtures
and synthetic interoperability tests do not constitute independent certification.
