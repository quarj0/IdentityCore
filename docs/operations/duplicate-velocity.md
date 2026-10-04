# Duplicate and velocity evidence

Policies accept optional `reuse_rules`; `{}` disables matching and writes no
fingerprints. Example configuration:

```json
{"version":1,"scope":"tenant","retention_days":7,"window_minutes":60,
 "thresholds":{"document":2,"portrait":2,"device":5,"network":20},
 "action":"manual_review"}
```

`scope` is `tenant` or `global`; action is `flag` or `manual_review`. Thresholds
range from 2 to 1000 and include the current case. Document and exact portrait
media matching cover retained fingerprints; device and network velocity cover
case creation times inside the configured window. Missing inputs are reported,
never replaced with a universal empty fingerprint. Shared devices, virtual cameras,
client-reported device identifiers and NAT/proxy networks remain weak evidence.
Portrait reuse means identical submitted media, not a biometric identity search.

Fingerprints are HMAC-SHA256 with purpose, kind, environment and scope separation.
Set `REUSE_SIGNAL_HASH_KEY` to an independently managed secret or use the Django
secret fallback. Key changes reset correlation naturally; previous fingerprints
expire without rehashing raw values. A network fingerprint uses an IPv4 /24 or
IPv6 /48 prefix from the session's observed peer address. An untrusted forwarded
header does not create a trusted network identity. Reports contain only fixed
threshold flags and unavailable kinds, without peer identifiers, hashes or counts.

Global matching requires `GLOBAL_REUSE_SIGNALS_ENABLED=true` and global scope on
both participating case policy snapshots. Private tenant fingerprints never enter
global matching; production and sandbox remain separate. Configure this optional
fraud purpose within the organization's data processing and consent controls.
When global matching is requested but unavailable, the case routes to review.

Retention is at most 90 days and is capped by metadata retention (and media retention for document/portrait),
anchored to case
creation. Retrying an assessment does not extend it. Minute-based bounded cleanup removes
expired indexes. Subject erasure removes the indexes immediately when erasure is
allowed; erased subjects cannot recreate them. Media cleanup removes document and
portrait indexes. A legal hold on evidence does not prolong these ephemeral fraud
indexes past their configured TTL.

PostgreSQL transaction locks serialize matching fingerprints before writes and
reads. Each case has one indexed observation per configured kind, preventing retries
from increasing counts. A rejection from existing evidence remains a rejection;
these signals can flag or require review but cannot automatically reject a subject.

Collection and erasure share a subject advisory lock. Erasure takes that lock after
its existing metadata/parent updates, and removes fingerprints before commit.
Collection rechecks erasure in the database after acquiring the lock, including
when its verification carries a previously cached subject. Cleanup runs every
minute with `REUSE_CLEANUP_BATCH_SIZE` (1..10000, default 1000); remaining expired
rows schedule another bounded batch after one second. Beat retries drainage after
a broker outage, and expired indexes are excluded from matching immediately.
