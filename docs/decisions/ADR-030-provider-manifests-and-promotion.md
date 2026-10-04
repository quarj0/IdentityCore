# ADR-030: Declare provider coverage and approve environment configuration

Status: Accepted

Provider Contract v1 remains the execution boundary. Providers add a public manifest v1 declaring capability input/output schema versions, country/document coverage, supported environments, processor, residency, retention and transfer notes. Credentials remain exclusively in encrypted configuration. Tenant listings expose declarations and a configured flag, never configuration values.

Assignments and route publication validate declared compatibility before activation. Empty legacy manifests remain compatible during rollout; new self-service configurations require declarations. A route without country/document restrictions requires wildcard coverage. Deployment privacy owners must validate processor agreements and residency statements; declarations do not prove vendor compliance.

Sandbox configuration promotion creates a distinct production configuration, takes separately supplied credentials, records a public configuration diff, requires fresh connection evidence tied to the exact configuration digest, and separates requester from privileged approver. Any subsequent change invalidates the test and approval. Production invocations select their own environment configuration and never fall back to sandbox credentials.
