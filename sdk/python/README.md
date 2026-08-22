# IdentityCore Python SDK

Typed, server-side Python client for IdentityCore. Requires Python 3.9+ and has no runtime dependencies.

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
