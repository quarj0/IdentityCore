# API Specification

## IdentityCore

**Version:** 1.0

---

# Purpose

This document defines the API design for IdentityCore Version 1.0.

IdentityCore exposes REST APIs for external integrations and GraphQL APIs for internal dashboards.

The API must be secure, tenant-aware, versioned, auditable, and predictable.

---

# API Strategy

IdentityCore uses two API styles:

```
REST API     → External integrations, SDKs, file uploads, webhooks
GraphQL API  → Internal admin and organization dashboards
```

REST is the primary public API.

GraphQL is not intended for public third-party integrations in Version 1.0.

---

# Base URL

Production:

```
https://api.identitycore.com/api/v1
```

Development:

```
http://localhost:8000/api/v1
```

AI service internal URL:

```
http://fastapi-ai:8001/v1
```

The AI service must not be exposed publicly in Version 1.0.

---

# Authentication

## Dashboard Authentication

Used by Platform Users.

Supported methods:

```
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

# API Key Rules

- API secrets must never be stored in plain .
- API keys must be scoped.
- API key usage must be audited.
- API keys may be restricted by IP.
- API keys may be revoked.
- API keys may have rate limits.

---

# API Versioning

All public REST APIs must be versioned.

```
/api/v1/...
```

Breaking changes require a new version.

Non-breaking changes may be added to the current version.

---

# Common Response Format

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

# Common Error Codes

```
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

# Pagination

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

---

# Filtering and Sorting

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

# Public REST API

---

# Health

## GET /health

Checks API availability.

Response:

```json
{
  "success": true,
  "data": {
    "status": "ok",
    "version": "1.0.0"
  },
  "request_id": "req_01JABC..."
}
```

---

# Document Types

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

# Country Profiles

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

# Verifications

## POST /verifications

Creates a Verification.

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
    "verification_url": "https://verify.identitycore.com/session/vs_01JABC...",
    "expires_at": "2026-07-05T12:00:00Z"
  },
  "request_id": "req_01JABC..."
}
```

Business rules:

- Creates a Verification.
- Creates or links a Verification Subject.
- Creates a Verification Session.
- Sends webhook event `verification.created`.

---

## GET /verifications

Lists verifications for the authenticated tenant.

Query parameters:

```
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

---

## POST /verifications/{verification_id}/cancel

Cancels a Verification.

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

# Verification Session API

These endpoints are used by the Verification Portal.

They are not authenticated by API keys. They use secure session tokens.

---

## GET /sessions/{session_id}

Gets session information.

Response:

```json
{
  "success": true,
  "data": {
    "session_id": "vs_01JABC...",
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

---

# Upload API

For security and scalability, media uploads should use signed upload URLs.

---

## POST /uploads

Creates a signed upload URL.

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

---

# Policies API

## GET /policies

Lists verification policies.

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

---

# Manual Review API

## GET /manual-reviews

Lists verifications requiring manual review.

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

---

# API Clients API

## GET /api-clients

Lists API clients for the tenant.

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

---

# Webhooks API

## GET /webhook-endpoints

Lists webhook endpoints.

## POST /webhook-endpoints

Creates webhook endpoint.

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

---

## POST /webhook-endpoints/{webhook_id}/test

Sends a test webhook.

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

---

# Webhook Event Format

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
X-IdentityCore-Signature: sha256=...
X-IdentityCore-Timestamp: 1783159380
```

Webhook events:

```
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

# Audit API

## GET /audit-events

Lists audit events.

Query parameters:

```
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

---

# Internal AI Service API

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

# GraphQL API

GraphQL powers dashboards.

Endpoint:

```
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

# Rate Limiting

Default limits:

```
API clients: 100 requests/minute
Verification sessions: 30 requests/minute
Dashboard users: 300 requests/minute
Webhook retries: controlled by worker queue
```

Limits may vary by plan and tenant.

---

# Idempotency

Critical POST requests should support idempotency.

Header:

```http
Idempotency-Key: unique-key-from-client
```

Required for:

```
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

# Security Requirements

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

# Version 1.0 API Scope

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

# Final API Principle

The API should make identity verification simple for organizations while keeping privacy, security, auditability, and tenant isolation strict by default.

External clients should not need to understand IdentityCore's internal architecture to create verifications, receive results, or integrate securely.
