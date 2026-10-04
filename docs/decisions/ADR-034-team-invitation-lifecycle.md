# ADR-034: Tenant invitation lifecycle and encrypted delivery

Status: Accepted

Tenant invitations are single-use capabilities bound to an immutable email,
tenant, and tenant role. Tenant management requires `manage_team`; administrators
may grant only permissions they already hold. Tenant locking serializes creation,
resend, revocation and acceptance. Role and account state are checked again at
acceptance. Existing users must prove their password and, when enabled, MFA; an
invitation never transfers an account between tenants or grants platform access.

Resend rotates the capability, revocation invalidates it, and expiry is enforced
at every use. Notifications retain the delivery message in an encrypted JSON
container and expose only a safe preview. Delivery checks the current invitation
and token digest so stale queued links are cancelled. Email links carry tokens
in fragments; the acceptance page removes the fragment before submitting it.
Acceptance issues no authentication tokens and directs users through normal login.

The existing notification row is the durable delivery work item. Broker dispatch
occurs after commit; pending deliveries can be recovered by the notification worker.
