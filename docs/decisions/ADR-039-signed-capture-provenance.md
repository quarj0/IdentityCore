# ADR-039: Signed capture provenance and replay signals

Status: Accepted

Capture receipts bind the server-validated media digest to its tenant, case, session,
upload, purpose, server timestamp, and a bounded client-reported capture method.
Receipts are signed with a purpose-separated Django signing key. Client assertions
remain explicitly untrusted: a browser camera, virtual camera, or uploaded file
cannot prove physical presence. Existing randomized active-liveness challenges and
PAD remain the controls for presence and media injection.

Newly completed uploads carry receipts. Legacy uploads remain usable and are
reported as unverified rather than silently attested. Invalid receipts prevent
submission. Identical validated media in another retained case in the same tenant is
flagged without exposing the other case or digest. Retries of the same upload
remain idempotent. Replay and unverified-source signals are available to reviewers;
these signals alone do not override configured biometric decisions.

The portal records camera, live recording, and file fallback separately. Unsupported
image capture can use a file with its provenance explicitly marked; unsupported
active video capture continues through the one-time device handoff, never through
an uploaded recording presented as a live challenge.
