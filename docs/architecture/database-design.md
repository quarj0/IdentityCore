# Database Design

## IdentityCore

**Version:** 1.0

---

# Purpose

This document defines the initial database design for IdentityCore Version 1.0.

The database must support multi-tenancy, verification workflows, document capture, selfie capture, liveness checks, face matching, consent, verification decisions, audit logs, API clients, webhooks, provider checks, and configurable policies.

---

# Database Strategy

IdentityCore Version 1.0 will use PostgreSQL as the primary relational database.

The first version should use one primary database with strong tenant isolation through `tenant_id`.

Future versions may separate high-risk or high-volume data into dedicated databases, such as:

- Audit database
- Biometric metadata database
- Reporting database
- Provider integration database

---

# Core Design Rules

- Every tenant-owned table must include `tenant_id`.
- Every sensitive action must create an audit event.
- Raw media should not be stored directly in PostgreSQL.
- Raw media should be stored in encrypted object storage.
- PostgreSQL should store references, metadata, status, scores, and decisions.
- Country-specific document names must not be hardcoded.
- Sensitive fields should be encrypted where required.
- Soft deletes should be used for business records.
- Hard deletes should be reserved for retention cleanup and compliance workflows.

---

# Common Fields

Most tables should include:

```text
id
created_at
updated_at
deleted_at
```

Tenant-owned tables should include:

```text
tenant_id
```

Actor-tracked tables may include:

```text
created_by_id
updated_by_id
```

External-facing records should use public identifiers:

```text
public_id
```

Example:

```text
ver_01JABC...
org_01JABC...
ten_01JABC...
sub_01JABC...
```

Internal database IDs should not be exposed through public APIs.

---

# Entity Relationship Overview

```text
Organization
└── Tenant
    ├── PlatformUsers
    ├── Roles
    ├── Permissions
    ├── APIClients
    ├── VerificationPolicies
    ├── WebhookEndpoints
    └── Verifications
        ├── VerificationSubject
        ├── VerificationSession
        ├── ConsentRecord
        ├── IdentityDocuments
        │   └── DocumentCaptures
        ├── SelfieCaptures
        ├── LivenessChecks
        ├── FaceMatches
        ├── ProviderChecks
        ├── RiskAssessment
        ├── VerificationDecision
        └── AuditEvents
```

---

# Tables

## organizations

Represents a customer organization.

```text
id
public_id
name
slug
industry
status
default_country_profile_id
default_jurisdiction_id
settings_json
created_at
updated_at
deleted_at
```

Statuses:

```text
active
suspended
pending_review
closed
```

Indexes:

```text
unique(public_id)
unique(slug)
index(status)
```

---

## tenants

Represents the isolated technical boundary for an organization.

```text
id
public_id
organization_id
name
slug
status
settings_json
created_at
updated_at
deleted_at
```

Relationships:

```text
organization_id -> organizations.id
```

Indexes:

```text
unique(public_id)
unique(slug)
index(organization_id)
index(status)
```

Version 1.0 rule:

```text
One organization maps to one tenant.
```

---

## platform_users

Represents people who log into IdentityCore.

```text
id
public_id
tenant_id
email
password_hash
first_name
last_name
phone_number
status
is_platform_admin
mfa_enabled
last_login_at
created_at
updated_at
deleted_at
```

Statuses:

```text
active
inactive
invited
suspended
locked
```

Indexes:

```text
unique(email)
unique(public_id)
index(tenant_id)
index(status)
```

Note:

Platform-level administrators may have `tenant_id = null`.

Implementation note:

- The Django implementation stores hashed credentials through the framework-managed password field.
- `last_login_at` remains an explicit application field for audit-friendly login tracking.

---

## roles

Represents named access roles.

```text
id
public_id
tenant_id
name
description
scope
is_system_role
created_at
updated_at
deleted_at
```

Scopes:

```text
platform
tenant
```

Indexes:

```text
unique(public_id)
unique(tenant_id, name)
unique(name) where tenant_id is null
index(scope)
```

---

## permissions

Represents granular permissions.

```text
id
code
name
description
created_at
updated_at
```

Examples:

```text
create_verification
view_verification
review_verification
manage_api_clients
view_audit_logs
manage_users
configure_policies
```

Indexes:

```text
unique(code)
```

---

## role_permissions

Many-to-many table between roles and permissions.

```text
id
role_id
permission_id
created_at
```

Relationships:

```text
role_id -> roles.id
permission_id -> permissions.id
```

Indexes:

```text
unique(role_id, permission_id)
```

---

## user_roles

Many-to-many table between platform users and roles.

```text
id
user_id
role_id
tenant_id
created_at
```

Relationships:

```text
user_id -> platform_users.id
role_id -> roles.id
tenant_id -> tenants.id
```

Indexes:

```text
unique(user_id, role_id, tenant_id)
index(tenant_id)
```

---

# Country and Jurisdiction Tables

## jurisdictions

Represents a legal or administrative region.

```text
id
public_id
name
code
type
created_at
updated_at
```

Examples:

```text
Ghana
Nigeria
Kenya
European Union
```

Types:

```text
country
region
economic_area
agency
```

Indexes:

```text
unique(code)
```

---

## country_profiles

Represents country-specific identity configuration.

```text
id
public_id
jurisdiction_id
country_code
name
settings_json
is_active
created_at
updated_at
```

Relationships:

```text
jurisdiction_id -> jurisdictions.id
```

Indexes:

```text
unique(country_code)
index(is_active)
```

---

## document_types

Generic document classifications.

```text
id
code
name
description
is_active
created_at
updated_at
```

Codes:

```text
national_id
passport
driver_license
voter_id
health_id
residence_permit
student_id
employee_id
other
```

Indexes:

```text
unique(code)
```

---

## country_document_types

Maps generic document types to local country names.

```text
id
country_profile_id
document_type_id
local_name
issuing_authority
format_rules_json
is_supported
created_at
updated_at
```

Example for Ghana:

```text
document_type: national_id
local_name: Ghana Card
issuing_authority: National Identification Authority
```

Indexes:

```text
unique(country_profile_id, document_type_id, local_name)
index(country_profile_id)
index(document_type_id)
```

---

# API and Integration Tables

## api_clients

Represents external applications integrated with IdentityCore.

```text
id
public_id
tenant_id
name
client_id
client_secret_hash
status
scopes_json
allowed_ips_json
rate_limit_per_minute
created_by_id
last_used_at
created_at
updated_at
deleted_at
```

Statuses:

```text
active
disabled
rotating
revoked
```

Indexes:

```text
unique(public_id)
unique(client_id)
index(tenant_id)
index(status)
```

Implementation notes:

- `client_id` is separate from `public_id` and is the identifier sent in the `X-Client-Id` header.
- `client_secret_hash` stores only the hashed secret value.
- `allowed_ips_json` may be empty, in which case IP restriction is not enforced.

Do not store raw client secrets.

---

## webhook_endpoints

Represents organization webhook URLs.

```text
id
public_id
tenant_id
url
description
secret_hash
events_json
status
created_by_id
created_at
updated_at
deleted_at
```

Statuses:

```text
active
disabled
failed
```

Indexes:

```text
unique(public_id)
index(tenant_id)
index(status)
```

---

## webhook_events

Represents webhook events queued for delivery.

```text
id
public_id
tenant_id
webhook_endpoint_id
event_type
payload_json
status
attempt_count
next_retry_at
last_attempt_at
created_at
updated_at
```

Statuses:

```text
pending
delivered
failed
cancelled
```

Indexes:

```text
unique(public_id)
index(tenant_id)
index(webhook_endpoint_id)
index(event_type)
index(status)
index(next_retry_at)
```

---

## webhook_delivery_attempts

Represents each attempt to deliver a webhook.

```text
id
webhook_event_id
status_code
response_body
error_message
attempted_at
duration_ms
```

Relationships:

```text
webhook_event_id -> webhook_events.id
```

Indexes:

```text
index(webhook_event_id)
index(attempted_at)
```

---

# Verification Tables

## verification_subjects

Represents the individual whose identity is being verified.

```text
id
public_id
tenant_id
external_reference
full_name
email
phone_number
date_of_birth
metadata_json
created_at
updated_at
deleted_at
```

Indexes:

```text
unique(public_id)
index(tenant_id)
index(external_reference)
index(email)
index(phone_number)
```

Notes:

- `external_reference` is provided by the organization.
- Avoid storing unnecessary personal data.
- Fields may be nullable depending on verification workflow.

---

## verification_policies

Represents organization-defined verification rules.

```text
id
public_id
tenant_id
name
description
version
status
required_document_types_json
required_liveness_level
face_match_threshold
manual_review_threshold
verification_expiry_minutes
media_retention_days
metadata_retention_days
created_by_id
created_at
updated_at
deleted_at
```

Statuses:

```text
draft
active
archived
```

Indexes:

```text
unique(public_id)
unique(tenant_id, name, version)
index(tenant_id)
index(status)
```

Important:

When a Verification is created, the policy version used must be copied or referenced immutably.

---

## verifications

Central workflow object.

```text
id
public_id
tenant_id
organization_id
verification_subject_id
verification_policy_id
policy_snapshot_json
status
purpose
external_reference
expires_at
completed_at
cancelled_at
created_by_id
created_at
updated_at
deleted_at
```

Statuses:

```text
created
pending_consent
in_progress
awaiting_document
awaiting_selfie
processing
manual_review_required
verified
rejected
expired
cancelled
failed
```

Relationships:

```text
tenant_id -> tenants.id
organization_id -> organizations.id
verification_subject_id -> verification_subjects.id
verification_policy_id -> verification_policies.id
created_by_id -> platform_users.id
```

Implementation note:

- The current Django bootstrap stores the requested policy public ID in a string field while the dedicated verification policy model is still pending.
- `policy_snapshot_json` is present now so immutable policy snapshots can be populated once policy records are connected.

Indexes:

```text
unique(public_id)
index(tenant_id)
index(organization_id)
index(verification_subject_id)
index(status)
index(expires_at)
index(created_at)
index(external_reference)
```

---

## verification_sessions

Represents time-bound subject-facing sessions.

```text
id
public_id
tenant_id
verification_id
session_token_hash
status
started_at
expires_at
completed_at
last_seen_at
ip_address
user_agent
device_fingerprint
created_at
updated_at
```

Statuses:

```text
created
active
completed
expired
revoked
```

Relationships:

```text
verification_id -> verifications.id
```

Indexes:

```text
unique(public_id)
unique(session_token_hash)
index(tenant_id)
index(verification_id)
index(status)
index(expires_at)
```

Do not store raw session tokens.

Implementation note:

- Verification session URLs are derived from `VERIFICATION_PORTAL_BASE_URL` plus the session `public_id`, so the API can point subjects to a dedicated portal host without hardcoded path assumptions.

---

# Consent Tables

## consent_templates

Represents versioned consent .

```text
id
public_id
tenant_id
name
version
language
content
status
created_by_id
created_at
updated_at
deleted_at
```

Statuses:

```text
draft
active
archived
```

Indexes:

```text
unique(public_id)
unique(tenant_id, name, version, language)
index(tenant_id)
index(status)
```

---

## consent_records

Represents accepted consent for a verification.

```text
id
public_id
tenant_id
verification_id
verification_subject_id
consent_template_id
consent_text_snapshot
accepted
accepted_at
ip_address
user_agent
device_fingerprint
withdrawn_at
created_at
updated_at
```

Relationships:

```text
verification_id -> verifications.id
verification_subject_id -> verification_subjects.id
consent_template_id -> consent_templates.id
```

Implementation note:

- `consent_template_id` is currently nullable in the Django bootstrap so consent acceptance can still be recorded before tenant-managed consent templates are fully administered.

Indexes:

```text
unique(public_id)
index(tenant_id)
index(verification_id)
index(verification_subject_id)
index(accepted_at)
```

---

# Document Tables

## identity_documents

Represents an identity document submitted for verification.

```text
id
public_id
tenant_id
verification_id
verification_subject_id
document_type_id
country_profile_id
local_document_name
document_number_hash
issuing_authority
issued_at
expires_at
status
extracted_data_json
created_at
updated_at
deleted_at
```

Statuses:

```text
submitted
processing
processed
failed
rejected
```

Relationships:

```text
verification_id -> verifications.id
verification_subject_id -> verification_subjects.id
document_type_id -> document_types.id
country_profile_id -> country_profiles.id
```

Implementation note:

- The current Django bootstrap stores `document_type_id` and `country_profile_id` as string identifiers so document submission can proceed before the catalog tables are implemented.

Indexes:

```text
unique(public_id)
index(tenant_id)
index(verification_id)
index(verification_subject_id)
index(document_type_id)
index(status)
index(document_number_hash)
```

Notes:

- Store document number as a hash where possible.
- Avoid storing full document number unless required.

---

## document_captures

Represents uploaded document images or scans.

```text
id
public_id
tenant_id
identity_document_id
side
storage_url
storage_key
storage_provider
mime_type
file_size_bytes
checksum_sha256
quality_score
status
captured_at
created_at
updated_at
deleted_at
```

Sides:

```text
front
back
single
mrz
other
```

Statuses:

```text
uploaded
validated
rejected
deleted
```

Relationships:

```text
identity_document_id -> identity_documents.id
```

Implementation note:

- During bootstrap, uploaded file metadata is represented by the provided `upload_id`, which is currently mapped into a derived `storage_key` until the dedicated upload initialization flow is added.

Indexes:

```text
unique(public_id)
index(tenant_id)
index(identity_document_id)
index(status)
index(captured_at)
```

---

## document_processing_results

Represents OCR, classification, and quality results.

```text
id
public_id
tenant_id
identity_document_id
provider_check_id
processing_type
status
confidence_score
result_json
model_version
processed_at
created_at
updated_at
```

Processing types:

```text
ocr
classification
quality_check
tamper_check
mrz_read
```

Indexes:

```text
unique(public_id)
index(tenant_id)
index(identity_document_id)
index(processing_type)
index(status)
```

---

# Biometric Tables

## selfie_captures

Represents selfie image or video evidence.

```text
id
public_id
tenant_id
verification_id
verification_subject_id
storage_url
storage_key
storage_provider
capture_type
mime_type
file_size_bytes
checksum_sha256
quality_score
face_count
status
captured_at
created_at
updated_at
deleted_at
```

Capture types:

```text
image
video
```

Statuses:

```text
uploaded
validated
rejected
deleted
```

Indexes:

```text
unique(public_id)
index(tenant_id)
index(verification_id)
index(verification_subject_id)
index(status)
index(captured_at)
```

Implementation note:

- During bootstrap, selfie upload metadata is represented by the provided `upload_id`, which is currently mapped into a derived `storage_key` until the dedicated upload initialization flow is added.
- The current session flow stores a default `face_count = 1` placeholder until AI-assisted face counting is connected.

---

## biometric_templates

Represents biometric embeddings or templates.

```text
id
public_id
tenant_id
verification_id
verification_subject_id
source_type
source_id
template_type
template_storage_key
template_hash
model_name
model_version
status
created_at
updated_at
deleted_at
```

Source types:

```text
selfie_capture
document_capture
```

Template types:

```text
face_embedding
```

Statuses:

```text
active
deleted
expired
```

Indexes:

```text
unique(public_id)
index(tenant_id)
index(verification_id)
index(verification_subject_id)
index(source_type, source_id)
index(template_hash)
```

Note:

Biometric templates are highly sensitive and should be encrypted separately from ordinary application data.

---

## liveness_checks

Represents liveness detection results.

```text
id
public_id
tenant_id
verification_id
selfie_capture_id
provider_check_id
liveness_type
status
score
confidence_level
failure_reason
model_name
model_version
checked_at
created_at
updated_at
```

Liveness types:

```text
passive
active
```

Statuses:

```text
passed
failed
inconclusive
error
```

Indexes:

```text
unique(public_id)
index(tenant_id)
index(verification_id)
index(selfie_capture_id)
index(status)
index(checked_at)
```

Implementation note:

- The current Django bootstrap creates liveness checks with an initial placeholder status while the AI service integration is still pending, and the session API returns a subject-facing `processing` state for that handoff.

---

## face_matches

Represents face comparison results.

```text
id
public_id
tenant_id
verification_id
selfie_capture_id
identity_document_id
document_capture_id
provider_check_id
status
match_score
confidence_level
threshold_used
model_name
model_version
matched_at
created_at
updated_at
```

Statuses:

```text
matched
not_matched
inconclusive
error
```

Indexes:

```text
unique(public_id)
index(tenant_id)
index(verification_id)
index(status)
index(match_score)
index(matched_at)
```

Implementation note:

- The current Django bootstrap creates a face-match placeholder record when liveness is submitted so downstream verification detail APIs can expose a concrete face-match lifecycle before AI integration is connected.
- The bootstrap flow links the face match to the latest submitted identity document and prefers a `front` or `single` document capture when available.

---

# Provider Tables

## providers

Represents internal or external providers.

```text
id
public_id
name
code
provider_type
status
configuration_json
created_at
updated_at
deleted_at
```

Provider types:

```text
document
biometric
identity_database
liveness
risk
notification
```

Statuses:

```text
active
disabled
testing
deprecated
```

Indexes:

```text
unique(public_id)
unique(code)
index(provider_type)
index(status)
```

---

## provider_checks

Represents a call to a provider during verification.

```text
id
public_id
tenant_id
verification_id
provider_id
check_type
status
provider_reference
request_metadata_json
response_metadata_json
normalized_result_json
error_code
error_message
started_at
completed_at
created_at
updated_at
```

Check types:

```text
document_ocr
document_quality
face_match
liveness
identity_lookup
risk_check
```

Statuses:

```text
pending
processing
completed
failed
timeout
cancelled
```

Relationships:

```text
provider_id -> providers.id
verification_id -> verifications.id
```

Indexes:

```text
unique(public_id)
index(tenant_id)
index(verification_id)
index(provider_id)
index(check_type)
index(status)
index(provider_reference)
```

---

# Decision and Risk Tables

## risk_assessments

Represents risk scoring for a verification.

```text
id
public_id
tenant_id
verification_id
risk_score
risk_level
signals_json
recommendation
created_at
updated_at
```

Risk levels:

```text
low
medium
high
critical
```

Recommendations:

```text
approve
reject
manual_review
```

Indexes:

```text
unique(public_id)
unique(verification_id)
index(tenant_id)
index(risk_level)
index(risk_score)
```

---

## verification_decisions

Represents the final decision for a verification.

```text
id
public_id
tenant_id
verification_id
decision
decision_type
reason_code
reason_detail
evidence_summary_json
decided_by_id
decided_at
created_at
updated_at
```

Decisions:

```text
verified
rejected
manual_review_required
expired
cancelled
failed
```

Decision types:

```text
automatic
manual
system
```

Relationships:

```text
verification_id -> verifications.id
decided_by_id -> platform_users.id
```

Indexes:

```text
unique(public_id)
unique(verification_id)
index(tenant_id)
index(decision)
index(decision_type)
index(decided_at)
```

---

# Audit Tables

## audit_events

Represents immutable audit records.

```text
id
public_id
tenant_id
actor_type
actor_id
action
target_type
target_id
ip_address
user_agent
device_fingerprint
metadata_json
sensitive_metadata_hash
created_at
```

Actor types:

```text
platform_user
api_client
verification_subject
system
provider
```

Examples of actions:

```text
user.login
verification.created
consent.accepted
document.uploaded
selfie.uploaded
liveness.completed
face_match.completed
verification.verified
verification.rejected
api_client.created
webhook.delivered
```

Indexes:

```text
unique(public_id)
index(tenant_id)
index(actor_type, actor_id)
index(action)
index(target_type, target_id)
index(created_at)
```

Rules:

- Audit events should be append-only.
- Audit events should not be updated.
- Sensitive data must be masked or hashed.
- Deletion should require special compliance process.

---

# Notification Tables

## notifications

Represents notification records.

```text
id
public_id
tenant_id
recipient_type
recipient
channel
template_code
status
subject
body_preview
provider_reference
sent_at
created_at
updated_at
```

Channels:

```text
email
sms
in_app
```

Statuses:

```text
pending
sent
failed
cancelled
```

Indexes:

```text
unique(public_id)
index(tenant_id)
index(channel)
index(status)
index(created_at)
```

---

# Reporting Tables

Version 1.0 can generate reports from transactional tables.

Future versions may introduce summary tables such as:

```text
daily_verification_metrics
tenant_usage_metrics
provider_performance_metrics
api_usage_metrics
```

For MVP, avoid premature reporting tables unless performance requires them.

---

# Retention and Deletion

Different data types should have different retention rules.

## Short-term retention

Raw media:

```text
document captures
selfie captures
liveness videos
```

Recommended default:

```text
30 days
```

## Medium-term retention

Verification metadata:

```text
verification status
decision
scores
provider references
risk summary
```

Recommended default:

```text
1-7 years depending on organization and jurisdiction
```

## Long-term retention

Audit metadata:

```text
audit events
security logs
decision records
```

Recommended default:

```text
7 years or jurisdiction-specific requirement
```

---

# Sensitive Data Rules

The following data should be treated as highly sensitive:

- Raw document images
- Selfie images
- Liveness videos
- Biometric templates
- Document numbers
- Date of birth
- Extracted identity data
- Provider responses
- Audit logs

Rules:

- Encrypt sensitive data at rest.
- Do not expose sensitive data through public URLs.
- Use signed temporary URLs for media access.
- Store hashes instead of raw identifiers where possible.
- Mask sensitive fields in logs and dashboards.
- Record all access to sensitive records.

---

# Indexing Strategy

High-priority indexes:

```text
tenant_id
public_id
verification_id
verification_subject_id
status
created_at
expires_at
external_reference
```

Most common queries:

```text
Find verifications by tenant and status.
Find verification by public_id.
Find verification by external_reference.
Find active verification sessions by token hash.
Find audit events by tenant and target.
Find webhook events pending retry.
Find expired verifications.
```

---

# Public ID Strategy

Every externally visible object should have a public ID.

Examples:

```text
org_...
ten_...
usr_...
ver_...
sub_...
doc_...
cap_...
sel_...
liv_...
mat_...
dec_...
aud_...
```

Reasons:

- Avoid exposing database IDs.
- Improve API safety.
- Make logs easier to read.
- Support safer data migration.

---

# Future Database Separation

As IdentityCore grows, the following may be separated:

```text
Core relational database
Audit database
Biometric metadata database
Reporting warehouse
Provider integration database
Billing database
```

First candidates for separation:

1. Audit events
2. Webhook events
3. Biometric templates
4. Reporting metrics

---

# Version 1.0 Database Scope

Version 1.0 includes:

- Organizations
- Tenants
- Platform Users
- Roles
- Permissions
- API Clients
- Webhooks
- Country Profiles
- Document Types
- Verification Subjects
- Verification Policies
- Verifications
- Verification Sessions
- Consent Records
- Identity Documents
- Document Captures
- Selfie Captures
- Biometric Templates
- Liveness Checks
- Face Matches
- Provider Checks
- Risk Assessments
- Verification Decisions
- Audit Events
- Notifications

Version 1.0 excludes:

- Criminal records
- Immigration records
- Government-owned identity records
- Fingerprint templates
- Iris templates
- Digital wallets
- National identity issuance records
- Centralized citizen registry

---

# Final Database Principle

The database must support trust.

Every table should help preserve tenant isolation, traceability, privacy, security, and verification accuracy.

If a field is not needed for verification, auditability, compliance, or integration, it should not be stored.
