# IdentityCore Provider SDK for Python

Requires Python 3.12+. This package implements the provider side of the signed
Provider Contract v1 and the separately negotiated `ic-provider-operations-v1`.
It is separate from the `identitycore` customer API client.

`ProviderRuntime.handle` accepts the exact HTTP method, path including query,
raw body bytes and headers. It authenticates before parsing, rejects ambiguous
JSON, enforces current key scope, and returns a signed response bound to the
request nonce. Framework adapters must preserve those bytes and enforce the
256 KiB request limit before buffering. Keys include their configured tenant,
environment and capability allowlist. Derive the message key from the environment
API credential with `derive_signing_secret`; never log credentials, bodies or
operation leases.

Construct `SQLiteStore` with a separate random 32-byte storage encryption key and
a database in a private directory. Its AES-GCM records bind ciphertext to the
operation ID. Replay claims and operation state are transactional across local
processes. SQLite/WAL supports one host on a local filesystem. For multiple hosts,
provide an equivalent shared transactional database store; independent pod copies
or a network filesystem do not provide distributed replay protection.

Asynchronous admission persists work before returning pending. A separate worker
calls `runtime.work_once()`. Business handlers receive the stable operation ID
and must use it to make external side effects idempotent. Worker generations and
expiring leases fence stale completion, but no protocol promises exactly-once
external side effects after a crash. The same admission ID is reconciled on retry.

Supply explicit cancel and delete handlers. They must be idempotent by operation
ID and return `True` only after their own processing/data actions are complete.
Cancellation fences workers and preserves content; deletion removes stored inputs,
results and the raw lease, retaining only an authenticated binding hash tombstone.
The runtime acknowledges external deletion only after the handler succeeds.
Expiration stops overdue work; deployment retention and legal-hold policy must
schedule destruction separately. Backup, filesystem snapshots and storage-key
retirement remain deployment responsibilities; logical deletion does not claim
cryptographic erasure of historical backups.

`runtime.callback(binding)` returns exact bytes and signing headers for an already
committed terminal result. Send them only to the preconfigured IdentityCore HTTPS
origin and the admitted callback path, with normal TLS verification and redirects
disabled. Re-sign with a fresh nonce on retry. Never follow a provider-supplied URL.

See the shared protocol and interoperability tests in `provider-sdk/conformance`.
Synthetic fixture success demonstrates protocol behavior and is not independent
provider certification or production approval.
