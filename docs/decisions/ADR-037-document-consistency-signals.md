# ADR-037: Versioned country-aware document signals

Status: Accepted

Document consistency produces evidence independently of decisions. A policy
version snapshots validated per-country rules and explicit signal actions.
Historical cases keep their rule snapshots. The risk evaluator applies only the
configured review/rejection actions, preserving existing rejection precedence.
Default configuration has no document-based decision action.

MRZ century ambiguity remains explicit; a heuristic cannot silently establish
age. Visual OCR and MRZ provenance remain separately available in encrypted
extraction evidence. Risk summaries contain fixed issue codes, applied versions
and age, without duplicating identity fields. Public projections stay redacted.
The additive policy configuration is documented in OpenAPI and generated SDKs.
