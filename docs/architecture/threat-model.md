# Threat Model

## IdentityCore

**Version:** 1.0

---

## Purpose

This document identifies major security threats against IdentityCore and defines the controls required to reduce risk.

IdentityCore handles personal data, identity documents, biometric data, API credentials, verification decisions, audit logs, and organization data. A successful attack could harm Verification Subjects, Organizations, and the trustworthiness of the platform.

---

## Threat Modeling Approach

IdentityCore uses the STRIDE framework:

- Spoofing
- Tampering
- Repudiation
- Information Disclosure
- Denial of Service
- Elevation of Privilege

---

## Assets to Protect

IdentityCore must protect:

- Platform User accounts
- API client credentials
- Verification Sessions
- Verification Subject data
- Identity Documents
- Selfie Captures
- Biometric Templates
- Liveness media
- Verification Decisions
- Audit Events
- Provider credentials
- Webhook secrets
- Object storage files
- Database records
- Encryption keys
- Internal AI service

---

## Trust Boundaries

The main trust boundaries are:

```text
Verification Subject Browser
        ↓
Verification Portal
        ↓
Public API
        ↓
Django Backend
        ↓
PostgreSQL / Redis / Object Storage
        ↓
FastAPI AI Service
        ↓
External Providers
```

Every boundary requires authentication, validation, authorization, rate limiting, logging, or encryption depending on the data involved.

---

## Threat Actors

Potential attackers include:

- External attackers
- Malicious Verification Subjects
- Compromised API Clients
- Malicious Organization Users
- Compromised Platform Users
- Insider threats
- Automated bots
- Fraud rings
- Compromised third-party providers
- Network attackers
- Cloud infrastructure attackers

---

## Spoofing Threats

## Threat: Stolen Platform User Credentials

An attacker obtains a Platform User's email and password.

Impact:

- Unauthorized dashboard access
- Verification data exposure
- Manual review abuse
- API client creation

Controls:

- MFA
- Strong password hashing
- Login rate limiting
- Suspicious login detection
- Session revocation
- Audit logging

---

## Threat: Leaked API Secret

An attacker obtains an Organization API secret.

Impact:

- Unauthorized verification creation
- Data access
- Webhook manipulation
- Billing abuse

Controls:

- Hash API secrets at rest
- Show secrets only once
- API key rotation
- Scoped API permissions
- Allowed networks
- Rate limiting
- Request signing
- Audit logs

---

## Threat: Verification Session Token Theft

An attacker steals a Verification Session URL.

Impact:

- Fraudulent submission
- Identity impersonation
- Verification hijacking

Controls:

- Expiring session tokens
- Secure random tokens
- Token hashing at rest
- Device/IP risk checks
- Session revocation
- Step-level validation
- Liveness checks

---

## Threat: Fake Provider Response

An attacker attempts to spoof a provider response.

Impact:

- False verification result
- Trust compromise

Controls:

- Signed provider callbacks
- Provider allowlisting
- TLS
- Request correlation IDs
- Provider response validation
- Provider metadata audit logs

---

## Tampering Threats

## Threat: Modified Verification Payload

An attacker modifies request data such as document type, verification ID, or subject details.

Impact:

- Incorrect verification
- Tenant data exposure
- Fraudulent approval

Controls:

- Server-side validation
- Tenant ownership checks
- Immutable policy snapshots
- Request signing for API clients
- Audit logging

---

## Threat: File Upload Tampering

An attacker uploads malicious or modified files.

Impact:

- Malware processing
- AI service compromise
- Storage abuse
- Invalid evidence

Controls:

- MIME validation
- File size limits
- Extension validation
- Malware scanning where possible
- Checksum verification
- Isolated processing
- Object storage access control

---

## Threat: Biometric Template Tampering

An attacker modifies face embeddings or biometric records.

Impact:

- False match
- False rejection
- Audit integrity compromise

Controls:

- Encryption
- Access control
- Integrity hashes
- Restricted service access
- Audit events
- Database permissions

---

## Threat: Audit Log Tampering

An attacker modifies or deletes audit events.

Impact:

- Loss of accountability
- Hidden abuse
- Compliance failure

Controls:

- Append-only audit events
- Restricted write permissions
- No normal update/delete paths
- Separate audit storage in future
- Hash chaining in future
- Admin action logging

---

## Repudiation Threats

## Threat: User Denies Performing Manual Review

A Verification Officer denies approving or rejecting a case.

Impact:

- Accountability failure
- Compliance issue

Controls:

- Authenticated sessions
- Audit events
- Actor ID
- Timestamp
- IP address
- Device fingerprint
- Reason codes

---

## Threat: Organization Denies API Usage

An Organization claims a verification was not created by them.

Impact:

- Disputes
- Billing conflict
- Compliance issue

Controls:

- API client audit logs
- Request IDs
- Idempotency keys
- API key identity
- Webhook records
- Immutable event history

---

## Threat: Verification Subject Denies Consent

A Verification Subject claims they never agreed to verification.

Impact:

- Legal dispute
- Compliance risk

Controls:

- Consent template versioning
- Consent timestamp
- IP/user agent
- Verification purpose
- Organization identity
- Consent record audit trail

---

## Information Disclosure Threats

## Threat: Cross-Tenant Data Exposure

A user accesses another Organization's verification data.

Impact:

- Severe privacy breach
- Trust failure
- Legal exposure

Controls:

- Tenant-scoped queries
- Tenant middleware
- Service-layer tenant checks
- Permission checks
- Automated tests for tenant isolation
- Audit alerts for violations

---

## Threat: Sensitive Data in Logs

Sensitive fields are accidentally logged.

Impact:

- Data leakage
- Compliance violation

Controls:

- Structured logging
- Sensitive field masking
- Log review
- Secret scanning
- Logging policy
- No raw media or tokens in logs

---

## Threat: Public Object Storage Exposure

Document or selfie files become publicly accessible.

Impact:

- Severe privacy breach
- Biometric exposure

Controls:

- Private buckets
- Signed temporary URLs
- Bucket policy reviews
- Storage access logging
- Retention cleanup
- No permanent public URLs

---

## Threat: GraphQL Overexposure

GraphQL exposes sensitive fields or allows broad querying.

Impact:

- Data leakage
- Tenant data exposure
- Performance abuse

Controls:

- Field-level authorization
- Query depth limits
- Query complexity limits
- Disable public GraphQL access
- Rate limiting
- Tenant filters

---

## Threat: Provider Response Leakage

Raw third-party provider payloads expose unnecessary data.

Impact:

- Excessive data storage
- Privacy risk

Controls:

- Normalize provider responses
- Redact raw payloads
- Store only necessary metadata
- Encrypt sensitive payloads
- Apply retention policies

---

## Denial of Service Threats

## Threat: API Flooding

An attacker sends excessive API requests.

Impact:

- Service slowdown
- Increased costs
- Customer disruption

Controls:

- Rate limiting
- WAF
- DDoS protection
- Request size limits
- API client quotas
- Monitoring and alerts

---

## Threat: Upload Abuse

An attacker uploads many large files.

Impact:

- Storage exhaustion
- Processing backlog
- Increased cost

Controls:

- File size limits
- Upload rate limits
- Tenant quotas
- Signed upload expiry
- Storage monitoring
- Cleanup jobs

---

## Threat: AI Processing Exhaustion

Attackers trigger expensive OCR, face matching, or liveness jobs.

Impact:

- Queue backlog
- High CPU usage
- Verification delays

Controls:

- AI queue separation
- Per-tenant quotas
- Worker autoscaling
- Job timeouts
- Retry limits
- Rate limiting

---

## Threat: Webhook Retry Storm

Failed webhook endpoints cause excessive retries.

Impact:

- Worker overload
- Queue delays

Controls:

- Exponential backoff
- Max retry count
- Dead-letter queue
- Endpoint disabling
- Webhook monitoring

---

## Elevation of Privilege Threats

## Threat: Organization User Becomes Platform Admin

A tenant user exploits authorization logic to gain platform-level access.

Impact:

- Full platform compromise

Controls:

- Strict role separation
- Server-side permission checks
- Platform role isolation
- Admin MFA
- Audit logs
- Authorization tests

---

## Threat: Verification Officer Accesses Unassigned Sensitive Cases

A reviewer accesses cases outside their scope.

Impact:

- Privacy breach
- Insider abuse

Controls:

- Assignment-based access
- Role-based permissions
- Tenant isolation
- Audit logging
- Sensitive view alerts

---

## Threat: API Client Uses Unauthorized Scope

An API Client attempts actions beyond its permissions.

Impact:

- Unauthorized access
- Data manipulation

Controls:

- Scope checks
- Least privilege API keys
- API gateway enforcement
- Audit events
- Rate limits

---

## Threat: Background Worker Bypasses Tenant Checks

Celery task processes data without tenant validation.

Impact:

- Cross-tenant data corruption
- Data exposure

Controls:

- Include tenant context in jobs
- Validate tenant ownership inside tasks
- Avoid raw IDs without tenant context
- Task-level authorization checks
- Integration tests

---

## AI-Specific Threats

## Threat: Spoofed Selfie

A Verification Subject uses a printed photo, phone screen, mask, or deepfake.

Impact:

- False verification
- Fraudulent account creation

Controls:

- Liveness detection
- Face quality checks
- Active challenge for risky cases
- Manual review
- Risk scoring

---

## Threat: Adversarial Image Attack

An attacker submits manipulated images to fool AI models.

Impact:

- False match
- False liveness
- Model failure

Controls:

- Image normalization
- Quality checks
- Model robustness testing
- Manual review thresholds
- Provider fallback
- AI monitoring

---

## Threat: Model Output Manipulation

An attacker tampers with AI service responses.

Impact:

- Incorrect verification decision

Controls:

- Internal-only AI service
- Service-to-service authentication
- TLS/private networking
- Response schema validation
- Audit provider checks
- Store model version

---

## Threat: Model Bias Causes Harm

AI performs worse for some groups or document types.

Impact:

- False rejection
- Unfair outcomes
- Reputational risk

Controls:

- Manual review
- Accuracy monitoring
- Threshold tuning
- Avoid AI-only final decisions
- Model evaluation
- Human oversight

---

## Infrastructure Threats

## Threat: Database Compromise

An attacker accesses PostgreSQL.

Impact:

- Major data breach
- Credential exposure
- Audit compromise

Controls:

- Least privilege DB users
- Encryption at rest
- Network isolation
- Backups encryption
- Strong credentials
- Monitoring
- Sensitive field encryption

---

## Threat: Redis Exposure

Redis is exposed publicly or accessed by attacker.

Impact:

- Queue manipulation
- Cache leakage
- Session risk

Controls:

- Private network only
- Authentication
- TLS where available
- No public Redis
- Minimal sensitive data in Redis

---

## Threat: Secrets Leak

Secrets are committed to Git or exposed in logs.

Impact:

- System compromise
- Provider compromise

Controls:

- Secret scanning
- Environment secrets
- Secrets manager
- Rotation policy
- Developer training
- No secrets in logs

---

## Threat: Compromised CI/CD Pipeline

An attacker injects malicious code into build or deployment pipeline.

Impact:

- Supply chain compromise
- Production compromise

Controls:

- Branch protection
- Required reviews
- CI secret protection
- Dependency scanning
- Signed artifacts in future
- Limited deploy permissions

---

## Web Threats

IdentityCore must protect against common web threats:

- SQL injection
- XSS
- CSRF
- SSRF
- Path traversal
- Command injection
- Open redirect
- Clickjacking
- Insecure deserialization
- Broken access control

Controls:

- Django ORM
- Input validation
- Output escaping
- CSRF protection where applicable
- Security headers
- Safe file handling
- URL allowlists
- Dependency scanning

---

## Risk Ratings

Threats should be rated using:

```text
Low
Medium
High
Critical
```

Risk depends on:

- Likelihood
- Impact
- Detectability
- Ease of exploitation
- Sensitivity of affected data

Critical risks must be addressed before production.

---

## Highest Priority Risks for Version 1.0

The highest priority risks are:

1. Cross-tenant data exposure
2. Public exposure of document or selfie media
3. API secret leakage
4. Weak verification session security
5. Unauthorized manual review access
6. Sensitive data in logs
7. AI spoofing attacks
8. Insecure file upload handling
9. Audit log tampering
10. Misconfigured object storage

---

## Required Security Tests

Before production, IdentityCore must test:

- Tenant isolation
- Permission enforcement
- API key scope checks
- Upload validation
- Session expiry
- Rate limits
- Webhook signature verification
- Sensitive field masking
- Object storage privacy
- GraphQL access control
- Manual review authorization

---

## Residual Risk

Some risks cannot be fully eliminated.

Examples:

- Advanced deepfake attacks
- Insider abuse by authorized users
- False positives or false negatives from AI
- Compromised customer systems
- Third-party provider failures

IdentityCore reduces these risks through layered controls, auditability, manual review, monitoring, and clear customer responsibility boundaries.

---

## Review Frequency

This threat model should be reviewed:

- Before production launch
- After major architecture changes
- After adding new AI models
- After adding new providers
- After security incidents
- At least quarterly

---

## Final Threat Model Principle

IdentityCore must assume that identity systems attract serious attackers.

The platform must not rely on obscurity, trust, or good behavior. It must rely on strong authentication, strict authorization, tenant isolation, privacy-preserving design, secure infrastructure, continuous monitoring, and complete auditability.
