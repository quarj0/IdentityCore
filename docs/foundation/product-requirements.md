# Product Requirements Document (PRD)

## IdentityCore

**Version:** 1.0 (MVP)

---

## Purpose

This document defines the functional and non-functional requirements for the first release (MVP) of IdentityCore.

The objective of Version 1.0 is to deliver a secure, multi-tenant identity verification platform that enables organizations to verify a person's identity using identity documents, facial recognition, and liveness detection through a simple API and web interface.

This document intentionally limits scope to ensure the platform is reliable, secure, and production-ready before expanding into broader digital identity services.

---

## Product Goal

Build a trusted identity verification platform that organizations can integrate into their applications to verify users securely, quickly, and transparently.

---

## Success Metrics

The MVP will be considered successful when it can:

- Create verification requests.
- Verify a person's identity using a document and selfie.
- Perform liveness detection.
- Perform facial matching.
- Return a verification result.
- Provide complete audit logs.
- Support multiple organizations (multi-tenancy).
- Expose secure REST APIs.
- Operate reliably in production.

---

## Target Customers

Initial customers include:

- Schools
- Universities
- Employers
- Security companies
- Event organizers
- Hostels
- Hospitals
- Fintech startups
- Digital platforms
- SaaS companies

Government agencies are **not** considered initial customers for Version 1.0.

---

## User Roles

## Platform Administrator

Responsible for overall platform management.

Permissions include:

- Manage tenants
- Manage billing
- View audit logs
- Configure providers
- Manage APIs
- Monitor platform health

---

## Tenant Administrator

Represents an organization using IdentityCore.

Permissions include:

- Invite users
- Configure verification workflows
- Generate API keys
- View reports
- View organization audit logs

---

## Verification Officer

Performs manual reviews when required.

Permissions include:

- Review verification results
- Approve or reject manual cases
- View assigned verification sessions

---

## Verification Subject

The individual being verified.

Capabilities include:

- Give consent
- Upload identity document
- Capture selfie
- Complete liveness challenge
- View verification status (where permitted)

---

## Functional Requirements

## Authentication

The system shall support:

- Email/password authentication
- Multi-factor authentication
- JWT authentication
- Secure session management
- Password reset
- Device/session revocation

## No-Code Verification Workflows

IdentityCore shall support no-code verification workflows for organizations that do not have technical teams or do not want to integrate through APIs.

Organization Administrators shall be able to:

- Create verification requests from the dashboard.
- Generate secure verification links.
- Share verification links manually by email or copy link.
- Configure verification policies without writing code.
- Select accepted Document Types.
- Configure liveness requirements.
- Configure face match thresholds.
- Configure manual review thresholds.
- Customize basic organization branding.
- View verification results from the dashboard.
- Review cases requiring manual review.
- Export verification reports where permitted.

No-code workflows shall use the same Verification Engine, Verification Policies, Consent Records, Audit Events, and Decision Engine as API-based workflows.

SMS link sharing may be implemented later, but it is not part of the active MVP no-code workflow requirements.

---

## Organization Onboarding

IdentityCore is an organization-first platform. Organizations are the customers of the platform, while the individuals being verified are referred to as Verification Subjects.

Before an organization can use production features, it shall complete the onboarding process.

For the MVP implementation, registration is organization-first:

- A user registers themselves and their organization together.
- The user account remains inactive until email verification succeeds.
- The default Tenant Administrator role is assigned only after email verification succeeds.
- Trial onboarding access may begin after email verification.
- Production API credentials remain blocked until platform approval.

### Step 1 – User Registration

A primary organization administrator shall register using:

- Full Name
- Business Email Address
- Password
- Country

The email address shall be verified before the account becomes active.

During this step, the system shall:

- Create the Platform User in an inactive state.
- Create the Organization in a Pending Email Verification state.
- Create the Tenant in a Pending state.
- Create onboarding state for the organization.
- Queue an email verification message.

---

### Step 2 – Organization Registration

The initial registration request shall also capture organization information:

- Organization Name
- Organization Type
- Country
- Website (optional)
- Support Email
- Phone Number

Supported organization types may include:

- Government
- Financial Institution
- Educational Institution
- Healthcare Provider
- Enterprise
- Non-Governmental Organization (NGO)
- Startup
- Other

After email verification succeeds, the system shall:

- Activate the Platform User.
- Assign the default Tenant Administrator role.
- Move onboarding to Organization Verification Required.
- Move the Organization and Tenant into Pending Review for the remaining onboarding steps.

---

### Step 3 – Organization Verification

Organizations requesting access to production services shall provide sufficient information to establish their legitimacy.

Information may include:

- Business Registration Number
- Tax Identification Number (where applicable)
- Registered Address
- Official Website
- Supporting documentation

Examples of supporting documentation include:

- Certificate of Incorporation
- Business Registration Certificate
- Government Authorization
- Operating License

Verification may be performed manually or through automated processes depending on jurisdiction and future platform capabilities.

---

### Step 4 – Administrator Identity Verification

The primary administrator shall complete identity verification using IdentityCore.

Verification may include:

- Identity Document
- Selfie Capture
- Liveness Detection

This establishes trust between the platform, the organization, and its primary administrator.

---

### Step 5 – Platform Review

Upon successful submission of all required information, the organization enters a Pending Review state.

IdentityCore administrators may:

- Approve the organization
- Reject the organization
- Request additional information

Organizations shall not receive production API credentials until the review process has been completed successfully.
Sandbox or trial access may be allowed earlier where explicitly supported by the platform.

---

### Step 6 – Organization Activation

Once approved, the organization may:

- Create Projects
- Configure Verification Policies
- Generate API Keys
- Configure Webhooks
- Invite Team Members
- Create Verification Requests
- Access Production APIs

---

## Organization Organization Tier

IdentityCore assigns every organization an Organization Tier that determines the capabilities available to that organization.

Organization Tier are designed to reduce platform abuse while allowing organizations to gain access to additional functionality as trust is established.

### Tier 0 – Trial

Purpose:

Evaluate the platform.

Capabilities:

- Sandbox environment only
- Test API Keys
- Mock verification responses
- Limited dashboard functionality
- No production verification
- No production webhooks

---

### Tier 1 – Verified

Purpose:

Verified organizations beginning production usage.

Requirements:

- Organization approved
- Administrator identity verified

Capabilities:

- Production API access
- Production verification
- Webhooks
- Basic reporting
- Standard rate limits

---

### Tier 2 – Trusted

Purpose:

Organizations with an established operational history.

Requirements may include:

- Sustained platform usage
- Good compliance history
- Successful billing history
- Internal review

Additional capabilities:

- Increased API limits
- Higher verification quotas
- Advanced verification policies
- Priority support
- Additional provider integrations

---

### Tier 3 – Enterprise

Purpose:

Large organizations requiring dedicated enterprise capabilities.

Examples:

- Governments
- National Identity Authorities
- Banks
- Large Enterprises

Capabilities:

- Dedicated deployments
- Private Cloud or On-Premises deployment
- Custom provider integrations
- Dedicated support
- Custom SLAs
- Advanced compliance features
- Government integrations

---

Organization Tier are administrative controls and shall not affect the integrity or outcome of verification decisions.

Their purpose is to govern platform access, operational limits, deployment options, and customer support.

## Multi-Tenant Architecture

The system shall:

- Support multiple organizations.
- Isolate tenant data.
- Support organization branding.
- Support organization-specific API keys.

---

## Verification Requests

Organizations shall be able to:

- Create verification requests.
- Generate verification links.
- Set verification expiration.
- Cancel verification requests.
- Track verification progress.

---

## Identity Document Verification

The platform shall support:

- Document upload.
- OCR extraction.
- Image quality validation.
- Document classification.
- Document metadata extraction.

Version 1.0 does **not** validate documents against government databases.

---

## Selfie Capture

The platform shall:

- Capture selfies.
- Validate image quality.
- Detect multiple faces.
- Detect missing faces.

---

## Liveness Detection

The platform shall:

- Detect presentation attacks.
- Support passive liveness.
- Support active liveness challenges.
- Return confidence scores.

---

## Face Matching

The platform shall:

- Generate facial embeddings.
- Compare document image with selfie.
- Produce similarity scores.
- Produce confidence scores.

---

## Verification Decision

The platform shall return:

- Verified
- Rejected
- Manual Review Required

Every decision shall include supporting evidence.

---

## Audit Logging

Every sensitive action shall be logged, including:

- Authentication
- Verification creation
- Document uploads
- Face matching
- Manual decisions
- API usage
- Administrative actions

Audit records shall be immutable.

---

## Notifications

The platform shall support:

- Email notifications
- Webhook callbacks

SMS support is outside the MVP scope.

---

## Developer APIs

Version 1.0 shall expose:

- REST API
- Webhooks
- API keys
- API documentation

GraphQL will initially power internal dashboards only.

---

## Non-Functional Requirements

## Security

The platform shall implement:

- HTTPS everywhere
- Encryption at rest
- Encryption in transit
- JWT authentication
- RBAC
- Rate limiting
- API signing
- Secure secrets management

---

## Performance

Target response times:

- Authentication: < 300 ms
- Verification creation: < 500 ms
- Face matching: < 3 seconds
- Verification result: < 5 seconds

---

## Scalability

The platform shall support horizontal scaling through stateless services and asynchronous background processing.

---

## Reliability

Target uptime:

99.9%

---

## Privacy

The platform shall:

- Collect only necessary data.
- Support consent workflows.
- Support configurable retention policies.
- Allow deletion of retained media after policy expiry.

---

## Maintainability

The platform shall:

- Follow clean architecture principles.
- Support automated testing.
- Use API versioning.
- Maintain comprehensive documentation.

---

## Out of Scope (Version 1.0)

The following features are intentionally excluded:

- Government database integrations
- Passport verification
- Document Type verification
- Driver's licence verification
- Fingerprint recognition
- Iris recognition
- Criminal records
- Immigration services
- Hospital integrations
- Payment processing
- Mobile applications
- AI fraud prediction
- Offline verification
- Digital identity wallet
- SDKs for all languages

These features remain part of the long-term roadmap.

---

## MVP Deliverables

Version 1.0 will deliver:

- Multi-tenant platform
- Authentication
- Organization management
- Verification workflows
- Document upload
- OCR
- Selfie capture
- Liveness detection
- Face matching
- Verification decisions
- Audit logs
- REST API
- Webhooks
- Admin dashboard
- Developer documentation

---

## Acceptance Criteria

IdentityCore Version 1.0 is complete when an organization can:

1. Register an organization.
2. Create a verification request.
3. Send the verification link to an Verification Subject.
4. Receive user consent.
5. Receive document upload.
6. Receive selfie capture.
7. Perform liveness detection.
8. Perform facial matching.
9. Receive a verification decision.
10. Receive webhook notifications.
11. Review audit logs.
12. Integrate successfully using the public REST API.

---

## Product Philosophy

IdentityCore is not a facial recognition application.

It is an identity infrastructure platform.

Every feature added to the platform must strengthen trust, improve security, preserve privacy, or simplify identity verification for organizations and the individuals they serve.
