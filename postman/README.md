# Postman Assets

Import these two files into Postman:

- `IdentityCore.postman_collection.json`
- `IdentityCore.local.postman_environment.json`

## What is included

- REST auth requests for dashboard users
- REST API-client verification flow requests
- Upload creation requests
- Verification session portal requests
- Manual review/admin requests
- GraphQL query and mutation examples
- GraphQL onboarding registration and approval flow examples

## Important auth modes

- Dashboard REST and GraphQL use:
  - `Authorization: Bearer <dashboard_access_token>`
- External API-client REST endpoints use:
  - `X-Client-Id: <api_client_id>`
  - `Authorization: Bearer <api_client_secret>`
- Verification session portal endpoints use:
  - `Authorization: Bearer <session_token>`
  - `session_id` is in the request URL

## Basic usage order

1. Import the collection and environment.
2. Run `REST - Dashboard Auth / Login`.
3. For organization onboarding GraphQL testing, start with `GraphQL - Onboarding / Register Organization Onboarding`.
4. In local `DEBUG`, that request stores `email_verification_debug_url` and `email_verification_token` automatically so you can run the email-verification mutation without a mailbox viewer.
5. Run `GraphQL - Onboarding / Verify Onboarding Email`.
6. The Tenant Administrator role is assigned only after that email-verification step succeeds.
7. Log in as the newly activated dashboard user if you want to continue the tenant-side onboarding requests.
8. Run `GraphQL - Onboarding / Platform Admin Login` before the final review mutation.
9. Production API key creation remains blocked until platform approval.
10. Fill `api_client_id` and `api_client_secret` from an existing API client.
11. Run `Create Verification`.
12. Set `session_token` manually from a created verification session if you want to test the hosted-session endpoints.
13. Run upload/session/manual-review/GraphQL requests as needed.

## Notes

- The collection stores some IDs and tokens automatically from responses.
- Session-token generation is intentionally secure, so the raw verification session token is not generally recoverable after creation unless you captured it at creation time.
- For GraphQL, the endpoint is `POST /api/graphql`.
- The onboarding registration mutation returns a `debugEmailVerificationUrl` only when Django is running with `DEBUG=1`; production environments should rely on the delivered email instead.
