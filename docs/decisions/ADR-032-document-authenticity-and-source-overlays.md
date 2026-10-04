# ADR-032: Versioned authenticity evidence and source-coordinate overlays

Status: Accepted

## Context

Authenticity requires its own provider capability and policy semantics. Vendor
analysis may crop, resize, rotate, or reflect an image, while reviewers see the
original document. Unbounded coordinates and raw model output are unsuitable for
a review surface.

## Decision

Add document_authenticity throughout provider taxonomy, contracts, assignments,
routing, policy snapshots, processing, risk, and review. Validate finite bounded
boxes and an invertible affine mapping against core-read EXIF-oriented source
dimensions; persist source-normalized boxes, model versions, transform and raw
output in encrypted evidence. Expose only bounded normalized annotations to
reviewers, with audited authorized previews and no-store responses. Use SVG
numeric attributes to preserve CSP and overlay alignment without inline styles.

Require review for uncertainty or suspicious regions. Keep the capability opt-in
for existing policy versions. The managed implementation reports unavailable
until a calibrated model exists; external deployments must evaluate their model.

## Consequences

Provider contracts explicitly carry geometry and lineage. Preview reads incur
bounded image processing. No uncalibrated model can masquerade as affirmative
authenticity evidence, and decision snapshots preserve why review was required.
