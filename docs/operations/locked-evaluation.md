# Locked evidence evaluations

Run `python tools/evaluation/evaluate.py /private/evaluation/manifest.json --report /private/evaluation/report.json`.
Exit 0 means every locked gate passed, 1 means a metric failed a gate, and 2 means
invalid inputs or a hash/lineage mismatch. CI runs only synthetic harness fixtures;
those tests do not certify a production model or commit biometric samples.

Keep consented datasets, labels, model artifacts, predictions and manifests outside
the repository. Control access, environment/purpose, retention and transfers under
the records-of-processing inventory. Review and lock the manifest before running
inference on the held-out dataset. Predictions alone cannot prove which model ran;
retain the approved inference job provenance and artifact hashes alongside the
report. Never tune thresholds on the locked holdout. A new model, dataset, gate,
or threshold requires a new approved lock and repeatable evaluation.

The manifest has `evaluation_version: "1"`, a slug `dataset_version`, and exactly
four `tasks`: `liveness`, `face_match`, `document_authenticity`, and `ocr`. Each task
has a slug `model_version`, `model`, `dataset`, `predictions`, `threshold`, and
`gates`. Each file lock is `{ "path": "relative-private-file", "sha256": "64 lower-case hex digits" }`.
Paths must resolve inside the manifest directory, including through symlinks.

Binary datasets contain `{ "id": "private-pseudonym", "label": true|false }`
rows. Positive means genuine/live, a matching pair, or authentic respectively.
Prediction envelopes contain `model_sha256`, `model_version`, `dataset_sha256`,
and `rows` with matching unique IDs and finite `score` values in [0,1]. A score
at or above the locked threshold accepts the positive hypothesis. Both classes
must be represented. Gates require minimum `precision`/`recall`, maximum
`false_accept_rate`, `false_reject_rate`, and `error_rate`, all in [0,1].

OCR datasets and prediction rows use `text` instead of `label`/`score`;
`threshold` must be null. Gates require minimum token `precision`/`recall` and
maximum `character_error_rate`/`word_error_rate`. Character and whitespace-token
Levenshtein distances are micro-aggregated without implicit normalization;
precision/recall use multiset token overlap. Empty predictions are allowed, but
the reference dataset must have characters and words. Version any desired OCR
normalization upstream as part of the locked dataset/predictions.

Reports contain hashes, versions, sample counts, thresholds, gates, confusion
counts and aggregate error rates, without private IDs or reference/predicted text.
The same locked inputs produce the same report. Set release gates from the
approved risk appetite and cohort requirements; use separate locked evaluations
for cohorts and attack families, and retain uncertainty/sample-size analysis in
the model review. The harness bounds JSON, row counts and text lengths and rejects
missing/duplicate IDs, nonfinite scores, unsupported fields, and lineage drift.

OCR disagreement comparisons are capped at 20 million aggregate character/token
edit-distance cells before any distance calculation. Exact matching strings use
a constant-result fast path. Split larger approved evaluations into locked cohorts;
retain their separately locked aggregate reports rather than raising the runtime
bound silently. Every gate is validated before pass/fail aggregation.
