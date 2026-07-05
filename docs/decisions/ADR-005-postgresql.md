# ADR-005: PostgreSQL as the Primary Database

**Status:** Accepted

**Date:** 2026-07-04

---

## Context

IdentityCore stores highly structured and relational data, including:

- Organizations
- Tenants
- Platform Users
- Verification Subjects
- Verifications
- Verification Sessions
- Identity Documents
- Consent Records
- Verification Policies
- Audit Events
- API Clients
- Webhook Configurations
- AI Processing Results

The platform requires a database that provides:

- Strong consistency
- ACID transactions
- Mature indexing
- Excellent relational modeling
- High reliability
- Long-term scalability

---

## Decision

IdentityCore will use **PostgreSQL** as the primary database for Version 1.0.

PostgreSQL will serve as the system of record for all persistent business data.

All domain models will be stored in PostgreSQL unless there is a compelling architectural reason to use another storage technology.

---

## Why PostgreSQL?

PostgreSQL was selected because it provides:

- Full ACID compliance
- Excellent relational capabilities
- Mature query planner
- Strong indexing options
- JSONB support
- Full- search
- Row-level locking
- Transaction support
- Large ecosystem
- Proven reliability

These capabilities align well with IdentityCore's security, auditability, and consistency requirements.

---

## Data Ownership

PostgreSQL stores:

- Organizations
- Tenants
- Platform Users
- Roles
- Permissions
- Verification Subjects
- Verifications
- Verification Sessions
- Verification Decisions
- Identity Documents metadata
- Consent Records
- Audit Events
- Provider configurations
- API Clients
- Webhook endpoints
- AI metadata
- Configuration data

Large binary files are **not** stored inside PostgreSQL.

---

## Object Storage

Binary media such as:

- Identity Documents
- Selfie Captures
- Liveness Videos

will be stored in encrypted object storage.

PostgreSQL stores only:

- Metadata
- File references
- Checksums
- Processing status

This keeps the database efficient while allowing secure handling of large media files.

---

## JSONB Usage

PostgreSQL's JSONB type may be used for data that is:

- Semi-structured
- Provider-specific
- Configuration-based
- Expected to evolve over time

Examples:

- Provider metadata
- AI processing metadata
- OCR raw output
- Webhook payload snapshots
- Device metadata

Core business entities should remain relational.

---

## Transactions

Critical operations should execute within database transactions.

Examples:

- Creating a Verification
- Recording Consent
- Creating Audit Events
- Issuing Verification Sessions
- Recording Manual Decisions

Transactions help maintain consistency during failures.

---

## Constraints

Database constraints should enforce data integrity wherever possible.

Examples:

- Foreign keys
- Unique constraints
- Check constraints
- Not-null constraints

Business rules that cannot be represented as database constraints belong in the service layer.

---

## Indexing

Indexes should be created for:

- Public IDs
- Tenant identifiers
- Verification status
- Verification Sessions
- Created timestamps
- Expiration timestamps
- API Client identifiers
- Audit Event timestamps

Indexes should be added based on measured performance rather than assumptions.

---

## Multi-Tenancy

IdentityCore uses a shared PostgreSQL database with a shared schema.

Tenant isolation is enforced by the application layer.

Every tenant-owned query must include tenant context.

Future versions may evaluate row-level security or dedicated databases for specific enterprise customers.

---

## Migrations

Schema changes must be managed through Django migrations.

Migration principles:

- Version-controlled
- Reviewed
- Tested in staging
- Backward compatible where possible

Destructive migrations should be planned carefully and executed only when necessary.

---

## Backup Strategy

PostgreSQL backups must support:

- Automated backups
- Encrypted storage
- Point-in-time recovery where possible
- Regular restoration testing

Backups should be monitored and periodically verified.

---

## Performance Strategy

Performance improvements should follow this order:

1. Optimize queries.
2. Add indexes.
3. Improve schema design.
4. Introduce caching.
5. Scale database resources.

Avoid premature optimization.

---

## High Availability

Version 1.0 does not require a highly available PostgreSQL cluster.

Future enterprise deployments may introduce:

- Streaming replication
- Read replicas
- Automatic failover
- Multi-region replication

These features should be introduced only when operational requirements justify them.

---

## Consequences

## Positive

- Strong transactional consistency.
- Mature ecosystem.
- Excellent support in Django.
- Powerful query capabilities.
- Reliable audit data storage.
- Flexible support for structured and semi-structured data.

## Negative

- Vertical scaling has limits.
- Large media must be stored separately.
- Requires careful indexing for high-volume workloads.

These trade-offs are acceptable for the expected growth of Version 1.0.

---

## Alternatives Considered

## MySQL

Rejected because PostgreSQL provides stronger support for advanced features such as JSONB, indexing options, and complex queries that are expected to benefit IdentityCore.

---

## MongoDB

Rejected because IdentityCore's core data model is highly relational and benefits from ACID transactions, foreign keys, and structured schemas.

MongoDB may be considered for specialized workloads in the future, but not as the primary system of record.

---

## Multiple Databases (Polyglot Persistence)

Rejected for Version 1.0 because maintaining multiple primary databases would increase operational complexity without sufficient benefit.

The platform will begin with a single relational database and introduce additional storage technologies only when justified.

---

## SQLite

Rejected because it is intended primarily for local development and is not suitable for production workloads involving concurrent users and high-volume identity verification.

---

## Future Considerations

Future versions may evaluate:

- Read replicas
- Table partitioning
- Database sharding
- PostgreSQL Row-Level Security
- Vector extensions for AI search
- Time-series storage for analytics
- Separate analytics database

These enhancements should not compromise the platform's core transactional integrity.

---

## Implementation Notes

- PostgreSQL is the authoritative source of business data.
- Object storage is used for binary media.
- Redis is not a source of truth.
- Database models should remain normalized unless performance measurements justify denormalization.
- Every externally exposed resource should use a prefixed ULID as its public identifier.

---

## References

- Database Design
- Architecture
- Deployment
- Security
- Coding Standards
- ADR-001: Public ID Strategy
- ADR-002: Modular Monolith Architecture
