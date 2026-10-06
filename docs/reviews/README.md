# Historical review audit (#281)

The disposition register tracks findings by original PR, comment and thread identifier. A resolved GitHub thread does not establish that its finding was implemented. Completed dispositions cite inspected implementation and regression evidence.

The register includes 762 threads from closed or merged PRs: 52 fixed, 139 verified, 19 actionable and 552 pending individual audit. It extends the original 484-thread scope with subsequent closed-PR feedback. The original issue remains open.

Merged remediation covers OCR outage gates, biometric evidence promotion, submitted-review expiry, MRZ issuer matching, provider attempt/evidence invariants, single-variant OpenCV runtime and authenticated immutable audit records. Current-main validation also covers redaction, secure HTTP adapters and webhook outbox/claim/disable/replay behavior. Delivery-time webhook isolation and controlled provider-health codes are merged in #370 and #372. Additional validation covers decision locks, external-risk I/O, authenticity redaction, retention holds and deferred evidence generation. System fallback contract fixes are merged in #373. Remaining parser fixes are tracked in #365. The independent SDK/idempotency audit verifies existing signing, replay, profile, retry and compiler behavior, and tracks live project/example, completion/type and conformance fixes in #375–#377.

For each remediation PR, inspect all review threads, implement valid late feedback, reply with commit and validation evidence, request a fresh final-head review, and require successful CI/Security. Refresh threads immediately before merging. Do not close #281 while pending dispositions or actionable findings remain.
