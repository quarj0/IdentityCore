# ADR-020: Require independent approval for high-risk decisions

## Status

Accepted

## Decision

Manual decisions for high or critical risk cases, and cases explicitly marked
by policy, are stored as pending approvals. The maker is assigned to the case
but cannot approve it. A different eligible reviewer atomically approves or
rejects the proposed outcome, transitions the verification, and creates an
audit event.

Lower-risk cases retain the existing single-reviewer path unless policy
requires maker-checker approval.
