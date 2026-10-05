# Reviewer reason codes and notes

Draft verification policies accept `review_reason_rules`. New cases snapshot the rules; subsequent policy edits do not alter an existing case. Empty rules allow legacy plain-text reviewer submissions but expose no manual reason through the public result contract.

```json
{
  "version": 1,
  "outcomes": {
    "verified": {"codes": ["evidence_confirmed"], "notes_required": false},
    "rejected": {"codes": ["evidence_mismatch"], "notes_required": true},
    "failed": {"codes": ["evidence_unavailable"], "notes_required": true}
  },
  "organization_facing_codes": ["evidence_confirmed", "evidence_mismatch"]
}
```

Submit `decision`, `reason_code` and optional `reason_detail` to `/api/v1/verifications/manual-reviews/{id}/decision`. Codes must be lowercase machine identifiers, at most 80 characters, drawn from the chosen outcome's catalog. Notes are at most 4000 characters of plain text. HTML, encoded markup and control characters are rejected. Required notes cannot be replaced with an automatic UI placeholder. The dashboard offers the configured catalog and requires notes according to the selected final outcome.

For maker/checker cases, `/manual-reviews/{id}/approval` accepts the same fields. A configured policy requires the checker to choose a code appropriate for their own final outcome and provide their own required notes. The maker cannot approve their own decision. Empty legacy rules retain approval compatibility with a generated manual outcome code. Checker notes remain auditable in encrypted sensitive audit metadata.

Public `/verifications/{id}/result` responses expose only configured organization-facing manual codes, never reviewer notes. Keep codes generic, never embed applicant identity, contact information, document numbers, or provider payloads. Automatic decision reasons retain their existing fixed allowlist. Invalid stored rule objects fail review validation and expose no manual codes in public results.

The nullable policy column supports additive rollout; existing null rows serialize as empty rules. APIs and all four generated SDK model sets include the policy configuration and checker reason fields.
