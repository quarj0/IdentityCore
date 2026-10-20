# IdentityCore Provider Conformance

This directory publishes two executable suites. The original five-case `run.py`
suite uses an isolated historical fixture envelope. The packaged SDKs implement
the current normal `/invoke` contract, exercised by `assurance.py` below.

The original Provider Contract v1 fixture suite It lets a
provider author verify the minimum synchronous HTTP boundary locally before requesting
integration or production review.

## Run locally

Start the provider in a dedicated conformance mode, then run:

```bash
python provider-sdk/conformance/run.py \
  --url http://127.0.0.1:8080 \
  --key-id conformance-key \
  --secret disposable-conformance-secret
```

Use a disposable conformance key and sandbox-only process. Do not pass a production
credential. The runner prints only case names and bounded failure reasons; it never prints
the secret, requests, responses, evidence, or subject data.

The provider must expose `POST /identitycore/conformance` while conformance mode is
enabled. It must disable that route in production. Requests use the Provider Signing v1
headers and the test-only `X-IC-Conformance-Case` header. Every non-timeout response must
be JSON, no larger than 1 MiB, signed with the same conformance key, and bound to the
request nonce.

## Required cases

| Case | Expected provider behavior |
| --- | --- |
| `success` | Return HTTP 200 and a signed Contract v1 completed result with the same invocation ID. |
| `malformed` | Reject signed malformed JSON with HTTP 400/422 and `invalid_request`. |
| `replay` | Accept the first signed request, then reject the identical nonce with HTTP 409 and `replay_rejected`. |
| `version_negotiation` | Reject Contract `999` with HTTP 400/422, `unsupported_contract_version`, and `supported_contract_versions: ["1"]`. |
| `timeout` | Delay longer than the runner deadline so the client observes a real transport timeout. |

Fixture rejections are non-retryable. The timeout case verifies transport behavior rather
than an error response because a timed-out call may still finish at the provider. The
fixed request bodies contain no personal data, documents, biometrics, storage references,
credentials, or real tenant identifiers.

## Provider-side checklist

1. Verify the HMAC signature against the exact body bytes before parsing JSON.
2. Enforce the five-minute timestamp tolerance and atomically claim a stable provider/direction identity and nonce across key rotations; exclude the rotating key ID.
3. Preserve the nonce and invocation ID when signing the response.
4. Reject unsupported contract versions before capability execution.
5. Keep conformance behavior isolated from normal endpoints and production configuration.
6. Delete the disposable key and stop the local server after the run.

The suite proves protocol compatibility only. Passing it is not provider certification,
a security assessment, a model evaluation, or approval for production data.

The disposable conformance secret is a direct message-signing key for the isolated conformance endpoint. Normal configured `hmac_v1` integrations derive that key from the encrypted environment API credential as specified in [Provider message signing](../../docs/architecture/provider-signing.md). Verify exact wire bytes in both modes.


## Packaged SDK HTTP and worker assurance suite

`assurance.py` exercises the actual SDK runtime through real loopback HTTP and an
isolated stdin driver. It checks all 17 `provider-assurance/v1` protocol/worker
cases, including signed callbacks and cancellation/deletion fencing. The driver
controls only a synthetic clock, worker and input fixture. Never expose these
controls on a provider deployment. No production credential is accepted or needed.

```sh
python provider-sdk/conformance/assurance.py --sdk python \
  --driver "python provider-sdk/conformance/harness/python.py" \
  --artifact /tmp/provider-python-assurance.json
python provider-sdk/conformance/assurance.py --sdk javascript \
  --driver "node provider-sdk/conformance/harness/javascript.mjs" \
  --artifact /tmp/provider-javascript-assurance.json
mvn -f provider-sdk/java/pom.xml test package dependency:build-classpath \
  -Dmdep.outputFile=target/provider-classpath.txt
python provider-sdk/conformance/assurance.py --sdk java \
  --driver "java -cp provider-sdk/java/target/test-classes:provider-sdk/java/target/classes:$(cat provider-sdk/java/target/provider-classpath.txt) io.identitycore.provider.ConformanceHarness" \
  --artifact /tmp/provider-java-assurance.json
dotnet build provider-sdk/dotnet/tests/IdentityCore.Provider.Tests/IdentityCore.Provider.Tests.csproj
python provider-sdk/conformance/assurance.py --sdk dotnet \
  --driver "dotnet provider-sdk/dotnet/tests/IdentityCore.Provider.Tests/bin/Debug/net8.0/IdentityCore.Provider.Tests.dll harness" \
  --artifact /tmp/provider-dotnet-assurance.json
```

Install the Python Provider SDK dependencies before running the common runner.
Each artifact identifies the SDK, SDK source digest, runner digest, suite, transport
and case outcomes, and explicitly
sets `deployment_assurance: false`. Stdout prints its SHA-256; no payloads, tokens,
secrets or exception data are included. CI retains these synthetic artifacts.
Django additionally tests its actual signed transport against the Python package
over verified TLS. Package-native tests verify durable state and replay protection
across separate processes, plus stale worker fencing and encryption.

These artifacts cannot stand in for an actual configuration-scoped deployment
report or independent assurance. Before proposing a certification, exercise the
actual configured deployment, retain its evidence and independent assessment
references, and obtain the separate maker/checker approval described in the
[provider operation runbook](../../docs/operations/provider-operations.md).
