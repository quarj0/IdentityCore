# IdentityCore Python SDK

Python client for IdentityCore public REST APIs.

## Install

```bash
pip install identitycore
```

During local development, install from this directory:

```bash
pip install -e sdk/python
```

## Quick start

```python
from identitycore import IdentityCoreClient

client = IdentityCoreClient(
    api_origin="https://api.identitycore.com",
    client_id="cli_...",
    client_secret="...",
)

policies = client.policies.list()

verification = client.verifications.create(
    purpose="Customer onboarding",
    policy_id=policies[0]["id"],
    verification_subject={
        "full_name": "Kwame Mensah",
        "email": "kwame@example.com",
    },
    external_reference="customer_123",
)

print(verification["verification_url"])
```

## Required scopes

- `policies:read` for policy/template list and detail.
- `verifications:create` for verification creation, cancellation, and link resend.
- `verifications:read` for verification list, detail, and evidence report URLs.

API-client-created verifications must include an active `policy_id`.
