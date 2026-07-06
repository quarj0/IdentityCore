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
3. Fill `api_client_id` and `api_client_secret` from an existing API client.
4. Run `Create Verification`.
5. Set `session_token` manually from a created verification session if you want to test the hosted-session endpoints.
6. Run upload/session/manual-review/GraphQL requests as needed.

## Notes

- The collection stores some IDs and tokens automatically from responses.
- Session-token generation is intentionally secure, so the raw verification session token is not generally recoverable after creation unless you captured it at creation time.
- For GraphQL, the endpoint is `POST /api/graphql`.
