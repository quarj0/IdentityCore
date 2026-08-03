# ADR-019: Claim manual reviews atomically

## Status

Accepted

## Decision

Manual review access is restricted by review owner and tenant scope. The first
eligible reviewer to submit a decision atomically claims an unassigned case;
subsequent reviewers cannot decide a case assigned to someone else. The claim
and final decision occur under the same row lock and assignment is recorded in
the audit stream.

This preserves an unassigned queue while preventing concurrent or unauthorized
review decisions and keeps platform-owned review cases separate from tenant
review work.
