# Provider manifest v1

`Provider.manifest_json` is public metadata. The tenant provider list includes only the caller's providers and platform defaults, and returns a configured flag instead of encrypted configuration. Do not put credentials, subject data or private endpoints in declarations.

Required properties: `manifest_version: "1"`, `contract_version: "1"`, `processor`, `transfer_notes`, `retention_days` (0–36500), `residency` (nonempty region identifiers), `environments` (sandbox/production), and `capabilities`.

Each capability declares `countries` (ISO alpha-2 or `*`), `document_types` (identifiers or `*`), `input_schema: "<capability>.input/v1"` and `output_schema: "<capability>.output/v1"`. Unknown fields/versions, incompatible provider types, oversized declarations and duplicate coverage values are rejected. Existing Provider Contract v1 defines execution fields; these schema identifiers select that version and do not permit an arbitrary external schema URL.

Active global assignments require both sandbox and production support and unrestricted country/document coverage. Route publication checks capability, environment and its exact coverage restrictions; an unrestricted route requires wildcard coverage. Editing a declaration cannot invalidate an active assignment or published route. Tenant and provider row locks serialize edits with activation. Provider identity (tenant, code and type) is immutable. Legacy empty declarations remain supported for existing managed and registered adapters during rollout; new self-service setup requires a validated declaration. See ADR-030 for environment configuration approval.
