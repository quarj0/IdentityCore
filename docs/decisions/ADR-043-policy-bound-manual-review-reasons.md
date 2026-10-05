# ADR 043: Policy-bound manual review reasons

Status: Accepted

Manual review reason catalogs and required notes are captured in each verification's immutable policy snapshot. Draft policies configure outcome-specific codes and note requirements, plus an explicit allowlist of codes safe for organization-facing results. Reviewer notes remain internal and are not copied to result payloads. A checker must satisfy the same rules for their final outcome rather than inheriting the maker's code when disagreeing.

A version-one rules object has `outcomes` entries for verified, rejected and failed, each containing a bounded non-empty `codes` list and a boolean `notes_required`, and `organization_facing_codes`. Codes are machine identifiers with lowercase letters, digits and underscores. Notes are bounded plain text; markup, encoded markup and control characters are rejected. Empty rules preserve existing valid plain-text reason submission but expose no unapproved manual reason through organization-facing results.

Validation applies after the verification row lock, using its snapshot, and before assigning the reviewer or mutating decisions. REST and GraphQL policy contracts share model validation. Audit records keep notes in encrypted sensitive metadata and result serialization publishes only allowlisted manual reason codes. Existing automatic reason contracts remain unchanged.
