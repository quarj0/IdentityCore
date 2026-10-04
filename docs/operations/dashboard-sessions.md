# Dashboard devices and sessions

Tenant account owners review recent sessions in Settings → Security. A session belongs
to one account and application scope. The list exposes only a coarse browser/OS
label, masked IPv4 /24 or IPv6 /48 network, timestamps and revocation state.
Raw user agents, IP addresses, JWTs and refresh family identifiers are not stored
in this session record or returned by these endpoints. Existing audit records
retain their separately governed request metadata.

Sign out a device to revoke its access and refresh credentials immediately in
REST and GraphQL. Sign out other sessions preserves the current session.
Changing or resetting a password, resetting MFA, logout and signed refresh replay
revoke the affected sessions. Credential changes require a new sign-in. Current
account, organization and MFA policy are checked on authenticated requests and
refresh, including roles promoted after the original sign-in.

Older signed refresh credentials migrate into an owned session on first refresh.
A scoped client without its scoped cookie may migrate the previous shared cookie;
an invalid scoped cookie never falls back. The migrated shared cookie is cleared.
Legacy access credentials expire within the configured access lifetime (default
five minutes), and any credential change or session revocation invalidates them.

Hourly `accounts.purge_session_history` removes up to 1,000 expired refresh rows
and up to 1,000 session records expired more than 90 days ago. Monitor the Celery
retention queue and schedule; the application does not retain an unbounded token
rotation history. Retention does not delete active credentials. The same job removes up to 1,000 expired SimpleJWT outstanding records
and their blacklist entries.

The browser list is capped at the most recently active 100 records. The bulk
revocation action operates on every owned session, including older records.
Database failures during logout return an error rather than claiming revocation
succeeded. Retry once the database has recovered.
