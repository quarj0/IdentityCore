# Organization invitations

Organization administrators with `manage_team` can invite members, resend an
unaccepted invitation, or revoke it at `/team/invite`. A role may grant only
permissions the administrator currently holds. Invitations expire after seven
days; resending rotates the token and restores an expired invitation. Accepted
or revoked invitations cannot be resent. An expired invitation does not block
creating a replacement.

Configure `TEAM_INVITATION_BASE_URL` to the dashboard HTTPS
`/accept-invitation` URL and configure the notification email provider. The URL
must have no user information, query or fragment. HTTP is allowed only in debug
development. Delivery is queued after the domain transaction commits. Pending
notification rows survive broker outages and are processed by the notification
worker. Failed delivery requires resending the invitation; it does not grant
membership. Stale queued links are cancelled. Delivery secrets are encrypted at
rest, absent from notification previews and API responses, and cleared when
delivery succeeds, fails or is cancelled.

Acceptance links use fragments so capabilities do not enter HTTP access logs.
The page clears the fragment before submitting the token. A new recipient chooses
a strong password. Existing recipients enter their current password and MFA or
recovery code when enabled; they must already belong to the same organization.
Acceptance never transfers accounts, overwrites an existing password, grants
platform access or returns authentication tokens. Users sign in through the
normal MFA-aware login flow afterward.

Internal dashboard endpoints are `GET/POST /api/v1/auth/team/invitations`,
`POST /api/v1/auth/team/invitations/{id}/resend`, and `/revoke`. Anonymous
acceptance uses `POST /api/v1/auth/team/invitations/accept` with `token`,
`password`, and optional `mfa_code`. These dashboard endpoints are outside the
public partner SDK contract. Foreign and unknown invitation IDs both return 404.
Creation, resend, revocation and acceptance produce audit events without tokens.
