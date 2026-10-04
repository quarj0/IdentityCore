# Machine-readable document zones

The real OCR pipeline parses ICAO 9303 TD1 (three 30-character lines), TD2 (two
36-character lines), and passport TD3 (two 44-character lines). It validates the
allowed alphabet and document number, birth, expiry, optional-data (TD3), and
composite check digits. A checksum is structural evidence and cannot prove a
document authentic or determine a business outcome.

Every result contains `mrz_evidence` with format, explicit `valid`, `invalid`,
`unsupported`, or `absent` status, fixed issue codes, individual checksum results,
and rule version `icao-9303-v1`. Extended document-number encodings and visa MRZs
are explicitly unsupported. Malformed recognized layouts are invalid.

Fields carry the source format, rule version, OCR line index, and start/end offsets
in the normalized uppercase line with whitespace removed. Names and identifiers
remove filler characters. Date fields retain their six-character MRZ encoding,
including unknown positions; resolving a century and document policy is separate
from checksum validation. Valid MRZ document numbers replace heuristic OCR
numbers, and `mrz_fields` retain their provenance. Invalid evidence never replaces
a heuristic field with an unverified MRZ value.

The result and provenance persist in the existing encrypted document extraction
and provider-check evidence. Public verification result summaries remain redacted.
MRZ lines and extracted identity fields must not be included in operational logs
or exception messages. All fixtures use ICAO example identities.
