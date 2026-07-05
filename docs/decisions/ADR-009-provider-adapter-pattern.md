# ADR-009: Provider Adapter Pattern

**Status:** Accepted

**Date:** 2026-07-04

---

## Context

IdentityCore relies on external providers for services that are outside the platform's core responsibilities.

Examples include:

* OCR services
* Email delivery
* SMS delivery
* Notification services
* Identity verification providers
* Future payment providers
* Future government integrations

Each provider exposes different APIs, authentication methods, request formats, response structures, rate limits, and error handling mechanisms.

Directly integrating these providers into business logic would tightly couple IdentityCore to specific vendors and make future changes costly.

---

## Decision

IdentityCore will implement the **Provider Adapter Pattern**.

Every external provider must be accessed through an adapter that exposes a consistent internal interface.

The rest of the application communicates only with the adapter, never directly with the provider.

---

## Architecture

``` id="7s0d2a"
Business Logic
        │
        ▼
Provider Interface
        │
        ▼
Provider Adapter
        │
        ▼
External Provider
```

Business logic should not know which vendor is being used.

---

## Responsibilities

The Provider Adapter is responsible for:

* Authentication
* Request formatting
* Response normalization
* Error translation
* Retry handling
* Timeout handling
* Logging provider metadata

Business logic remains provider-agnostic.

---

## Examples

## OCR

``` id="i3hrw0"
OCRService

↓

PaddleOCRAdapter

or

CommercialOCRAdapter

or

GovernmentOCRAdapter
```

---

## Email

``` id="azbbjk"
EmailService

↓

ResendAdapter

or

SMTPAdapter

or

EnterpriseMailAdapter
```

---

## SMS

``` id="kmzzm2"
SMSService

↓

HubtelAdapter

or

ArkeselAdapter

or

TwilioAdapter
```

---

## Identity Providers

``` id="q2f2hs"
IdentityVerificationProvider

↓

NationalIDAdapter

PassportAuthorityAdapter

CommercialKYCAdapter
```

Each adapter implements the same internal contract.

---

## Interface Design

Every provider category should define a common interface.

Example:

```python id="eqyzvz"
class OCRProvider:

    def extract_text(...):
        ...

    def classify_document(...):
        ...
```

Every OCR adapter implements this interface.

Business logic depends on the interface rather than a concrete implementation.

---

## Response Normalization

Providers return different response formats.

Adapters convert them into a standard internal format.

Example:

Provider A:

```json id="hn26mo"
{
  "score": 0.94
}
```

Provider B:

```json id="kp2dnx"
{
  "confidence": 94
}
```

Internal result:

```json id="ef0eyg"
{
  "confidence_score": 0.94
}
```

This keeps business logic simple and consistent.

---

## Error Handling

Provider-specific errors should never propagate directly into business logic.

Instead, adapters should translate them into standard internal exceptions.

Examples:

* ProviderTimeout
* ProviderUnavailable
* InvalidProviderResponse
* ProviderAuthenticationError

The rest of the application should not need to understand provider-specific error codes.

---

## Configuration

Organizations may configure different providers where supported.

Example:

``` id="kixfah"
Organization A

↓

PaddleOCR

Organization B

↓

Commercial OCR

Organization C

↓

Government OCR
```

The backend selects the appropriate adapter at runtime.

---

## Fallback Strategy

Provider adapters support fallback.

Example:

``` id="lgf1p9"
Primary OCR

↓

Failure

↓

Secondary OCR

↓

Failure

↓

Manual Review
```

Fallback logic should be configurable and auditable.

---

## Security

Provider adapters must:

* Use secure authentication.
* Validate responses.
* Enforce timeouts.
* Log safely.
* Protect credentials.
* Avoid leaking sensitive information.

Credentials must never be hardcoded.

---

## Testing

Business logic tests should mock provider interfaces rather than provider implementations.

Each adapter should have dedicated integration tests.

This allows provider changes without affecting business logic tests.

---

## Monitoring

Metrics should include:

* Provider response time
* Success rate
* Failure rate
* Timeout rate
* Retry count
* Fallback usage

Monitoring should identify provider degradation early.

---

## Consequences

## Positive

* Reduced vendor lock-in.
* Easier provider replacement.
* Consistent business logic.
* Improved testing.
* Cleaner architecture.
* Easier support for multiple providers.
* Better long-term maintainability.

## Negative

* Additional abstraction layer.
* Slight increase in implementation effort.
* Every new provider requires an adapter.

These trade-offs are acceptable because provider flexibility is a strategic goal.

---

## Alternatives Considered

## Direct Provider Integration

Rejected because it tightly couples business logic to provider APIs.

Replacing providers would require widespread code changes.

---

## One Adapter for Every Provider Feature

Rejected because adapters should expose business capabilities, not mirror provider APIs.

The internal interface should remain stable even if provider capabilities differ.

---

## Generic HTTP Wrapper

Rejected because providers require business-specific normalization and error handling.

A generic HTTP client alone does not provide sufficient abstraction.

---

## Future Considerations

Future versions may support:

* Dynamic provider selection
* Provider health scoring
* Geographic routing
* Cost-aware provider selection
* AI-assisted provider recommendations

These enhancements should remain behind the adapter interface.

---

## Implementation Notes

* Business logic depends on provider interfaces.
* Providers are selected through configuration.
* Responses are normalized.
* Errors are translated.
* Credentials are managed securely.
* Provider-specific code remains isolated.

---

## References

* Architecture
* AI Design
* Security
* Deployment
* Coding Standards
* Testing Strategy
