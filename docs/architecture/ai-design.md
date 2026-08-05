# IdentityCore Managed AI Providers

## Purpose

This document defines the AI and computer-vision provider implementations operated by IdentityCore.

The FastAPI AI service is not a privileged architectural subsystem and does not define the platform boundary. It is a host for **IdentityCore Managed Providers** that implement selected capabilities behind the same Provider Runtime used by commercial, government, and customer-hosted providers.

The canonical platform architecture is defined in [`ARCHITECTURE.md`](../../ARCHITECTURE.md). Provider execution is defined in [`provider-runtime.md`](provider-runtime.md), and provider-neutral capability contracts are defined in [`capability-model.md`](capability-model.md).

## Core principle

AI produces evidence, not final organizational decisions.

Managed AI Providers may answer technical questions such as:

- Is a document capture usable?
- Which supported document type best matches the observed evidence?
- What text and structured fields can be extracted?
- Is a usable face present?
- How similar are two face representations?
- Does a presentation appear bona fide or suspicious?
- Which model, threshold, and confidence produced the result?

The Workflow, Policy, and Decision Engines determine what happens next. Uncertain, unsupported, unavailable, or contradictory results may trigger retry, fallback, additional evidence, Manual Review, or a fail-closed outcome.

## Architecture

```text
Workflow Engine
      |
      v
Provider Runtime
      |
      +--> IdentityCore Managed AI Provider
      |       |
      |       +--> Document quality
      |       +--> Document classification
      |       +--> OCR and field extraction
      |       +--> Face detection and comparison
      |       +--> Liveness / presentation attack detection
      |       +--> Model registry and metadata
      |
      +--> Commercial provider
      +--> Customer-hosted provider
      +--> Government or authoritative provider
```

The Django backend must not depend directly on model libraries or provider-specific response shapes. It resolves and invokes capabilities through provider adapters, then stores normalized, versioned evidence.

## Current managed capabilities

The current FastAPI service hosts implementations for:

- `document.quality`
- `document.classification`
- `document.ocr`
- face detection used by biometric workflows
- `biometric.face-match`
- `biometric.liveness`
- presentation attack detection where configured
- model and runtime metadata reporting

Capability availability depends on runtime mode, configured models, object storage, and deployment resources.

## Runtime modes

The service supports:

- `mock` — deterministic development responses without production model assets;
- `hybrid` — real processing where configured, with controlled development fallbacks;
- `real` — configured model and media-processing paths intended for production-like validation.

The legacy `local` value is normalized to `mock` for backward compatibility.

Mock and hybrid modes are development tools. They must not be represented as production model assurance.

## Invocation lifecycle

A managed AI invocation follows the platform runtime:

1. The workflow identifies a required capability.
2. The Provider Runtime resolves the provider assignment.
3. A Provider Check is created or resumed idempotently.
4. IdentityCore grants minimal, time-limited evidence access.
5. The adapter invokes the managed provider.
6. The provider validates media and executes the capability.
7. The response is schema-validated and normalized.
8. Provider, adapter, schema, and model versions are recorded.
9. Sensitive request and response telemetry is redacted.
10. The resulting evidence is consumed by workflow and policy evaluation.

Managed providers must not bypass provider checks, evidence lineage, tenant scoping, or audit requirements.

## Provider responsibilities

Managed AI Providers are responsible for:

- media validation and safe decoding;
- model execution;
- technical scores and observations;
- confidence and quality metadata;
- model name and version;
- processing timestamps and duration;
- deterministic error codes;
- safe handling of unsupported or inconclusive inputs;
- avoiding raw media, embeddings, or sensitive text in logs.

They are not responsible for:

- tenant authorization;
- consent validation;
- final verification decisions;
- business eligibility decisions;
- retention policy ownership;
- Manual Review outcomes;
- webhook delivery;
- provider routing outside their own invocation.

## Document quality

Document quality evaluates whether a capture is suitable for downstream processing.

Potential signals include:

- blur;
- glare;
- cropping;
- low resolution;
- poor lighting;
- obstruction;
- orientation;
- missing corners;
- unsupported format or unsafe content.

A normalized result should include status, quality score, observed issues, model or algorithm version, and whether retry is recommended. Poor quality is evidence about usability, not proof of fraud.

## Document classification

Document classification estimates the supported document family and country from observable evidence.

The current implementation uses OCR line normalization, phrase matching, confidence, structural evidence, country definitions, and MRZ validation where applicable.

Classification statuses should distinguish:

- `recognized`
- `unknown`
- `unsupported`
- `ambiguous`
- `insufficient_evidence`

Low confidence, unsupported documents, or conflicting evidence should not be silently rejected as fraudulent. They should produce explicit evidence and an appropriate workflow action.

Country support is additive and configuration-driven. Core platform logic must not hardcode Ghana-specific labels or require one country's document taxonomy.

## OCR and field extraction

OCR produces extracted text and candidate fields such as:

- name;
- date of birth;
- document number;
- expiry date;
- nationality;
- issuing authority;
- machine-readable zone fields.

OCR output is unverified evidence. It may be wrong, incomplete, or inconsistent. The platform should preserve field-level confidence and provenance, normalize formats, compare corroborating evidence, and avoid exposing sensitive values unnecessarily.

## Face detection and alignment

Face detection determines whether an image contains a usable face and may return bounding boxes, landmarks, pose, quality, and detection confidence.

Face alignment prepares a detected face for comparison. Derived face representations are biometric data and must be protected, minimized, and deleted according to policy.

Public APIs must not expose raw biometric templates.

## Face comparison

Face comparison estimates similarity between two face representations, commonly a selfie and document portrait.

A normalized result should retain:

- similarity score;
- threshold used;
- technical match outcome;
- quality or confidence;
- model and version;
- processing timestamp;
- failure or inconclusive reason.

A technical `matched` result is not equivalent to a final `verified` decision. Face comparison must not be the sole basis for sensitive decisions.

## Liveness and presentation attack detection

Liveness evaluates whether evidence appears to come from a live, present person rather than a replay, print, screen, mask, injection, or generated presentation.

IdentityCore may support:

- passive analysis;
- active challenges such as head movement or other prompts;
- presentation attack detection models;
- capture-provenance and device-integrity signals.

Results should distinguish passed, failed, inconclusive, unsupported, and unavailable states. Accessibility, device quality, demographic performance, and attack-class coverage must be evaluated explicitly.

## Model registry and reproducibility

Every model-backed result should include, where applicable:

- provider ID;
- capability and schema version;
- model name and version;
- model artifact checksum or release identifier;
- runtime mode;
- threshold configuration version;
- processing timestamp;
- duration;
- confidence and quality metadata.

This information supports auditability, debugging, reproducibility, replacement, drift analysis, and incident response.

## Thresholds

Thresholds affecting workflow or decision behavior belong to versioned policy or provider configuration, not undocumented model code.

The exact threshold used must be retained with the result. Different workflows may choose different risk tolerances, but thresholds require representative evaluation and change control.

## Accuracy and claim discipline

IdentityCore must not advertise a general accuracy percentage without a locked, representative, independently reviewable evaluation for the exact provider, model, configuration, country, document type, device conditions, and attack classes.

Performance reporting should identify relevant metrics, including:

- false acceptance and false rejection rates;
- precision and recall;
- calibration;
- latency;
- manual-review rate;
- attack presentation classification error rate;
- bona fide presentation classification error rate;
- OCR field accuracy and character error rate;
- classification accuracy by supported document family.

A narrow, reproducible claim is preferable to a broad marketing number.

## Bias and fairness

Biometric and document models may perform differently across demographics, devices, lighting, geography, and document quality.

Requirements include:

- representative evaluation;
- monitoring for false-positive and false-negative disparities;
- avoidance of face matching as the sole decision factor;
- Manual Review and retry paths;
- accessible active-liveness alternatives;
- documented supported populations and limitations;
- lawful and ethical handling of evaluation attributes.

## Security

Managed AI processing must:

- validate MIME type, extension, size, dimensions, and decoded content;
- quarantine unsafe uploads;
- protect against decompression bombs and malicious documents;
- prevent path traversal and unrestricted network access;
- use short-lived evidence access;
- avoid logging raw media, document numbers, OCR text, or embeddings;
- enforce internal authentication and provider message integrity;
- apply timeout, response-size, and concurrency limits;
- isolate model execution from the public API surface.

## Data handling

Managed providers should process media using temporary, least-privilege access.

Rules:

- do not copy media unnecessarily;
- do not retain temporary files beyond processing needs;
- do not persist biometric templates unless explicitly required and governed;
- store normalized evidence instead of unrestricted raw responses;
- record retention class and deletion state;
- respect legal holds and subject deletion workflows;
- never include provider credentials or signed evidence URLs in telemetry.

## Observability

Safe operational telemetry may include:

- request and correlation IDs;
- provider check ID;
- capability;
- provider, adapter, model, and schema versions;
- duration;
- status and normalized error code;
- retryability;
- resource utilization without sensitive payloads.

## Failure semantics

Managed provider failures must map to platform-wide states such as:

- `timeout`
- `unavailable`
- `invalid_request`
- `unsupported_input`
- `malformed_response`
- `inconclusive`
- `provider_error`
- `policy_blocked`

The workflow determines whether to retry, choose another provider, request new evidence, enter Manual Review, or fail closed.

## Deployment

The FastAPI service should remain independently scalable and private. CPU execution should be supported where practical; GPU or dedicated inference nodes may be used where justified by model and latency requirements.

Production deployment requires explicit model assets, health/readiness checks, resource limits, monitoring, network controls, and representative validation. Merely setting `AI_SERVICE_MODE=real` does not establish production fitness.

## Replacement and coexistence

An organization may replace or supplement managed capabilities with:

- commercial document or biometric providers;
- customer-hosted models;
- government registry evidence;
- specialist authenticity or fraud providers.

The workflow contract and normalized evidence model should remain stable when providers change.

## Related documentation

- [`ARCHITECTURE.md`](../../ARCHITECTURE.md)
- [`provider-runtime.md`](provider-runtime.md)
- [`capability-model.md`](capability-model.md)
- [`evidence-model.md`](evidence-model.md)
- [`managed-providers.md`](../providers/managed-providers.md)
- [`provider-sdk.md`](../providers/provider-sdk.md)

## Final principle

IdentityCore may operate excellent AI capabilities, but the platform's strategic value is not tied to one OCR engine, face model, or liveness implementation.

Managed AI Providers are replaceable participants in a governed identity execution plane. Evidence, policy, interoperability, privacy, and auditability remain the enduring platform contracts.
