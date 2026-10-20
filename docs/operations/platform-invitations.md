# Platform administrator invitations

Platform invitations grant **full platform administration**. Limited/read-only
platform roles are not enforced and are therefore rejected for new invitations.
Existing unsupported pending roles must be revoked/reissued as an explicit full-admin
invitation; they cannot be accepted. Tenant team invitations remain separate.

Install `notifications.0003` before deploying. It permits platform-scoped notification
rows only for the platform invitation email template; the database rejects arbitrary
null-tenant notifications. Configure deployment email settings and
`PLATFORM_INVITATION_BASE_URL` as the public HTTPS platform-admin `/accept-invitation`
page, without credentials, query or fragment. Local HTTP is allowed only in DEBUG.

The invitation mutation validates the address and records an encrypted durable outbox
item in its transaction. Dispatch occurs after commit. The UI reports queued delivery,
not confirmed arrival. The notification worker uses deployment email configuration,
never a tenant's provider/credentials. Pending rows survive broker publication failure.
Delivery revalidates invitation status, expiry, token, role and inviter authority.
Stale work is cancelled; credentials are cleared after sent, failed or cancelled delivery.

Use notification status to diagnose delivery. After a terminal delivery failure, inviting
the same address again revokes the old pending invitation and issues a fresh token/outbox
item under the platform lock. An undelivered pending outbox does not permit duplicate
invites. Old links remain invalid after replacement. Do not copy tokens into support or
audit records; ordinary previews contain no invitation capability.

Links carry the token in a fragment so it is not sent in the page request. The public
acceptance page clears the fragment and submits the token only in its API request body.
Acceptance validates current role/inviter authority, consumes the credential once and
records a platform audit event, including when MFA setup is required. The recipient
continues through normal MFA-aware sign-in. The page does not persist auth tokens.

Acceptance requires the deployed platform-admin origin in the backend's trusted cookie
origin allowlist. Keep the notification recipient, expiry, role and delivery configuration
under least privilege; exercise a synthetic invite/accept flow before release.
