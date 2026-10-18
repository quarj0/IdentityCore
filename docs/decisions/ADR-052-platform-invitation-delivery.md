# ADR 052: Platform administrator invitation delivery

Status: Accepted

Platform administrator invitations use the existing durable notification outbox with
an explicitly platform-scoped email record. A database constraint restricts null-tenant
notifications to this template/channel/recipient kind. Delivery secrets are encrypted,
excluded from previews and cleared after a terminal delivery result. Platform messages
use deployment email configuration, never a tenant provider assignment. Pending work
survives broker outages; stale invitations are cancelled before delivery.

The only currently supported platform invitation role is `Platform Admin`, whose
privilege is full platform administration. The UI must not imply read-only or limited
roles until the authorization boundary enforces them. Unsupported pending roles cannot
be accepted. Normal tenant roles and invitations are unaffected.

Invitation links carry the token in a fragment and enter a public acceptance page.
Acceptance consumes the token once, records platform audit evidence and requires the
normal MFA-aware sign-in/security setup afterward. Delivery failures remain observable;
replacement of a failed-delivery invitation must rotate its token and invalidate the
old link. Never claim an email was sent merely because it was durably queued.
