# ADR-023: Pseudonymize data-subject deletion while preserving required audit facts

## Status

Accepted

## Decision

Data-subject deletion requires explicit confirmation and is tenant-scoped. An
active tenant or verification legal hold defers the request and reports each
hold reason.

When allowed, the workflow pseudonymizes the subject profile, document
metadata, verification metadata, and decision inputs while preserving stable
public identifiers, verification outcomes, and tamper-evident audit facts.
Raw evidence remains governed by the configured retention worker. The API
returns a completion report listing anonymized and retained categories.
