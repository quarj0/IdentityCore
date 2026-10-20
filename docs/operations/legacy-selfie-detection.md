# Legacy selfie detection evidence maintenance

`biometrics.0006_clear_legacy_placeholder_face_counts` adds correction metadata and
repairs unsupported default-one counts. It is a data migration requiring a planned
maintenance/staged release, not an automatic rolling expansion.

Rehearse from an encrypted backup, inspect the `0005` application timestamp and
candidate cohort, and drain/pause affected capture/biometric writes using the normal
[deployment procedure](deployment-rollout.md). Keep a backup and approved migration
record before applying migrations. The repair selects only rows created before
`0005` with face_count=1 and no recorded detection confidence/model attribution.
It sets the current count to null and stores the previous assertion and correction
provenance. It preserves analyzed history, zeros and later records, including
soft-deleted records' retained correction provenance.

Verify candidate/corrected counts, inspect synthetic report JSON/PDF and confirm
that unmeasured detection is unavailable rather than reported as one face. This
maintenance operation does not regenerate stored report objects or modify audit
records. Subsequent report-generation calls include the current observations and
explicit correction metadata. The
migration is idempotent; a retry does not replace existing correction timestamps.
The populated pre-0005 migration regression exercises this boundary.

Resume only after the normal readiness/evidence checks. Code rollback keeps the
expanded schema and correction metadata; do not down-migrate to restore unsupported
counts or remove the correction history. Recovery that changes historical assertions
requires an explicit reviewed correction or approved backup restoration.
