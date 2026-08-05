# IdentityCore Managed Providers

> IdentityCore Managed Providers are provider implementations operated by the IdentityCore deployment. They are convenient defaults, not privileged architectural components.

## Purpose

IdentityCore includes built-in implementations for selected capabilities so the first workload can operate without requiring every customer to integrate a third-party provider.

These implementations are exposed through the same provider abstraction used by commercial, government, and customer-hosted providers.

## Current managed capability areas

The internal AI service currently hosts or supports managed implementations for capabilities including:

- document image quality analysis;
- document classification;
- OCR and field extraction;
- face detection and face comparison;
- passive and active liveness-related processing;
- presentation attack detection where configured;
- model and processing metadata.

Exact support depends on configured models, runtime mode, enabled countries, document definitions, and deployment resources.

## Architectural position

```text
Workflow Engine
      |
      v
Provider Runtime
      |
      +--> IdentityCore Managed Provider
      +--> Commercial Provider
      +--> Government Registry
      +--> Customer-hosted Provider
```

Core workflow and decision code must not call managed implementations directly. Managed implementations must be resolved, invoked, observed, and normalized through provider contracts.

## Why managed providers exist

Managed providers offer:

- a working default for local development and early deployments;
- consistent integration with IdentityCore evidence and audit models;
- transparent model and adapter versioning;
- a reference implementation for Provider SDK authors;
- a fallback option when organizational policy permits it;
- a path for deployments that require self-hosted or open components.

## What managed does not mean

Managed does not mean:

- mandatory;
- more trusted than every external provider;
- exempt from capability contracts;
- exempt from policy or evidence normalization;
- allowed to make final business decisions;
- universally accurate across all people, countries, documents, devices, or attacks;
- production-certified merely because the code exists in the repository.

## Runtime modes

The AI service supports runtime modes for different deployment needs.

- **Mock** supports deterministic development without full model assets.
- **Hybrid** may combine available real processing with controlled fallback behavior.
- **Real** uses configured model assets and object-storage access for actual processing.

Runtime mode must be observable in provider metadata. Mock results must never be mistaken for production evidence.

## Evidence responsibilities

A managed provider should emit technical evidence such as:

- quality issues and usability status;
- classification candidates and confidence;
- OCR lines and normalized extracted fields;
- face comparison score and model metadata;
- liveness/PAD outcome and confidence;
- warnings, unsupported states, and processing failures.

The provider must not return the organization's final verification decision. The Policy and Decision Engines interpret normalized evidence.

## Model governance

Each managed model result should identify:

- model name;
- model version;
- adapter version;
- capability schema version;
- processing timestamp;
- runtime mode;
- threshold or configuration version where relevant;
- processing duration;
- warnings and confidence.

Model replacement must not erase the identity of the model used for historical evidence.

## Accuracy and fairness

Managed biometric and document models require deployment-specific evaluation.

IdentityCore must not advertise unsupported general accuracy percentages. Any published performance claim should identify:

- exact capability;
- model and configuration version;
- supported countries and document types;
- evaluation dataset and date;
- attack categories where relevant;
- false acceptance and false rejection measures;
- precision and recall;
- manual-review rate;
- known limitations.

Uncertain or out-of-distribution evidence should route to retry, another provider, or Manual Review rather than silent approval.

## Data handling

Managed providers should receive short-lived, minimal access to evidence.

They must:

- avoid unnecessary media copies;
- never log raw media or biometric templates;
- enforce file type and size limits;
- delete temporary files;
- redact signed URLs and credentials;
- isolate model execution;
- return only required normalized results and bounded diagnostics.

## Provider replacement

Organizations should be able to replace a managed capability with another provider without changing their application integration.

Replacement should occur through versioned provider assignment or routing configuration, while the workflow continues to request the same capability.

```text
workflow requests document.ocr
            |
            v
provider route selects implementation
            |
      +-----+-----+
      |           |
managed OCR   customer OCR
```

## Fallback

Managed providers may participate in fallback chains, but fallback must be explicit and auditable.

A future complete route may state:

```text
customer-hosted OCR
    -> commercial OCR on retryable failure
    -> managed OCR on regional availability
    -> Manual Review if no acceptable result
```

The current runtime has invocation and adapter foundations, but documentation should not claim every conditional route and ordered fallback behavior is complete until implemented and tested end to end.

## Security boundary

The managed provider host is an execution service, not a trusted bypass around the core platform.

It must use:

- authenticated internal requests;
- service-to-service authorization;
- request correlation;
- bounded media access;
- network restrictions;
- secure model and dependency management;
- safe failure behavior;
- provider-check recording;
- audit-compatible metadata.

## Operational responsibilities

A production deployment must monitor:

- readiness and model availability;
- capability latency;
- timeout and failure rates;
- queue depth;
- CPU/GPU/memory usage;
- model drift and quality metrics;
- manual-review outcomes;
- dependency and model integrity;
- evidence access failures.

## Relationship to AI design

`docs/architecture/ai-design.md` remains the detailed design for computer vision and OCR implementations.

That document should be read as the design of selected IdentityCore Managed Providers, while `provider-runtime.md` and `provider-sdk.md` define the provider-neutral platform boundary.

## Current maturity

Implemented foundations include:

- a separate FastAPI provider host;
- real, hybrid, and mock processing paths;
- adapter-backed capability execution;
- centralized provider invocation;
- provider-check persistence;
- normalized and versioned outcomes;
- model metadata;
- redacted telemetry;
- timeout and failure handling;
- Manual Review routing for uncertain outcomes.

Production maturity still depends on model evaluation, deployment hardening, expanded country/document support, operational monitoring, security review, and conformance with the same contracts expected of external providers.
