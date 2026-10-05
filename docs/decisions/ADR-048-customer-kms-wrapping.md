# ADR 048: Customer-managed KMS and HSM wrapping

Status: Accepted

Customer keys wrap tenant/environment DEKs through AWS KMS symmetric Encrypt/Decrypt. This includes customer keys backed by AWS CloudHSM custom key stores and imported key material. Applicant plaintext stays in the application; only random DEKs and short-lived connection probes reach KMS. Tenant administration authentication keys remain platform-wrapped.

Connections require explicit manage_encryption permission and validate a stable key ARN, enabled symmetric customer-key metadata, effective Encrypt/Decrypt grants, and an authenticated-context round trip before activation. Context binds tenant public ID, environment, binding public ID, key version and wrapping purpose. Optional grant tokens are platform-encrypted to avoid recursive dependence on the DEKs they authorize. Responses and audit events never include tokens, plaintext DEKs or wrapped blobs.

Activating a validated binding starts a new DEK version and resumable rotation. Earlier binding records remain available for old-version reads. Explicit disablement blocks wrapping and unwrapping through that binding; outages fail closed without falling back to platform keys. Disabled bindings can be revalidated and re-enabled for recovery. SDK requests have bounded timeouts and one attempt; the application does not retry or log raw provider errors.

Configuration is tenant/environment scoped and source key ARNs are immutable. Contract tests exercise grants, metadata checks, context isolation, rotation, disabled keys and outages with an in-memory KMS fixture. Live connection validation happens only when an authorized tenant administrator explicitly configures a real key using the service's IAM credentials.
