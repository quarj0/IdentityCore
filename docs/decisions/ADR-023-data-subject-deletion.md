# ADR-023: Pseudonymize data-subject deletion while preserving required audit facts

## Status

Accepted

## Decision

Data-subject deletion requires explicit confirmation and the tenant
`manage_subject_privacy` permission, rechecked when the transaction runs. An
active tenant or verification legal hold defers the request and reports each
hold reason.

When allowed, the workflow pseudonymizes the subject profile, document
metadata, verification metadata, and decision inputs while preserving stable
public identifiers, verification outcomes, and tamper-evident audit facts.
Sessions are revoked, unfinished jobs exhausted and unfinished cases cancelled before
commit. Verification references, provider result copies and generated subject exports
are scrubbed; late workers cannot restore results. Opaque report pointers remain
tracked for retention cleanup. Raw evidence remains governed by retention. See the
[privacy procedure](../operations/subject-privacy.md) for retained categories and
remaining notification/report-object cleanup work. The API
returns a completion report listing anonymized and retained categories.
