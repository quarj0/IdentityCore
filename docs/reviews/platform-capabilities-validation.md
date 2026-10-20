# Governed platform extension validation

Local validation on 2026-10-20 for the bounded public v0.4 implementation.
This receipt describes repository/synthetic tests. It is not production,
independent provider/model, privacy/legal, physical-device or penetration-test assurance.
Protected independent review and current-head CI/Security remain merge requirements.

## Implemented scope

- Independent purpose-scoped evidence resources, immutable schemas, encrypted
  provenance, bounded lineage, supersession, holds and privacy retirement.
- Deterministic versioned claims, source-bound freshness, explicit independent
  conflict resolution, revocation, approved reuse and audience-bound field disclosure.
- Configuration/manifest/contract-scoped provider assurance reports with independent
  approval, expiry/revocation and separate conformance/assured levels.
- Signed durable pending provider operations, callbacks/polling, lease/deadline
  binding, original-worker resumption and durable remote cancel/delete reconciliation.
- Python, JavaScript, Java and .NET Provider SDK packages, public OpenAPI coverage
  and generated governed-resource methods/models in all four API client SDKs.

## Executed checks

| Check | Result |
| --- | --- |
| Complete Django suite | 1,366 tests; passed, 61 environment-dependent skips |
| Governed evidence/claims, subject privacy and provider PostgreSQL suite | 84 tests; passed, no skips |
| Exact CI PostgreSQL concurrency selection | 245 tests; passed, no skips; overlaps the focused suite |
| Public contract/generator/config regression selection | 111 tests; passed |
| Public route/OpenAPI parity | 111 operations validated |
| Real signed backend-to-Python-Provider-SDK HTTPS integration | Passed negotiation, sync, pending, polling, worker completion, callback signature and deletion over verified TLS |
| Redis shared provider replay | Passed with actual separate processes and key-rotation protection |
| Provider SDK native tests | Python 6, JavaScript 5, Java 6, .NET 6; passed, including real process replay and stale-worker fencing |
| Packaged SDK HTTP/worker assurance | All four languages passed all 17 `provider-assurance/v1` cases |
| API client native suites | Passed Python, JavaScript, Java and .NET, including new governed scope/header/user-JWT and strict wire-enum checks |
| Live API client HTTP compatibility | Python and JavaScript passed against an isolated migrated Django backend; Java/.NET live jobs remain part of hosted CI |
| Distribution builds | Python wheel/sdist, Java JAR/sources and .NET NuGet built; JavaScript archive packed |
| Other checks | No migration drift; processing inventory valid (11 activities, 1,421 fields); generated model/method drift, TypeScript declarations, Ruff, changed Markdown links and whitespace checks passed |

The complete Django SQLite suite intentionally skips environment-dependent tests.
The focused and full CI PostgreSQL selections exercise actual locking/concurrency;
Redis and TLS checks execute their real transport/process boundaries. Suite counts
are separate runs and must not be added as a count of distinct tests.

## Reproduce

Run `scripts/test_all.sh` with the documented Python, Node, Java, .NET and frontend
toolchains. `make check-sdk-models` verifies both generated models and governed
methods. CI also applies migrations to empty PostgreSQL, runs its concurrency
selection, and retains the four SDK conformance artifacts. See the job definitions
in [CI](../../.github/workflows/ci.yml) for exact commands and fixture services.

The [conformance guide](../../provider-sdk/conformance/README.md) documents each
language's real HTTP harness command. Artifacts identify the SDK, suite, transport
and case outcomes with `deployment_assurance: false`; they contain no subject
values, raw messages, credentials or lease tokens. The harness includes controlled
clock/worker actions only for synthetic testing and must never be deployed.

Runtime operations and authorization boundaries are documented in
[governed resources](../operations/governed-resources.md) and
[provider operations](../operations/provider-operations.md). Retained deployment
reports and independent references require their own accountable approval.
