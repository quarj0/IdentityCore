# Historical review audit (#281)

The disposition register tracks each review thread by original PR, comment and thread identifier. A resolved GitHub thread does not establish that a finding was implemented. Each completed disposition cites current implementation and regression evidence; `pending` entries remain open audit work.

This register currently includes 754 threads collected from closed or merged pull requests, extending the original 484-thread issue scope to include subsequent feedback. This initial remediation batch covers OCR outage review gates, biometric evidence promotion, submitted-review expiry and MRZ issuer country binding. It also records earlier MFA and session remediation evidence. Remaining entries are deliberately pending until individually verified.

For each remediation PR, pass CI and security, inspect all review threads, implement valid late feedback, reply with evidence, and refresh the thread list immediately before merging. Do not close #281 while pending dispositions or actionable findings remain.

The current inventory includes the storage reviews from merged #360 and #362. Five older HTTP adapter findings have current-main implementation and validation evidence from the 23-test secure HTTP adapter suite. The full audit remains incomplete.
