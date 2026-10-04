# ADR-035: Dashboard session ownership and revocation

Status: Accepted

Each first-party login creates a durable session owned by one user and refresh
family. Access and refresh JWTs identify that session; REST and GraphQL use the
same authentication boundary to check revocation, expiry, account/tenant status,
password binding and current MFA policy. Token rotation retains the session and
registers each successor as outstanding. User-row locking serializes refresh,
session revocation and sensitive credential changes. Audit-producing changes
acquire the tenant audit lock before the user lock to preserve lock ordering.

Tenant dashboard users can list their own sessions, revoke one session, or revoke all others.
Metadata consists of a bounded browser/OS label and a masked peer network; claimed
forwarded headers and arbitrary user-agent strings are not retained. Tokens,
JTIs and raw IP addresses are never exposed by these endpoints.

Valid legacy refresh tokens migrate to tracked sessions after signature, expiry,
blacklist, ownership and current MFA validation. Legacy access tokens are accepted
only during their existing five-minute lifetime and are invalidated by any user
revocation or sensitive credential change. New session JWTs are invalidated
immediately when their session is revoked. Expired refresh history is purged, and
revocation bulk-blacklists only currently live outstanding tokens.
