# Document authenticity and reviewer annotations

Authenticity is independent from quality, classification, and OCR. Opt in with
`document_authenticity_required` and a snapshotted minimum confidence (0–1).
A completed, authentic result above that threshold with no suspicious regions
can continue; suspicious, unavailable, malformed, low-confidence, and inconclusive
results require manual review. Favorable biometrics cannot override that review.
Existing workflows remain compatible when the capability is disabled.

Configure and assign `document_authenticity` for the appropriate environment using
a document provider. The provider operation receives the authorized document
storage reference and EXIF-oriented source dimensions. The managed adapter returns
explicit uncertainty because no calibrated authenticity model ships in this
repository. Deployments must evaluate their model before enabling automatic
continuation; use the locked evaluation harness and private approved datasets.

Contract v1 requires contract/capability/status/authenticity versions, verdict,
finite confidence, bounded model name/version, source and analysis dimensions,
an invertible six-element affine analysis-to-source transform, at most 20 regions,
and a bounded JSON raw-output object. An analysis box is `[x,y,width,height]`;
`[a,b,c,d,e,f]` maps `(x,y)` to `(a*x+b*y+c,d*x+e*y+f)`. All four corners must
land within the original source. Core verifies source dimensions against the
owned, live capture, maps boxes to normalized source coordinates, and accepts
only copy-move, resampling, text inconsistency, portrait editing, and template
inconsistency reasons. Negative, nonfinite, oversized, degenerate, and unknown
annotations fail the provider contract before persistence.

Raw output, normalized evidence, provider checks, model versions, and transforms
remain in encrypted evidence and decision lineage under normal retention/deletion.
Reviewer APIs reuse manual-review tenant/platform ownership authorization and
exclude raw output. Preview requests recheck ownership and deletion, bound image
bytes/pixels, apply EXIF orientation, remove metadata, and return a limited JPEG
preview. Responses use `Cache-Control: no-store`; access is audited without image
bytes or model output. Preview data URLs render under the existing strict CSP.
Reviewers can toggle SVG overlays and inspect the reason/confidence legend.
Annotations assist a human decision; they do not independently approve a document.
