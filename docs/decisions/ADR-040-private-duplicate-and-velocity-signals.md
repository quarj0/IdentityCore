# ADR-040: Private duplicate and velocity signals

Status: Accepted

Policies configure tenant or mutually opted-in global matching, thresholds, action,
velocity window, and fingerprint retention. The default is disabled. Fingerprints
are purpose-separated keyed HMACs; document numbers, exact selfie media digests,
client-reported device identifiers, and coarse network prefixes never enter reports.
Environment boundaries apply in both scopes. Global matching additionally requires
an operator enablement flag and returns threshold flags without peer counts or IDs.

Document and exact portrait-media reuse use the configured retention horizon;
device and network velocity use case creation times inside a configurable window.
Signals are advisory or require manual review; they cannot automatically reject a
person or assert that two portraits identify the same individual. Client device
claims and shared networks are explicitly weak evidence.

Fingerprint writes are idempotent per case and kind. PostgreSQL transaction locks
serialize matching fingerprints so simultaneous cases cannot both miss the signal.
Expiry is anchored to case creation and never extended by risk reevaluation. The
retention worker drains expired fingerprints in bounded continuing batches; subject erasure removes them
immediately unless a legal hold defers erasure. Media cleanup removes media-derived
fingerprints. New matching excludes erased cases and subjects.

Collection and erasure share a subject advisory lock. Erasure takes that lock after
its existing metadata/parent updates, and removes fingerprints before commit.
Collection rechecks erasure in the database after acquiring the lock, including
when its verification carries a previously cached subject. Cleanup runs every
minute with `REUSE_CLEANUP_BATCH_SIZE` (1..10000, default 1000); remaining expired
rows schedule another bounded batch after one second. Beat retries drainage after
a broker outage, and expired indexes are excluded from matching immediately.
