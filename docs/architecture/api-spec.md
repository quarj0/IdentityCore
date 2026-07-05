# API Specification

## IdentityCore

**Version:** 1.0

---

## Purpose

This document defines the API design for IdentityCore Version 1.0.

IdentityCore exposes REST APIs for external integrations and GraphQL APIs for internal dashboards.

The API must be secure, tenant-aware, versioned, auditable, and predictable.

---

## API Strategy

IdentityCore uses two API styles:

```text
REST API     → External integrations, SDKs, file uploads, webhooks
GraphQL API  → Internal admin and organization dashboards
```

REST is the primary public API.

GraphQL is not intended for public third-party integrations in Version 1.0.

---

## Base URL

Production:

```text
https://api.identitycore.com/api/v1
```

Development:

```text
http://localhost:8000/api/v1
```

AI service internal URL:

```text
http://fastapi-ai:8001/v1
```

The AI service must not be exposed publicly in Version 1.0.

---

## Authentication

## Dashboard Authentication

Used by Platform Users.

Supported methods:

```text
Email/password
MFA
Session authentication or JWT
```

---

## Public REST API Authentication

Used by API Clients.

Required headers:

```http
Authorization: Bearer <api_secret>
X-Client-Id: <client_id>
X-Request-Id: <unique_request_id>
```

Optional but recommended:

```http
X-Signature: <request_signature>
X-Timestamp: <unix_timestamp>
```

---

## API Key Rules

- API secrets must never be stored in plain .
- API keys must be scoped.
- API key usage must be audited.
- API keys may be restricted by IP.
- API keys may be revoked.
- API keys may have rate limits.

---

## API Versioning

All public REST APIs must be versioned.

```text
/api/v1/...
```

Breaking changes require a new version.

Non-breaking changes may be added to the current version.

---

## Common Response Format

## Success Response

```json
{
  "success": true,
  "data": {},
  "request_id": "req_01JABC..."
}
```

## Error Response

```json
{
  "success": false,
  "error": {
    "code": "validation_error",
    "message": "The request contains invalid data.",
    "details": {}
  },
  "request_id": "req_01JABC..."
}
```

---

## Common Error Codes

```text
authentication_failed
permission_denied
tenant_not_found
resource_not_found
validation_error
rate_limit_exceeded
verification_expired
verification_cancelled
consent_required
document_required
selfie_required
liveness_failed
face_match_failed
manual_review_required
provider_unavailable
webhook_delivery_failed
internal_error
```

---

## Pagination

List endpoints must support pagination.

Request:

```http
GET /verifications?page=1&page_size=20
```

Response:

```json
{
  "success": true,
  "data": {
    "results": [],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total": 100,
      "total_pages": 5
    }
  },
  "request_id": "req_01JABC..."
}
```

Implementation note:

- When the verification subject email is present, the current Django implementation queues an email notification containing the verification link.

---

## Filtering and Sorting

List endpoints should support filtering.

Example:

```http
GET /verifications?status=verified&created_from=2026-01-01&created_to=2026-01-31
```

Sorting:

```http
GET /verifications?sort=-created_at
```

---

## Public REST API

---

## Health

## GET /api/v1/health

Checks API availability.

Response:

```json
{
  "success": true,
  "data": {
    "status": "ok",
    "service": "django",
    "version": "1.0.0"
  },
  "request_id": "req_01JABC..."
}
```

---

## Platform User Authentication

## POST /auth/login

Authenticates a Platform User with email and password.

Response:

```json
{
  "success": true,
  "data": {
    "tokens": {
      "access": "jwt-access-token",
      "refresh": "jwt-refresh-token"
    },
    "user": {
      "public_id": "usr_01JABC...",
      "email": "kwame@example.com",
      "tenant_public_id": "ten_01JABC...",
      "is_platform_admin": false,
      "mfa_enabled": false,
      "roles": ["Organization Administrator"]
    }
  },
  "request_id": "req_01JABC..."
}
```

## POST /auth/refresh

Refreshes a Platform User access token.

## GET /auth/me

Returns the currently authenticated Platform User and tenant context.

---

## Document Types

## GET /document-types

Returns supported generic document types.

Response:

```json
{
  "success": true,
  "data": [
    {
      "code": "national_id",
      "name": "National ID"
    },
    {
      "code": "passport",
      "name": "Passport"
    },
    {
      "code": "driver_license",
      "name": "Driver License"
    }
  ],
  "request_id": "req_01JABC..."
}
```

---

## Country Profiles

## GET /country-profiles

Returns supported country profiles.

Response:

```json
{
  "success": true,
  "data": [
    {
      "code": "GH",
      "name": "Ghana",
      "supported_document_types": [
        {
          "document_type": "national_id",
          "local_name": "Ghana Card"
        },
        {
          "document_type": "health_id",
          "local_name": "NHIS Card"
        }
      ]
    }
  ],
  "request_id": "req_01JABC..."
}
```

---

## Verifications

## POST /verifications

Creates a Verification.

Required scope:

```text
verifications:create
```

Request:

```json
{
  "external_reference": "customer_12345",
  "purpose": "Customer onboarding verification",
  "verification_subject": {
    "full_name": "Kwame Mensah",
    "email": "kwame@example.com",
    "phone_number": "+233500000000"
  },
  "policy_id": "pol_01JABC...",
  "redirect_url": "https://example.com/verification-complete",
  "metadata": {
    "source": "mobile_app"
  }
}
```

Response:

```json
{
  "success": true,
  "data": {
    "id": "ver_01JABC...",
    "status": "pending_consent",
    "verification_url": "https://verify.identitycore.com/session/ses_01JABC...",
    "session_id": "ses_01JABC...",
    "expires_at": "2026-07-05T12:00:00Z"
  },
  "request_id": "req_01JABC..."
}
```

Business rules:

- Creates a Verification.
- Creates or links a Verification Subject.
- Creates a Verification Session.
- Requires an API client with the `verifications:create` scope.
- The current bootstrap implementation stores the requested `policy_id` as a public identifier reference and keeps `policy_snapshot_json` as a placeholder until verification policies are wired in.
- Expiry is enforced asynchronously by background jobs; once `expires_at` passes, the Verification and any active session may transition to `expired` without another API call.
- Sends webhook event `verification.created`.

---

## GET /verifications

Lists verifications for the authenticated tenant.

Required scope:

```text
verifications:read
```

Query parameters:

```text
status
external_reference
created_from
created_to
page
page_size
sort
```

Response:

```json
{
  "success": true,
  "data": {
    "results": [
      {
        "id": "ver_01JABC...",
        "status": "verified",
        "external_reference": "customer_12345",
        "created_at": "2026-07-04T10:00:00Z",
        "completed_at": "2026-07-04T10:03:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total": 1,
      "total_pages": 1
    }
  },
  "request_id": "req_01JABC..."
}
```

---

## GET /verifications/{verification_id}

Retrieves verification details.

Required scope:

```text
verifications:read
```

Response:

```json
{
  "success": true,
  "data": {
    "id": "ver_01JABC...",
    "status": "verified",
    "purpose": "Customer onboarding verification",
    "external_reference": "customer_12345",
    "verification_subject": {
      "id": "sub_01JABC...",
      "full_name": "Kwame Mensah"
    },
    "checks": {
      "document": {
        "status": "processed"
      },
      "liveness": {
        "status": "passed",
        "score": 0.94
      },
      "face_match": {
        "status": "matched",
        "score": 0.96
      }
    },
    "risk_assessment": {
      "id": "rsk_01JABC...",
      "risk_level": "low",
      "risk_score": 14.0,
      "recommendation": "approve"
    },
    "decision": {
      "decision": "verified",
      "decision_type": "automatic",
      "decided_at": "2026-07-04T10:03:00Z"
    },
    "created_at": "2026-07-04T10:00:00Z",
    "completed_at": "2026-07-04T10:03:00Z"
  },
  "request_id": "req_01JABC..."
}
```

Sensitive data must be minimized.

Implementation note:

- The current Django bootstrap creates provider-check records for liveness, face match, and risk evaluation.
- Until external AI/provider integrations are connected, inconclusive bootstrap evidence is automatically routed into `manual_review_required` with a persisted automatic decision and risk assessment.

---

## POST /verifications/{verification_id}/cancel

Cancels a Verification.

Required scope:

```text
verifications:create
```

Request:

```json
{
  "reason": "User abandoned onboarding"
}
```

Response:

```json
{
  "success": true,
  "data": {
    "id": "ver_01JABC...",
    "status": "cancelled"
  },
  "request_id": "req_01JABC..."
}
```

---

## POST /verifications/{verification_id}/resend-link

Resends the Verification Session link.

Request:

```json
{
  "channel": "email"
}
```

Response:

```json
{
  "success": true,
  "data": {
    "sent": true
  },
  "request_id": "req_01JABC..."
}
```

---

## Verification Session API

These endpoints are used by the Verification Portal.

They are not authenticated by API keys. They use secure session tokens.

Required header:

```http
Authorization: Bearer <session_token>
```

---

## GET /sessions/{session_id}

Gets session information.

Response:

```json
{
  "success": true,
  "data": {
    "session_id": "ses_01JABC...",
    "verification_id": "ver_01JABC...",
    "status": "active",
    "organization": {
      "name": "Example Bank",
      "logo_url": "https://..."
    },
    "purpose": "Customer onboarding verification",
    "required_steps": [
      "consent",
      "document_capture",
      "selfie_capture",
      "liveness_check"
    ],
    "expires_at": "2026-07-05T12:00:00Z"
  },
  "request_id": "req_01JABC..."
}
```

Implementation note:

- The current backend derives the session URL from `VERIFICATION_PORTAL_BASE_URL` and authenticates the subject by matching the session public ID plus bearer session token.

---

## POST /sessions/{session_id}/consent

Accepts consent.

Request:

```json
{
  "accepted": true
}
```

Response:

```json
{
  "success": true,
  "data": {
    "consent_record_id": "con_01JABC...",
    "next_step": "document_capture"
  },
  "request_id": "req_01JABC..."
}
```

Business rules:

- Accepting consent creates a Consent Record.
- Accepting consent advances the Verification to `in_progress`.
- If no active tenant consent template exists yet, the backend stores a generated consent text snapshot so the acceptance remains auditable during bootstrap.

---

## POST /sessions/{session_id}/documents

Uploads document metadata after file upload.

Request:

```json
{
  "document_type": "national_id",
  "country_code": "GH",
  "captures": [
    {
      "side": "front",
      "upload_id": "upl_01JABC..."
    },
    {
      "side": "back",
      "upload_id": "upl_01JABD..."
    }
  ]
}
```

Business rules:

- Consent must already be accepted for the Verification before document metadata can be submitted.
- The current bootstrap implementation stores `document_type` and `country_code` directly on the identity document record until dedicated document type and country profile tables are introduced.
- Each submitted capture side must be unique within the request.
- Each `upload_id` must refer to an issued temporary upload for the same verification session and is consumed when the corresponding `DocumentCapture` record is created.
- The current Django implementation queues asynchronous document OCR and document-quality processing after document submission while allowing the subject flow to continue.

Response:

```json
{
  "success": true,
  "data": {
    "identity_document_id": "doc_01JABC...",
    "status": "processing",
    "next_step": "selfie_capture"
  },
  "request_id": "req_01JABC..."
}
```

---

## POST /sessions/{session_id}/selfies

Submits selfie metadata after upload.

Request:

```json
{
  "capture_type": "image",
  "upload_id": "upl_01JABC..."
}
```

Business rules:

- Consent and document submission must already be complete before selfie metadata can be submitted.
- The provided `upload_id` must refer to an issued temporary upload for the same verification session and is consumed when the `SelfieCapture` record is created.
- Selfie submission currently creates a `SelfieCapture` record and advances the subject flow to `liveness_check`.

Response:

```json
{
  "success": true,
  "data": {
    "selfie_capture_id": "sel_01JABC...",
    "status": "processing",
    "next_step": "liveness_check"
  },
  "request_id": "req_01JABC..."
}
```

---

## POST /sessions/{session_id}/liveness

Submits liveness challenge result or media reference.

Request:

```json
{
  "liveness_type": "passive",
  "selfie_capture_id": "sel_01JABC..."
}
```

Business rules:

- The referenced selfie capture must belong to the current verification session.
- The current Django implementation records a `LivenessCheck` immediately and returns `status: processing` while queued background AI processing completes liveness and face-match evaluation asynchronously.

Response:

```json
{
  "success": true,
  "data": {
    "liveness_check_id": "liv_01JABC...",
    "status": "processing"
  },
  "request_id": "req_01JABC..."
}
```

---

## GET /sessions/{session_id}/status

Returns subject-facing verification status.

Response:

```json
{
  "success": true,
  "data": {
    "verification_id": "ver_01JABC...",
    "status": "processing",
    "current_step": "processing",
    "message": "Your verification is being processed."
  },
  "request_id": "req_01JABC..."
}
```

Business rules:

- The response is a subject-facing summary and must not expose internal-only processing details.
- The current bootstrap implementation maps internal verification statuses into a simplified `current_step` and `message` for the verification portal.

---

## Upload API

For security and scalability, media uploads should use signed upload URLs.

---

## POST /uploads

Creates a signed upload URL.

Current bootstrap authentication:

```http
Authorization: Bearer <session_token>
X-Session-Id: <session_id>
```

Request:

```json
{
  "purpose": "document_capture",
  "mime_type": "image/jpeg",
  "file_size_bytes": 2500000
}
```

Response:

```json
{
  "success": true,
  "data": {
    "upload_id": "upl_01JABC...",
    "upload_url": "https://storage-provider.com/signed-upload-url",
    "expires_at": "2026-07-04T10:10:00Z"
  },
  "request_id": "req_01JABC..."
}
```

Rules:

- Upload URLs must expire.
- Uploads must be scanned or validated before processing.
- Public permanent URLs must not be used for sensitive media.

Implementation note:

- The current Django implementation exposes upload initialization as a verification-session-scoped endpoint using `Authorization: Bearer <session_token>` plus `X-Session-Id`.
- Upload initialization now persists a tenant-scoped `Upload` record tied to the verification session, and later document/selfie submission must reference that issued `upload_id`.
- Returned upload URLs remain placeholder signed-style URLs derived from `UPLOAD_URL_BASE` until the object storage integration is connected.

---

## Policies API

## GET /policies

Lists verification policies.

Authentication:

- Platform user JWT required.

Response:

```json
{
  "success": true,
  "data": [
    {
      "id": "pol_01JABC...",
      "name": "Default Verification",
      "version": 1,
      "status": "active"
    }
  ],
  "request_id": "req_01JABC..."
}
```

---

## POST /policies

Creates a verification policy.

Authentication:

- Platform user JWT required.

Request:

```json
{
  "name": "Default Verification",
  "required_document_types": ["national_id", "passport"],
  "required_liveness_level": "passive",
  "face_match_threshold": 0.85,
  "manual_review_threshold": 0.65,
  "verification_expiry_minutes": 1440,
  "media_retention_days": 30,
  "metadata_retention_days": 365
}
```

Response:

```json
{
  "success": true,
  "data": {
    "id": "pol_01JABC...",
    "name": "Default Verification",
    "version": 1,
    "status": "draft"
  },
  "request_id": "req_01JABC..."
}
```

Business rules:

- Policies are tenant-scoped.
- Creating a policy with an existing name creates a new version for that tenant instead of overwriting the previous record.
- New policies are created in `draft` status by default.

---

## Manual Review API

## GET /manual-reviews

Lists verifications requiring manual review.

Authentication:

- Platform user JWT required.

Response:

```json
{
  "success": true,
  "data": {
    "results": [
      {
        "verification_id": "ver_01JABC...",
        "status": "manual_review_required",
        "risk_level": "medium",
        "created_at": "2026-07-04T10:00:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total": 1,
      "total_pages": 1
    }
  },
  "request_id": "req_01JABC..."
}
```

---

## POST /manual-reviews/{verification_id}/decision

Records a manual decision.

Authentication:

- Platform user JWT required.

Request:

```json
{
  "decision": "verified",
  "reason_code": "evidence_confirmed",
  "reason_detail": "Document and selfie match after manual review."
}
```

Response:

```json
{
  "success": true,
  "data": {
    "verification_id": "ver_01JABC...",
    "decision": "verified",
    "decision_type": "manual",
    "decided_at": "2026-07-04T12:00:00Z"
  },
  "request_id": "req_01JABC..."
}
```

Business rules:

- Manual review actions are tenant-scoped.
- Recording a manual decision creates or updates the persisted verification decision record and updates the verification status.
- Manual review lists should reflect the persisted verification risk assessment when one exists.
- Verification decision transitions may queue subject-facing status notifications and reviewer notifications when manual review is required.

---

## API Clients API

## GET /api-clients

Lists API clients for the tenant.

Requires Platform User authentication and tenant context.

## POST /api-clients

Creates an API client.

Request:

```json
{
  "name": "Production Backend",
  "scopes": ["verifications:create", "verifications:read"],

  "allowed_networks": ["197.251.0.15/32", "197.251.0.0/24", "2001:db8::/32"],
  "rate_limit_per_minute": 100
}
```

Response:

```json
{
  "success": true,
  "data": {
    "client_id": "cli_01JABC...",
    "client_secret": "secret_shown_once",
    "scopes": ["verifications:create", "verifications:read"]
  },
  "request_id": "req_01JABC..."
}
```

Rule:

`client_secret` is shown only once.

Implementation note:

- `client_id` is a prefixed public identifier such as `cli_01J...`.
- Raw client secrets are never stored.
- API client requests authenticate with `Authorization: Bearer <api_secret>` and `X-Client-Id: <client_id>`.

---

## Webhooks API

## GET /webhook-endpoints

Lists webhook endpoints.

Authentication:

- Platform user JWT required.

## POST /webhook-endpoints

Creates webhook endpoint.

Authentication:

- Platform user JWT required.

Request:

```json
{
  "url": "https://example.com/webhooks/identitycore",
  "events": [
    "verification.verified",
    "verification.rejected",
    "verification.manual_review_required"
  ]
}
```

Response:

```json
{
  "success": true,
  "data": {
    "id": "wh_01JABC...",
    "secret": "webhook_secret_shown_once",
    "status": "active"
  },
  "request_id": "req_01JABC..."
}
```

Business rules:

- Webhook endpoints are tenant-scoped.
- The raw webhook secret is shown only once and is never stored in plain text.

---

## POST /webhook-endpoints/{webhook_id}/test

Sends a test webhook.

Authentication:

- Platform user JWT required.

Response:

```json
{
  "success": true,
  "data": {
    "queued": true
  },
  "request_id": "req_01JABC..."
}
```

Implementation note:

- The current Django implementation queues webhook events for later delivery, records test sends as queued `webhook.test` events, signs outbound requests, and records delivery attempts.
- Failed webhook deliveries are retried with exponential backoff until the configured maximum attempt count is reached.

---

## Webhook Event Format

Webhook payload:

```json
{
  "id": "evt_01JABC...",
  "type": "verification.verified",
  "created_at": "2026-07-04T10:03:00Z",
  "data": {
    "verification_id": "ver_01JABC...",
    "external_reference": "customer_12345",
    "status": "verified"
  }
}
```

Webhook headers:

```http
X-IdentityCore-Event-Id: evt_01JABC...
X-IdentityCore-Event-Type: verification.verified
X-IdentityCore-Signature: sha256=...
X-IdentityCore-Timestamp: 1783159380
```

Webhook events:

```text
verification.created
verification.consent_accepted
verification.document_uploaded
verification.selfie_uploaded
verification.processing
verification.manual_review_required
verification.verified
verification.rejected
verification.expired
verification.cancelled
```

---

## Audit API

## GET /audit-events

Lists audit events.

Authentication:

- Platform user JWT required.

Query parameters:

```text
actor_type
action
target_type
target_id
created_from
created_to
page
page_size
```

Response:

```json
{
  "success": true,
  "data": {
    "results": [
      {
        "id": "aud_01JABC...",
        "actor_type": "api_client",
        "action": "verification.created",
        "target_type": "verification",
        "target_id": "ver_01JABC...",
        "created_at": "2026-07-04T10:00:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total": 1,
      "total_pages": 1
    }
  },
  "request_id": "req_01JABC..."
}
```

Business rules:

- Audit event listing is tenant-scoped.
- Audit events are append-only security records and must not expose raw sensitive payloads.

---

## Internal AI Service API

The AI service is internal only.

---

## POST /v1/face/compare

Compares two face images or templates.

Request:

```json
{
  "verification_id": "ver_01JABC...",
  "selfie_storage_key": "media/selfies/...",
  "document_storage_key": "media/documents/...",
  "threshold": 0.85
}
```

Response:

```json
{
  "status": "completed",
  "match_score": 0.96,
  "confidence_level": "high",
  "matched": true,
  "model_name": "insightface",
  "model_version": "v1"
}
```

---

## POST /v1/liveness/check

Runs liveness detection.

Request:

```json
{
  "verification_id": "ver_01JABC...",
  "selfie_storage_key": "media/selfies/...",
  "liveness_type": "passive"
}
```

Response:

```json
{
  "status": "completed",
  "score": 0.94,
  "confidence_level": "high",
  "passed": true,
  "model_name": "liveness-model",
  "model_version": "v1"
}
```

---

## POST /v1/document/ocr

Runs OCR on document capture.

Request:

```json
{
  "verification_id": "ver_01JABC...",
  "document_storage_key": "media/documents/...",
  "document_type": "national_id",
  "country_code": "GH"
}
```

Response:

```json
{
  "status": "completed",
  "confidence_score": 0.91,
  "extracted_fields": {
    "full_name": "Kwame Mensah",
    "date_of_birth": "1998-01-01",
    "document_number": "masked_or_hashed"
  },
  "model_name": "paddleocr",
  "model_version": "v1"
}
```

---

## POST /v1/document/quality

Checks document image quality.

Request:

```json
{
  "verification_id": "ver_01JABC...",
  "document_storage_key": "media/documents/..."
}
```

Response:

```json
{
  "status": "completed",
  "quality_score": 0.88,
  "issues": []
}
```

---

## GraphQL API

GraphQL powers dashboards.

Endpoint:

```text
/api/graphql
```

Example query:

```graphql
query VerificationList {
  verifications(status: "manual_review_required") {
    id
    status
    createdAt
    riskAssessment {
      riskLevel
      riskScore
    }
    verificationSubject {
      fullName
    }
  }
}
```

Example mutation:

```graphql
mutation ManualDecision {
  recordManualDecision(
    verificationId: "ver_01JABC..."
    decision: "verified"
    reasonCode: "evidence_confirmed"
  ) {
    verificationId
    decision
    decidedAt
  }
}
```

GraphQL rules:

- Must enforce tenant context.
- Must enforce permissions.
- Must avoid exposing sensitive fields by default.
- Must use query depth limits.
- Must use rate limiting.
- Must log sensitive queries.

---

## Rate Limiting

Default limits:

```text
API clients: 100 requests/minute
Verification sessions: 30 requests/minute
Dashboard users: 300 requests/minute
Webhook retries: controlled by worker queue
```

Limits may vary by plan and tenant.

---

## Idempotency

Critical POST requests should support idempotency.

Header:

```http
Idempotency-Key: unique-key-from-client
```

Required for:

```text
POST /verifications
POST /webhook-endpoints
POST /api-clients
POST /manual-reviews/{verification_id}/decision
```

Rules:

- Same key with same payload returns same result.
- Same key with different payload returns error.
- Idempotency records expire after a configured period.

---

## Security Requirements

All APIs must enforce:

- Authentication
- Authorization
- Tenant isolation
- Input validation
- Rate limiting
- Audit logging
- Sensitive data masking
- Secure error handling

Public APIs must never expose:

- Raw biometric templates
- Raw document numbers unless required
- Internal database IDs
- Provider secrets
- Raw provider credentials
- Full object storage URLs without expiration

---

## Version 1.0 API Scope

Version 1.0 includes:

- Health
- Document Types
- Country Profiles
- Verifications
- Verification Sessions
- Uploads
- Policies
- Manual Reviews
- API Clients
- Webhooks
- Audit Events
- Internal AI APIs
- Dashboard GraphQL

Version 1.0 excludes:

- Government identity lookup APIs
- Criminal record APIs
- Immigration APIs
- Fingerprint APIs
- Iris APIs
- Digital wallet APIs
- Public GraphQL API
- Mobile-specific APIs
- Payment APIs

---

## Final API Principle

The API should make identity verification simple for organizations while keeping privacy, security, auditability, and tenant isolation strict by default.

External clients should not need to understand IdentityCore's internal architecture to create verifications, receive results, or integrate securely.
