# ADR 055: Per-session BFF credentials and retryable exchange

Status: Accepted

A portal-wide token/ID cookie pair made concurrent verification tabs overwrite each
other. The BFF now selects a session-specific host-only HttpOnly bearer cookie by
a validated public session ID header and hashed cookie-name suffix. URL/session
mismatches fail closed; clearing a session deletes only its own cookie. Handoff
uses the same mechanism and never returns its bearer to browser JavaScript.

Credential exchange keeps the link fragment until confirmed success and coalesces
duplicate initialization. Failures remain retryable without browser token storage.
Old global cookies are retired rather than used as a fallback. See the
[cutover and verification guide](../operations/portal-sessions.md).
