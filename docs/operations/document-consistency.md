# Country-aware document consistency signals

Policy creation accepts `document_consistency_rules`. Draft policy edits and
cloning preserve it; each verification snapshots the complete configuration so
subsequent policy edits cannot alter an in-flight case. Version 1 supports ISO
country keys and `*` as a default. A country entry replaces the default entry.

```json
{"version":1,"countries":{"GH":{"minimum_age":18,"maximum_document_years":10,"expiry_grace_days":0,"actions":{"document_expired":"reject","document_age_below_minimum":"manual_review","document_birth_date_ambiguous":"manual_review","document_birth_date_unavailable":"manual_review","document_birth_date_mismatch":"manual_review","mrz_country_mismatch":"manual_review"}}}}
```

Rules generate expiry, future issue/birth, date ordering, maximum validity,
minimum age and cross-field consistency signals. Age uses the exact birthday;
February 29 birthdays advance on March 1 in a non-leap year. Expiry remains valid
through its stated day, plus any configured grace. Evaluation uses a UTC date.
Country rules are customer policy configuration, not claims about local law.

MRZ two-digit years are interpreted only when exactly one plausible century
exists (birth age 0–120; expiry within 50 years). A matching full subject birth
date may resolve the century. Ambiguous birth dates have no age and emit an
explicit signal. Invalid calendar dates, unknown encodings and unsupported MRZs
cannot establish age from MRZ evidence. A missing age emits
`document_birth_date_unavailable` when a minimum age is configured. Original visual OCR evidence is retained beside
MRZ fields so a normalized replacement cannot hide a cross-field mismatch.

No signal changes a decision by default. Configure each fixed issue code with
`ignore`, `manual_review`, or `reject`. Review actions cannot downgrade an existing
rejection, and rejection takes precedence over review. Invalid persisted rule
configurations require manual review. Rules and their applied versions are
recorded in encrypted risk evidence, without copying names, document numbers or
birth dates into the signal summary or public result projections.

Supported codes: `document_expired`, `document_issue_date_future`,
`document_birth_date_future`, `document_date_order_invalid`,
`document_validity_too_long`, `document_age_below_minimum`,
`document_birth_date_ambiguous`, `document_birth_date_unavailable`, `document_date_invalid`,
`document_birth_date_mismatch`, `document_name_mismatch`,
`document_number_mismatch`, `mrz_country_mismatch`, `mrz_checksum_invalid`, and
`document_rules_invalid`.
