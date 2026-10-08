# Postman Assets

Import these two files into Postman:

- `IdentityCore.postman_collection.json`
- `IdentityCore.local.postman_environment.json`

## What is included

- REST auth requests for dashboard users
- REST API-client verification flow requests
- Session-authenticated upload creation and multipart transfer requests
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
13. Run `Session Detail`, then `Accept Consent` with the four exported notice fields.
14. For the collection’s GH national ID example, select front and back JPEGs and set `document_file_size_bytes` and `document_back_file_size_bytes` to their exact byte counts. Run each upload creation followed by its multipart transfer, selecting the same file in the `file` field. Both use `session_token` plus `X-Session-Id` and must finish before `Submit Document`.
15. Wait until `Session Status` reports the selfie step. Set `selfie_file_size_bytes`, create and transfer the selfie JPEG, then run `Submit Selfie`.
16. `Submit Liveness` is the passive policy example. Run it only when `Session Detail` reports passive liveness; an active policy requires the hosted portal’s fresh challenge and live camera recording. The optional video upload pair alone does not satisfy an active challenge.
17. Continue with manual-review or GraphQL requests as needed.

## Notes

- The collection stores some IDs and tokens automatically from responses.
- Session-token generation is intentionally secure, so the raw verification session token is not generally recoverable after creation unless you captured it at creation time.
- For GraphQL, the endpoint is `POST /api/graphql`.
- The onboarding registration mutation returns a `debugEmailVerificationUrl` only when Django is running with `DEBUG=1`; production environments should rely on the delivered email instead.

Upload transfers validate MIME type, content and the declared byte count, bind evidence to the authenticated session, and return an uploaded resource. Upload creation alone does not make an upload eligible for document or selfie submission. Postman must supply its own multipart boundary, so transfer requests intentionally omit an explicit Content-Type header.
