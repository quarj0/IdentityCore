# IdentityCore Public API Postman Collection

Focused Postman assets for external API-client integrations.

Import:

- `IdentityCore Public API.postman_collection.json`
- `IdentityCore Public API.local.postman_environment.json`

Usage:

1. Set `api_client_id` and `api_client_secret`.
2. Set a unique `idempotency_key` for the verification create payload.
3. Run `Health`.
4. Run `List Active Policies`; the first policy ID is saved as `policy_id`.
5. Run `Create Verification`; IDs and hosted URL are saved into the environment.
6. Run detail, resend, cancel, or evidence-report requests as needed.

Reuse an idempotency key only to retry the exact same create payload. Change it when the payload changes.

Required scopes:

- `policies:read`
- `verifications:create`
- `verifications:read`
