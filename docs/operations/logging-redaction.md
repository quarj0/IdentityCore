# Logging redaction and safe telemetry

IdentityCore treats logs as an operational data stream, not as a place to store verification evidence or user data. Application logs must never contain credentials, session material, direct subject PII, raw document/OCR content, storage locations for evidence, or biometric payloads.

## Backend boundary

Django, Celery workers, storage/provider call paths, and the managed AI service use the shared redaction implementation in `backend/shared/logging_redaction.py`.

The boundary is installed when Django starts, before Celery initializes its application logger, and before the AI service imports processing routes. It sanitizes every Python `LogRecord` after `extra` fields have been attached and before handlers format the record. This covers:

- nested dictionaries/lists passed as structured logging context;
- positional and mapping logging arguments;
- bearer/JWT-like credentials and common credential assignments embedded in free text;
- common email, phone, and IP shapes in free text;
- exception messages and tracebacks;
- bytes and byte-like values, which are always replaced rather than rendered.

Safe operational dimensions such as public request/verification IDs, operation names, status/reason codes, provider codes, durations, retry counts, and queue names may be logged when they do not themselves contain subject data.

When a new secret, PII field, document field, or biometric representation is introduced, add its normalized key to the shared redaction corpus and add an adversarial test before using it in telemetry.

## Frontend boundary

Frontend code must use `safeLog` exported by `@identitycore/api-client`. The logger applies the same categories of key-aware and free-text redaction before calling the browser console.

Direct `console.log`, `console.info`, `console.warn`, `console.error`, `console.debug`, or `console.trace` calls are rejected by the frontend lint gate for production source. This prevents a future component from bypassing the redaction helper with a raw API error, token, form state, capture payload, or server response.

## What not to log

Do not log:

- authorization headers, API keys, passwords, cookies, refresh/session tokens, provider credentials, or private keys;
- names, email addresses, phone numbers, addresses, dates of birth, national/passport/document numbers, or tax identifiers;
- OCR/MRZ text, raw document images/bytes, evidence storage keys, selfies, face embeddings, liveness media, or biometric templates;
- complete request/response bodies from identity, provider, storage, or webhook operations.

Prefer stable reason/error codes and public correlation identifiers over raw exception/request payloads.

## Verification

The CI suite includes adversarial tests for Django, Celery, managed AI, and frontend logging. Tests intentionally place sensitive values in nested structured fields, positional arguments, binary values, and exception text and assert that those values never reach formatted log output. Frontend lint also fails when production source introduces a direct console logging call.
