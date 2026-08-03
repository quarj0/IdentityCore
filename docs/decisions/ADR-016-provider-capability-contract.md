# ADR-016: Version the provider capability contract

## Status

Accepted

## Decision

Every provider invocation crosses the same adapter boundary and persists a
normalized result containing `contract_version`, `capability`, and `status`.
The contract applies to document OCR, document quality, classification,
liveness, and face comparison. Provider-specific fields remain available for
evidence, while workflow code relies on the stable fields.

Provider failures use the same versioned envelope with a stable capability and
error object, allowing retries and safe manual-review routing without exposing
provider-specific transport details.
