# API usage quotas

Authenticated REST API clients reserve one request after authorization and before
executing the endpoint. PostgreSQL serializes reservations on an organization and
environment quota row, so every process shares atomic organization minute/month
and client minute counters. A failed limit increments denials without consuming
admitted capacity in any window. Database failures fail the request closed; the
service does not silently switch to process-local counters. Dashboard JWT and
verification-session traffic retain their separate existing throttles. GraphQL
currently supports dashboard JWT authentication, so it does not admit API-client
traffic and cannot bypass these REST quotas.

Minute windows and calendar months use UTC, including year boundaries. A client
without a project uses sandbox. Production and sandbox have separate quotas and
counts. Organization defaults are 6,000 requests/minute and 1,000,000/month;
each client's stored `rate_limit_per_minute` is also enforced. Operators set the
organization/environment `APIUsageQuota` limits through controlled database/admin
configuration. Zero disables admissions. Set deployment limits from measured
capacity, contracts and risk appetite; counters survive configuration changes.

Responses include `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and
`X-RateLimit-Reset` (UTC epoch seconds) for the limiting window, plus
`X-RateLimit-Environment`. Explicit headers show
`X-RateLimit-Organization-Minute-Limit/Remaining`,
`X-RateLimit-Organization-Month-Limit/Remaining`, and
`X-RateLimit-Client-Minute-Limit/Remaining`. A 429 includes `Retry-After` in seconds,
covering every exhausted window. Remaining capacity is a snapshot; other requests
may consume it immediately. Authorized CORS callers can read these headers.
Counts include every admitted request, including later 4xx/5xx results and
idempotent replays, and exclude rejected credentials/authorization and OPTIONS.
Quota-related responses use no-store.

The dashboard **API usage** page shows only the authenticated user's organization,
with independent sandbox/production admitted/denied counts, limits, remaining
capacity and reset times. The internal usage endpoint accepts no tenant selector;
API credentials and platform administrators cannot use it. Counters contain no
request paths, subject identifiers, credentials, or evidence. A retention worker
purges expired aggregate/client window rows after 90 days. Monitor quota-row lock
latency when selecting production throughput and partition the service if needed;
shared database enforcement intentionally favors correctness.
