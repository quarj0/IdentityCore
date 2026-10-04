# One-time mobile handoff

A desktop session creates a QR/deep-link claim with a maximum lifetime of five
minutes, capped by both session and verification expiry. Creating another QR
invalidates every pending claim from that source. Only one concurrent redemption
can issue a mobile session, and concurrent creation leaves one live claim.

The claim travels in `#handoff=...`, never a URL query. The portal clears the
fragment before making a redemption request. It sends both the claim and the
source `session_id`; a claim presented for another source fails without consuming
it. Older query-based links require a new QR. Direct redemption callers must
include `session_id` with the handoff value.

The mobile session has a fresh bearer credential and inherits only the source's
current permitted actions. Expired, revoked, terminal, suspended or deleted
sources cannot create mobile credentials. Successful redemption sets the portal's
secure HttpOnly cookie; the browser response never contains the bearer token.
The claim does not enter browser storage, server-rendered props or audit metadata.

Desktop polling retains its own session cookie and reads case status after mobile
progress. The source bearer never enters the QR, copyable URL, logs or DOM.
Clearing the mobile fragment leaves a safe session URL for reload/resume.
Redemption failure requires a fresh QR; it cannot replay an already consumed claim.
Anonymous redemption is rate limited and inputs are bounded before password-proof
verification. Browser and PostgreSQL concurrency regressions cover these paths.

Verified server-generated 256-bit handoff grants use individual throttle buckets,
so a shared portal BFF address cannot exhaust the allowance for other valid grants.
Invalid guesses use a separate peer-address bucket. Client-supplied session IDs,
handoff IDs, and forwarded addresses cannot select an independent bucket without
proving possession of a live grant. Older password-hashed grants use the invalid-
attempt bucket; regenerate previously issued links during this rollout.
