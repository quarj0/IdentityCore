# IdentityCore Public API Postman Collection

Focused Postman assets for external API-client integrations.

Import:

- `IdentityCore Public API.postman_collection.json`
- `IdentityCore Public API.local.postman_environment.json`

Usage:

1. Set `api_client_id` and `api_client_secret`.
2. Run `Health`.
3. Run `List Active Policies`; the first policy ID is saved as `policy_id`.
4. Run `Create Verification`; IDs and hosted URL are saved into the environment.
5. Run detail, resend, cancel, or evidence-report requests as needed.

Required scopes:

- `policies:read`
- `verifications:create`
- `verifications:read`
