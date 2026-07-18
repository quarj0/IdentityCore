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
print(verification["verification_url"])
```

GET requests retry transient failures automatically. Mutating requests retry only when you provide an `idempotency_key`.

## Pagination and webhooks

```python
from identitycore import verify_webhook_signature

for verification in client.verifications.iter(status="verified"):
    print(verification["id"])

valid = verify_webhook_signature(
    raw_request_body,
    signature=request.headers["X-IdentityCore-Signature"],
    timestamp=request.headers["X-IdentityCore-Timestamp"],
    signing_key=webhook_signing_key,
)
```

Always verify the unmodified webhook body before parsing JSON. The default timestamp tolerance is five minutes.

Required scopes are `policies:read`, `verifications:create`, and `verifications:read` for their corresponding resources.

