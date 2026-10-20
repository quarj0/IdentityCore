# IdentityCore Provider SDK for .NET

`IdentityCore.Provider` implements the signed `ic-provider-v1` transport and
`ic-provider-operations-v1` durable operation contract. This package implements
provider endpoints; `sdk/dotnet` is the separate IdentityCore API client.

The library targets .NET 8 for compatibility; deploy on a supported patched
runtime (prefer .NET 10 LTS for new deployments). Use `ProviderRuntime.HandleAsync`
in your HTTP framework, passing the exact method, path including query, raw body
bytes and signature headers. Forward the returned status, headers and bytes
unchanged. Require HTTPS at the host and bound the body before buffering.

Construct `SigningKey` per approved configuration using `Wire.DeriveSigningSecret`
with its provider API key, tenant, environment and allowed capabilities. Construct
`SQLiteStore` with a separate 32-byte encryption key from your secret manager and
a database path inside a private directory. Supply capability handlers and explicit
cancel/delete handlers. Return `true` only after cancellation/deletion of external
jobs, files and downstream copies has succeeded. Failures return a retryable error;
local worker ownership is fenced before lifecycle handlers execute.

Run `WorkOnceAsync` from a worker loop; admission persists inputs before returning
pending, and worker leases renew automatically. Use the operation ID as the
idempotency key for external side effects. Expired worker leases can retry: the
SDK does not promise exactly-once side effects. `CallbackAsync` returns a signed
completion body and headers; deliver only to the configured IdentityCore origin
plus the validated callback path, verify the signed receipt against its nonce,
and retry transient delivery failures. Polling remains available.

SQLite/WAL is a durable single-host reference, including cross-process replay
claims and fenced jobs. Implement `IOperationStore` on a shared transactional
service for multiple hosts; never substitute an in-memory replay cache. Run
`ExpireAsync` regularly. Delete acknowledgments erase live encrypted content and
retain only an encrypted binding hash and operational metadata. Configure removal
of expired records, logs, backups and storage encryption keys under your retention
policy; deleting live rows does not erase historical backups or WAL snapshots.
Never log raw messages, leases, values, authorization headers or secrets.

Build/test/package:

```sh
dotnet test tests/IdentityCore.Provider.Tests/IdentityCore.Provider.Tests.csproj
dotnet pack src/IdentityCore.Provider/IdentityCore.Provider.csproj -c Release
```

Proprietary; see LICENSE.
