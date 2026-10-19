# IdentityCore Python SDK

Typed, server-side Python client for IdentityCore. Requires Python 3.12+ and has no runtime dependencies.

> Never place an API client secret in browser, desktop, or mobile application code.

## Quick start

```python
from identitycore import IdentityCoreClient

client = IdentityCoreClient(
    api_origin="https://api.identitycore.com",
    client_id="cli_...",
    client_secret="...",
)

policy = client.policies.list()[0]
verification = client.verifications.create(
    purpose="Customer onboarding",
    policy_id=policy["id"],
    project_id="prj_...",
    verification_subject={"full_name": "Kwame Mensah", "email": "kwame@example.com"},
    external_reference="customer_123",
    redirect_url="https://app.example.com/identity/complete",
    idempotency_key="customer_123-onboarding-v1",
)
result = client.verifications.result(verification["id"])
print(verification["verification_url"])
```

An optional `project_id` must identify an active project in the same workspace and match the selected policy’s project. Omit it to use the policy’s project. Unknown or mismatched IDs are rejected before creating the verification.

GET requests retry transient failures automatically. Verification creation is idempotent and safely retried; cancellation and link resend are not retried automatically.

## CLI

Install the SDK and save a server-side API client configuration:

```sh
pip install identitycore
identitycore login --api-origin https://api.identitycore.com \
  --client-id cli_...
identitycore policies list
identitycore verifications create --purpose "Customer onboarding" \
  --policy-id pol_... --full-name "Kwame Mensah" --email kwame@example.com
```

The configuration file is written with owner-only permissions. Environment
variables (`IDENTITYCORE_API_ORIGIN`, `IDENTITYCORE_CLIENT_ID`, and
`IDENTITYCORE_CLIENT_SECRET`) can be used in CI instead of `login`.

### Shell autocomplete

Generate a dependency-free completion script once, then start a new shell. Tab
completion includes commands, nested commands, and their options.

```sh
# Bash
identitycore completion bash >> ~/.bashrc

# Zsh
identitycore completion zsh >> ~/.zshrc

# Fish
mkdir -p ~/.config/fish/completions
identitycore completion fish > ~/.config/fish/completions/identitycore.fish
```

For a temporary setup in Bash or Zsh, use
`eval "$(identitycore completion bash)"` or
`eval "$(identitycore completion zsh)"`, respectively.

## Pagination and webhooks

```python
from identitycore import verify_webhook_signature

for verification in client.verifications.iter(status="verified"):
    print(verification["id"])

valid = verify_webhook_signature(
    raw_request_body,
    signature=request.headers["X-IdentityCore-Signature-V1"],
    timestamp=request.headers["X-IdentityCore-Timestamp"],
    event_id=request.headers["X-IdentityCore-Event-Id"],
    signing_keys=[current_webhook_secret, previous_webhook_secret],
    claim_event_id=claim_processed_event_id,
)
```

Always verify the unmodified webhook body before parsing JSON. The default timestamp tolerance is five minutes. `claim_processed_event_id` must atomically insert the event ID only if it does not exist and return whether the claim succeeded. During rotation, supply both secrets only until the API-provided overlap expiry; IdentityCore emits v1 signatures for both during that window. The original `X-IdentityCore-Signature` header remains available for staged migration of legacy receivers.

Required scopes are `policies:read`, `verifications:create`, and `verifications:read` for their corresponding resources.

CLI options require their full names (for example, `--profile`); abbreviated long options are rejected so parsing stays consistent with shell completion.

## Creation date filters

List and cursor iteration accept inclusive `created_from`/`created_to` dates in
`YYYY-MM-DD` format (camelCase options in JavaScript, Java and .NET). The API uses
the deployment's configured time zone, rejects impossible dates and reversed
ranges with HTTP 400, and binds cursors to the unchanged filters. Iterators retain
both dates on every page. Existing calls without dates keep their behavior.

```python
for verification in client.verifications.iter(
    created_from="2026-01-01", created_to="2026-01-31"
):
    pass  # handle verification
```

Python 3.12 is the minimum supported version. Compatibility CI targets Python 3.12
and 3.14; Python 3.9–3.11 are no longer supported. The SDK has no runtime
dependencies. Backend/AI runtime versions are maintained separately and currently
require Python 3.12 or newer.
