# AI Design

## IdentityCore

**Version:** 1.0

---

# Purpose

This document defines the AI and computer vision design for IdentityCore Version 1.0.

The AI system supports identity verification by processing document captures, selfie captures, liveness checks, face matching, quality analysis, and OCR.

The AI system does not make final business decisions. It produces evidence, scores, confidence levels, and technical outputs that the main platform evaluates using Verification Policies.

---

# AI Design Principle

AI in IdentityCore is an evidence engine, not the final authority.

The AI system should answer questions such as:

- Is there a face in the selfie?
- Is the document image clear?
- Does the selfie match the document portrait?
- Does the selfie appear to be live?
- What can be extracted from the document?
- What confidence score was produced?

The Django backend decides whether a Verification is approved, rejected, or sent to manual review.

---

# AI Service Architecture

IdentityCore uses a separate internal FastAPI service for AI processing.

```text
Django Backend
    |
    v
FastAPI AI Service
    |
    +--> Face Detection
    +--> Face Matching
    +--> Liveness Detection
    +--> Document Quality
    +--> OCR
    +--> Model Registry
```

The AI service is internal only.

It must not be exposed publicly.

---

# AI Service Responsibilities

The AI service is responsible for:

- Face detection
- Face alignment
- Face embedding generation
- Face comparison
- Passive liveness detection
- Active liveness challenge evaluation
- Document image quality checks
- OCR processing
- Document classification
- Model version reporting
- Confidence scoring

The AI service is not responsible for:

- Tenant authorization
- Final verification decisions
- Consent validation
- Audit ownership
- Billing
- Webhook delivery
- Manual review decisions

---

# AI Processing Flow

```text
Verification Subject submits document and selfie
        |
        v
Django validates verification session and consent
        |
        v
Django stores media in encrypted object storage
        |
        v
Django creates background AI jobs
        |
        v
FastAPI AI Service processes media
        |
        v
AI Service returns technical results
        |
        v
Django stores normalized results
        |
        v
Decision Engine applies Verification Policy
```

---

# Core AI Modules

## Face Detection

Face Detection identifies whether an image contains a face.

Inputs:

- Selfie image
- Document portrait image

Outputs:

- Face detected: true/false
- Number of faces
- Bounding box
- Detection confidence
- Model name
- Model version

Business rules:

- A selfie must contain exactly one clear face.
- A document image should contain one usable portrait where applicable.
- Multiple faces in a selfie should trigger rejection or manual review.
- No detected face should trigger rejection or retry.

---

## Face Alignment

Face Alignment normalizes detected faces before embedding generation.

Purpose:

- Improve face matching accuracy
- Reduce pose-related errors
- Standardize image input for models

Outputs:

- Aligned face image reference
- Alignment confidence
- Landmarks
- Model version

---

## Face Embedding

Face Embedding converts a face into a mathematical representation.

Inputs:

- Aligned selfie face
- Aligned document face

Outputs:

- Face embedding
- Embedding model name
- Embedding model version
- Embedding quality score

Rules:

- Embeddings are biometric templates.
- Embeddings must be encrypted if stored.
- Embeddings must never be exposed through public APIs.
- Embeddings should be deleted according to retention policy.

---

## Face Matching

Face Matching compares two face embeddings.

Typical comparison:

```text
Selfie Capture face
        vs
Identity Document portrait face
```

Outputs:

- Match score
- Threshold used
- Match result
- Confidence level
- Model name
- Model version

Example result:

```json
{
  "match_score": 0.94,
  "threshold_used": 0.85,
  "matched": true,
  "confidence_level": "high",
  "model_name": "insightface",
  "model_version": "v1"
}
```

Business rules:

- Face match alone must not be the only basis for sensitive decisions.
- Thresholds must be configurable by Verification Policy.
- Low match scores may trigger rejection or manual review.
- Borderline scores should trigger manual review.

---

# Liveness Detection

Liveness Detection determines whether the Verification Subject is physically present.

IdentityCore should support two approaches:

```text
Passive Liveness
Active Liveness
```

---

## Passive Liveness

Passive liveness analyzes an image or video without requiring user action.

Checks may include:

- Screen replay detection
- Printed photo detection
- Texture analysis
- Face depth cues
- Lighting consistency
- Spoof pattern detection

Advantages:

- Better user experience
- Faster onboarding
- Less friction

Risks:

- May be less reliable against advanced attacks
- Requires strong model validation

---

## Active Liveness

Active liveness requires the Verification Subject to perform an action.

Examples:

- Blink
- Turn head left/right
- Smile
- Read numbers aloud
- Follow on-screen prompts

Advantages:

- Stronger against simple spoofing
- Easier to explain during manual review

Risks:

- More friction
- Accessibility concerns
- Poor network/device quality issues

---

## Liveness Output

Example:

```json
{
  "liveness_type": "passive",
  "score": 0.92,
  "passed": true,
  "confidence_level": "high",
  "failure_reason": null,
  "model_name": "liveness-model",
  "model_version": "v1"
}
```

Business rules:

- Failed liveness should normally block automatic approval.
- Inconclusive liveness should trigger retry or manual review.
- Liveness thresholds must be configurable.
- Liveness evidence must follow retention policy.

---

# Document Intelligence

Document Intelligence processes Identity Documents.

Modules include:

- Document quality analysis
- Document classification
- OCR
- MRZ extraction for passports
- Field extraction
- Tamper detection in future versions

---

## Document Quality Analysis

Checks whether a document capture is usable.

Signals:

- Blur
- Glare
- Cropping
- Low resolution
- Poor lighting
- Obstruction
- Wrong orientation
- Missing corners

Output:

```json
{
  "quality_score": 0.88,
  "usable": true,
  "issues": []
}
```

Business rules:

- Poor quality should trigger retry.
- Repeated poor-quality attempts may trigger manual review.
- Quality results must be stored for auditability.

---

## Document Classification

Classifies the document type.

Examples:

- National ID
- Passport
- Driver License
- Voter ID
- Health ID

Output:

```json
{
  "document_type": "national_id",
  "confidence_score": 0.93,
  "country_code": "GH"
}
```

Business rules:

- The AI service returns generic Document Types.
- Country-specific document names come from Country Profiles.
- Low classification confidence should trigger manual review.

---

## OCR

OCR extracts from document captures.

Possible extracted fields:

- Full name
- Date of birth
- Document number
- Expiry date
- Issuing authority
- Nationality
- Gender, where applicable

Output:

```json
{
  "confidence_score": 0.91,
  "extracted_fields": {
    "full_name": "Kwame Mensah",
    "date_of_birth": "1998-01-01",
    "document_number": "masked_or_hashed"
  }
}
```

Business rules:

- OCR output must be treated as unverified evidence.
- OCR output should be normalized by the Django backend.
- Sensitive fields should be masked or hashed where possible.
- OCR confidence should affect risk scoring.

---

## MRZ Extraction

MRZ extraction applies mainly to passports.

Version 1.0 may include basic MRZ reading if passport support is included.

Extracted data may include:

- Passport number
- Date of birth
- Expiry date
- Nationality
- Name
- MRZ checksum validity

Business rules:

- MRZ checksum validation increases confidence.
- Failed MRZ extraction does not automatically mean fraud.
- Manual review may be required.

---

# Model Registry

IdentityCore must track model versions.

Each AI result should include:

- Model name
- Model version
- Model type
- Processing timestamp
- Confidence score
- Runtime environment

Purpose:

- Auditability
- Debugging
- Reproducibility
- Model replacement
- Performance monitoring

Example:

```json
{
  "model_name": "insightface",
  "model_version": "buffalo_l_v1",
  "model_type": "face_embedding",
  "processed_at": "2026-07-04T10:03:00Z"
}
```

---

# Confidence Levels

Raw model scores should be converted into human-readable confidence levels.

Example:

```text
0.90 - 1.00  high
0.70 - 0.89  medium
0.50 - 0.69  low
0.00 - 0.49  very_low
```

Actual thresholds must be tested and configurable.

Confidence levels should support, not replace, raw scores.

---

# Decision Boundaries

The AI service must not return:

```text
verified
rejected
manual_review_required
```

Those are business decisions.

The AI service may return:

```text
matched
not_matched
passed
failed
inconclusive
```

The Django Decision Engine maps AI results to Verification Decisions.

---

# Threshold Management

Thresholds should be configured in Verification Policies.

Examples:

```text
face_match_threshold = 0.85
manual_review_threshold = 0.65
liveness_threshold = 0.80
document_quality_threshold = 0.75
```

Business rules:

- Different organizations may use different thresholds.
- Higher-risk workflows may require stricter thresholds.
- Threshold changes must be versioned.
- The threshold used must be recorded for every result.

---

# Bias and Fairness

IdentityCore must treat biometric AI bias as a serious risk.

Requirements:

- Evaluate model performance across diverse demographics.
- Avoid relying on face matching alone.
- Support manual review.
- Track false positive and false negative rates.
- Monitor performance by geography and document type where lawful and appropriate.

The platform should avoid collecting sensitive demographic data unless legally justified and ethically necessary for model evaluation.

---

# Accuracy Metrics

AI performance should be measured using:

- False Acceptance Rate
- False Rejection Rate
- Equal Error Rate
- Precision
- Recall
- Confidence calibration
- Processing latency
- Manual review rate

For OCR:

- Field-level accuracy
- Character error rate
- Document classification accuracy

For liveness:

- Attack presentation classification error rate
- Bona fide presentation classification error rate

---

# Performance Targets

Initial targets for Version 1.0:

```text
Face detection: < 1 second
Face matching: < 3 seconds
Liveness check: < 5 seconds
Document quality check: < 2 seconds
OCR: < 5 seconds
```

Targets may vary depending on hardware and media size.

---

# Hardware Strategy

Version 1.0 should support CPU-based inference where possible.

Future versions may support:

- GPU inference
- Model quantization
- ONNX Runtime optimization
- Batch processing
- Dedicated AI nodes

For MVP, avoid requiring expensive GPU infrastructure unless necessary.

---

# Model Selection

Initial model candidates:

```text
Face Detection:
MediaPipe, RetinaFace

Face Embeddings / Matching:
InsightFace, FaceNet

Liveness:
Open-source passive liveness models, MediaPipe-based active checks, commercial provider fallback

OCR:
PaddleOCR, Tesseract, EasyOCR

Document Quality:
OpenCV-based quality checks
```

Final model choices must be documented in ADRs.

---

# Provider Fallback Strategy

IdentityCore should support internal and external AI providers.

Example:

```text
Primary: Internal AI Service
Fallback: Third-party KYC provider
```

Provider fallback may be useful when:

- Internal model fails
- Accuracy is uncertain
- Specific country document support is weak
- Enterprise customer requires certified provider

Provider usage must be auditable.

---

# Data Handling

AI processing should use temporary access to media.

Rules:

- Use signed internal URLs or secure object storage access.
- Do not copy media unnecessarily.
- Do not store temporary files permanently.
- Delete temporary files after processing.
- Never log raw media or biometric templates.
- Record only required metadata and results.

---

# AI Security

AI-specific security requirements:

- Validate input files.
- Reject unsupported formats.
- Enforce file size limits.
- Protect against malicious files.
- Isolate processing environment.
- Prevent path traversal.
- Prevent model endpoint abuse.
- Rate limit AI requests.
- Log processing errors safely.

---

# AI Observability

AI processing should log:

- Request ID
- Verification ID
- Processing module
- Model name
- Model version
- Duration
- Status
- Error code where applicable

AI logs must not include raw biometric or document data.

---

# AI Failure Handling

AI failures should be handled safely.

Examples:

- OCR failure → retry or manual review
- Face detection failure → retry capture
- Liveness inconclusive → retry or manual review
- Provider timeout → retry or mark provider unavailable
- Model error → fail safely and notify system

AI failure should not expose internal technical details to Verification Subjects.

---

# Manual Review Support

AI results should support human review.

Manual reviewers may need:

- Document quality issues
- Extracted fields
- Face match score
- Liveness score
- Risk signals
- Evidence summary
- Model version
- Reason codes

Manual review screens must avoid exposing unnecessary sensitive information.

---

# Model Update Strategy

Model updates must be controlled.

Requirements:

- Version every model.
- Test before deployment.
- Record old and new performance.
- Support rollback.
- Avoid silent model changes.
- Record model version per verification result.

---

# Future AI Capabilities

Future versions may include:

- Document forgery detection
- Deepfake detection
- Voice liveness
- Fingerprint matching
- Iris recognition
- Duplicate identity detection
- Face search across authorized datasets
- Watchlist matching where legally permitted
- Fraud pattern detection
- Model drift detection
- Automated document template learning

---

# Version 1.0 AI Scope

Version 1.0 includes:

- Face detection
- Face matching
- Passive liveness
- Basic active liveness
- Document quality checks
- OCR
- Document classification
- Model version tracking
- Confidence scoring
- Manual review support

Version 1.0 excludes:

- Government database lookup
- Criminal watchlist matching
- Mass face search
- Fingerprint recognition
- Iris recognition
- Deepfake detection as a certified control
- Fully autonomous high-impact decisions
- Model training pipeline
- Production-grade biometric search engine

---

# Final AI Principle

IdentityCore's AI must be accurate, explainable, auditable, replaceable, and privacy-preserving.

The goal is not to replace human judgment or legal responsibility. The goal is to provide strong, measurable identity evidence that helps organizations make secure and responsible verification decisions.
