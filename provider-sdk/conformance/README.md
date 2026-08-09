# IdentityCore Provider Conformance

This directory publishes the executable Provider Contract v1 fixture suite. It lets a
provider author verify the minimum synchronous HTTP boundary locally before requesting
integration or production review.

## Run locally

Start the provider in a dedicated conformance mode, then run:

```bash
python provider-sdk/conformance/run.py \
  --url http://127.0.0.1:8080 \
  --key-id conformance-key
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
2. Enforce the five-minute timestamp tolerance and atomically claim the key-ID/nonce pair.
3. Preserve the nonce and invocation ID when signing the response.
4. Reject unsupported contract versions before capability execution.
5. Keep conformance behavior isolated from normal endpoints and production configuration.
6. Delete the disposable key and stop the local server after the run.

The suite proves protocol compatibility only. Passing it is not provider certification,
a security assessment, a model evaluation, or approval for production data.
