# Provider setup and environment promotion

Organization administrators use **Providers** in the dashboard. Existing administrator roles receive `manage_providers` and `approve_provider_promotion`; new onboarding administrators receive both. Delegate approval to a second authorized person. Tenant users without these permissions cannot configure, test or activate connections. Platform defaults are visible through the provider catalogue but cannot be modified through tenant setup.

1. Declare capability coverage, processing regions, processor identity, retention and transfer safeguards. Declarations must match Provider Contract v1. The deployment privacy owner validates agreements and residency before use.
2. Request a sandbox configuration with an HTTPS endpoint and a separately entered credential. Credentials are encrypted, never echoed and never copied into a promotion. The dashboard clears the credential after successful submission.
3. Test the exact draft version. A POST to its configured endpoint sends `operation: connection_test`, contract version 1, environment, a random challenge, and capability names. The provider must return `status: completed`, the same challenge, version and capability set. No subject/media data is sent. The secure transport pins public DNS addresses, verifies TLS, allows only explicit hostnames, rejects redirects/private addresses and bounds timeout/response size.
4. Activate within 15 minutes of a successful test, then publish an environment-scoped capability route. Coverage restrictions match the declaration; unknown capability/coverage is rejected. Failures enter the route's controlled fallback/review path.
5. To promote, choose an active sandbox source and separately supply the production endpoint/credential. Production requires an approved organization and a credential different from sandbox. The immutable proposal contains a non-secret configuration diff and pinned manifest. Test the production endpoint again, then have a **different** user with approval permission activate it.

Configuration changes create a new version and require a new test. Manifest changes invalidate pending tests and runtime configuration snapshots. Activation retires the prior version in the same environment atomically; sandbox remains independent. Connection outcomes, requests, activation and assignment are recorded in the tenant audit chain without payloads or credentials.

Internal dashboard endpoints are under `/api/v1/providers/`: POST `setup/`, GET/POST `<provider_id>/configurations/`, and POST `configurations/<configuration_id>/{test,activate,assign}/`. These are control-plane APIs, not the public partner SDK surface. POST configuration accepts `environment`, `configuration` (`endpoint_url`, `allowed_hosts`, `timeout_seconds`), `credentials` (`api_key`), and production `source_id`. Assignment accepts a declared `capability`, `countries`, and `document_types`.

Configured invocations POST contract version, capability, environment and the required capability inputs, with credentials only in Authorization. Responses must match the requested contract/capability. Select configuration from the verification project environment; there is no sandbox credential fallback. The endpoint operator must implement the existing capability input/output contract and authorized evidence reference handling. A passing connection probe checks reachability/authentication/contract declarations; production rollout also requires capability conformance and operational validation with synthetic evidence. Never install shared-storage credentials in browser configuration or provider responses.

## Scoped assurance and asynchronous completion

Public `/api/v1/providers/certifications` resources add scoped retained reports,
independent approval, expiry and revocation. These do not expose the internal
configuration/setup endpoints as public SDK operations. Async configurations require
`hmac_v1`, explicit `ic-provider-operations-v1` negotiation and current approved
assurance. See [provider operations](provider-operations.md) for report scope, all
17 required async cases, durable workers/callbacks and remote deletion acknowledgments.
