# Internal liveness data and evaluation

This document defines the minimum evidence required before IdentityCore treats
the internal liveness/PAD engine as pilot-ready. It is not permission to collect
biometric or identity-document data without an approved legal and privacy
process.

## Data streams

Keep these datasets separate:

1. **Face PAD:** consented live and presentation-attack face videos. Labels must
   include attack type, device, browser, lighting, capture format, frame rate,
   locale, and challenge actions.
2. **Document capture:** Ghana passport and Ghana Card capture examples for
   quality, layout, MRZ, portrait extraction, and tamper detection. Use
   redacted or synthetic documents wherever possible.
3. **Face match:** consented document-portrait/selfie pairs with match,
   non-match, and inconclusive labels. This is not a substitute for PAD data.

Public research datasets such as CelebA-Spoof, OULU-NPU, and SiW require a
licence review before any commercial use. Their research results must not be
represented as IdentityCore production performance.

## Controlled Ghana capture study

The study must use written consent, a documented purpose, retention period,
access list, deletion process, and a Ghana Data Protection Commission review by
the accountable privacy owner. Do not collect passport numbers, Ghana Card PINs,
MRZ strings, addresses, signatures, or raw document images in chat or ordinary
developer storage.

For each volunteer, collect multiple live sessions across supported phones,
browsers, lighting conditions, distance, orientation, and network quality. Each
attack session must be labelled and performed with approved disposable test
materials: printed photo, screen replay, recorded video, glare, partial
occlusion, and injection/virtual-camera attempts where the test environment
permits.

## Evaluation gate

Split by person, not by frame: training, validation, and held-out test subjects
must never overlap. Freeze thresholds on validation data before running the
held-out test. Report APCER, BPCER, ACER, false accept rate, false reject rate,
inconclusive rate, p95 latency, and results by device, browser, locale,
lighting, and demographic cohort.

The held-out report must show that:

- real-mode inference uses the approved PAD model and checksum-listed artifact;
- mock or hybrid fallback is impossible in production;
- active challenge replay and duplicate submission fail closed;
- uncertain results become manual review, never automatic approval;
- the security, privacy, and product owners accept the residual risk before a
  limited pilot.

The first approved model must be packaged as
`AI_MODEL_ROOT/liveness/pad.onnx` and recorded in `manifest.json`. Runtime
downloads are prohibited.

The first country matrix is Ghana, Nigeria, Senegal, Togo, and Côte d’Ivoire.
The PAD model is shared across this matrix, but evaluation results must be
reported separately for each country. Passport support does not imply support
for that country’s national ID; national-ID enablement requires separate,
lawfully obtained document fixtures and tests.
