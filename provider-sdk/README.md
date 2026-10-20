# IdentityCore Provider SDKs

Provider packages implement the server side of the signed provider protocol and
its durable async operations. They are separate from the customer API clients in
[`sdk`](../sdk/README.md). All packages are proprietary; see their LICENSE files.

| Package | Runtime baseline | Build and tests |
| --- | --- | --- |
| [Python `identitycore-provider`](python/README.md) | Python 3.12+ | `python -m unittest discover -s provider-sdk/python/tests`; `python -m build provider-sdk/python` |
| [JavaScript `@identitycore/provider`](javascript/README.md) | Node 24+ | `npm test --prefix provider-sdk/javascript`; `npm pack ./provider-sdk/javascript --dry-run` |
| [Java `io.identitycore:identitycore-provider`](java/README.md) | Java 17+ | `mvn -f provider-sdk/java/pom.xml test package` |
| [.NET `IdentityCore.Provider`](dotnet/README.md) | .NET 8 library; prefer .NET 10 LTS deployment | `dotnet test provider-sdk/dotnet/tests/IdentityCore.Provider.Tests/IdentityCore.Provider.Tests.csproj`; `dotnet pack provider-sdk/dotnet/src/IdentityCore.Provider/IdentityCore.Provider.csproj` |

Packages are built and validated in CI. They are not automatically published to
public registries; distribution requires the owner's license and release process.

All four support exact-byte HMAC authentication, version/capability/environment
negotiation, strict bounded JSON, durable pending admission, polling, signed
callbacks, fenced worker generations, renewable leases, explicit cancel/delete
handlers, encrypted SQLite storage and atomic replay claims across processes.
Configure signing keys and a distinct storage encryption key through your secret
manager. An in-memory replay store is never the default. Use a shared transactional
store adapter for multiple hosts; the reference SQLite/WAL store supports one
local host, not network filesystems or separate pod copies.

Pass raw HTTP bytes through the framework-neutral runtime. Its returned body and
signature headers must reach the caller unchanged. Require HTTPS in deployment,
keep callback origins preconfigured, and enforce body limits before buffering.
Use stable operation IDs for idempotent external side effects. Delete handlers
must acknowledge actual external cleanup before the runtime acknowledges deletion.
Retention schedules, holds, backups, downstream processors and key retirement are
explicit deployment responsibilities.

[The conformance directory](conformance/README.md) contains the original isolated
five-case fixture contract and the 17-case packaged-SDK HTTP/worker suite. Test
drivers expose synthetic stdin controls and must never be deployed. Synthetic
protocol tests do not certify a real provider, model or production environment.

Operation deadlines use RFC 3339 with years 0001–9999, at most six fractional
second digits, and timezone offsets within ±14:00. IdentityCore emits UTC. Lease
generations are positive integers within the JavaScript safe-integer range.
