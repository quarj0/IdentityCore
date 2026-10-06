# Historical review audit (#281)

The disposition register tracks findings by original PR, comment and thread identifier. A resolved GitHub thread does not establish that its finding was implemented. Completed dispositions cite inspected implementation and regression evidence.

The register includes 759 threads from closed or merged PRs: 40 fixed, 88 verified, 9 actionable and 622 pending individual audit. It extends the original 484-thread scope with subsequent closed-PR feedback. The original issue remains open.

Merged remediation covers OCR outage gates, biometric evidence promotion, submitted-review expiry, MRZ issuer matching, provider attempt/evidence invariants, single-variant OpenCV runtime and authenticated immutable audit records. Current-main validation also covers redaction, secure HTTP adapters and webhook outbox/claim/disable/replay behavior. The remaining parser fixes and delivery-time webhook environment check are tracked in PRs #365, #370 and #372.

For each remediation PR, inspect all review threads, implement valid late feedback, reply with commit and validation evidence, request a fresh final-head review, and require successful CI/Security. Refresh threads immediately before merging. Do not close #281 while pending dispositions or actionable findings remain.
