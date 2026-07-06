# Manual Testing

## Purpose

This checklist is for smoke-testing IdentityCore when automated tests pass but the integrated flow still needs human verification.

## Current State

- `pytest` is configured for `backend/ai-service/tests`
- Django backend suites still run through `python django/manage.py test`
- Frontend and local dev orchestration are still incomplete, so manual testing should focus on API and service behavior first

## AI Service Smoke Checks

Before starting the AI service, verify:

- `AI_SERVICE_MODE` is set to `mock`, `hybrid`, or `real`
- `AI_MODEL_ROOT` matches the deployed model directory layout
- object storage credentials and media bucket settings are present for `hybrid` and `real`

After startup:

1. Call `GET /v1/health` and confirm the reported mode.
2. Call `GET /v1/ready` with the internal token and confirm:
   - `mock` returns `ready=true`
   - `hybrid` may return `status=degraded` with fallback available
   - `real` must return `ready=true`
3. Submit sample requests for:
   - `/v1/document/quality`
   - `/v1/document/ocr`
   - `/v1/document/classify`
   - `/v1/liveness/check`
   - `/v1/face/compare`

## Django Verification Flow Checks

Test at least one full verification manually:

1. Create a verification.
2. Accept consent.
3. Upload document captures.
4. Upload selfie or liveness video.
5. Submit liveness.
6. Verify:
   - uploads move from temp to media
   - document OCR, classification, and quality provider checks are created
   - liveness and face match provider checks complete
   - verification status updates correctly
   - evidence JSON and PDF artifacts are created in the evidence bucket

## Recommended Test Modes

- Use `mock` for UI and integration wiring.
- Use `hybrid` for early shared-environment validation.
- Use `real` only after readiness passes and local model assets are confirmed.
