# ADR-012: Scope verification session tokens

## Status

Accepted

## Decision

Every verification portal session token is bound to one `VerificationSession`.
The request must provide that session's public ID and bearer token; the token is
stored only as a password hash and is rejected when the session is expired,
revoked, or completed.

Each session also carries an explicit allowed-action set. Portal endpoints
require the action appropriate to the operation, such as `document:capture`,
`liveness:submit`, or `upload:transfer`. A token therefore cannot be reused to
perform a different operation or against another session.

## Consequences

Session issuers must populate the action set when creating a session. Existing
sessions are backfilled with the complete set during migration so they remain
compatible while the new restriction is introduced. Future issuers should
grant only the actions required by the flow.
