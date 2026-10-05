# Tenant and environment encryption keys

Tenant-owned encrypted database fields and encrypted verification evidence JSON/PDF use separate sandbox and production DEKs. Tenant-wide administration fields, such as MFA settings and tenant configuration, use a third `shared` scope. Keys are random 256-bit values; database key records contain authenticated platform-wrapped envelopes. Neither API responses nor rotation command output include plaintext keys or content. Platform-global fields continue to use the application keyring.

Environment derives from authoritative project and verification relations; legacy project-less cases belong to sandbox. Field and object associated data bind the tenant public ID, environment, version and purpose. Object envelopes also authenticate content type. Reads accept retained older tenant key versions and legacy platform envelopes. Legacy envelopes lack tenant/environment cryptographic binding, so migrate them before claiming complete envelope isolation. Retain all referenced platform wrapping keys, including those needed to read wrapped DEKs in older backups.

Expand the database to install `tenants.0004` before starting this application version. Old application instances continue reading legacy envelopes but cannot read tenant v2 envelopes; drain writers and authentication workers before this cutover. Keep this application version and wrapping keys available during rollback; restoring old code while v2 data remains is unsafe. Historical migration models keep legacy field preparation so bootstrap does not query a key table before it exists.

Start a bounded rotation (the namespace is the actual tenant public ID):

```sh
python backend/django/manage.py rotate_tenant_keys --tenant "$TENANT_PUBLIC_ID" --environment sandbox --batch-size 100 --max-batches 1
```

The output prints a rotation ID, environment, state and counts. Repeat with that ID:

```sh
python backend/django/manage.py rotate_tenant_keys --resume "$ROTATION_PUBLIC_ID" --batch-size 100 --max-batches 10
```

New encryption uses the new active version immediately. Existing versions remain readable. Database migration checkpoints each model/field and primary key and uses compare-and-swap to preserve concurrent content updates. Conflicts cause another verification pass before completion. Evidence migration requires object-store ETags and conditional `IfMatch` writes; stores without conditional writes fail closed. Interrupted object batches remain readable even if object encryption committed before metadata/checkpoint updates. Resume after restoring storage availability or resolving a write conflict.

`completed` means the recorded database and referenced evidence scan finished. Drain any older encryption writers and verify referenced evidence and backups before retiring old wrapping material. This command deliberately retains old DEKs and wrapping-key references; it does not delete keys. Starting another rotation supersedes the older job's target; resume the current target's job rather than forcing writes under an inactive version.

Raw values queries return opaque tenant envelopes. Read encrypted values through owning instances, as the backup inventory does. Bulk updates of tenant encrypted fields require explicit prepared envelopes; normal writes and erasure use instance-aware saves. Wrapped key records are cached only within one HTTP request, with tenant/environment/version in the cache key; plaintext DEKs are not cached.
