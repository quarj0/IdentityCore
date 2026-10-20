"""Encrypted, transactional single-host reference store; no volatile replay default.

Use a shared transactional database adapter for multiple hosts. SQLite's WAL is
for processes on one local filesystem, never a network filesystem or pod copies.
"""

from contextlib import contextmanager
from dataclasses import dataclass, field
from hashlib import sha256
import os
from pathlib import Path
import secrets
import sqlite3
import time

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .contracts import same_binding, validate_result
from .wire import ProtocolError, json_bytes, parse_json


class StorageUnavailable(RuntimeError):
    def __init__(self):
        super().__init__("Provider operation storage is unavailable.")


@dataclass(frozen=True)
class WorkerLease:
    operation_id: str
    generation: int
    owner: str = field(repr=False)
    binding: dict = field(repr=False)
    inputs: dict = field(repr=False)


class SQLiteStore:
    def __init__(self, path, *, encryption_key: bytes, clock=time.time):
        if not isinstance(encryption_key, bytes) or len(encryption_key) != 32:
            raise ValueError(
                "Supply a separate 32-byte provider-storage encryption key."
            )
        self.path = Path(path)
        self.clock = clock
        self._cipher = AESGCM(encryption_key)
        descriptor = os.open(self.path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
        os.close(descriptor)
        os.chmod(self.path, 0o600)
        with self._transaction() as db:
            db.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS nonces (digest TEXT PRIMARY KEY, expires REAL NOT NULL);
                CREATE INDEX IF NOT EXISTS nonce_expiry ON nonces(expires);
                CREATE TABLE IF NOT EXISTS operations (
                    id TEXT PRIMARY KEY, configuration TEXT NOT NULL, deadline REAL NOT NULL,
                    state TEXT NOT NULL, content BLOB NOT NULL, generation INTEGER NOT NULL DEFAULT 0,
                    owner TEXT NOT NULL DEFAULT '', lease_until REAL NOT NULL DEFAULT 0,
                    result_digest TEXT NOT NULL DEFAULT '', created REAL NOT NULL
                );
                CREATE INDEX IF NOT EXISTS operation_work ON operations(state,deadline,lease_until);
            """)

    @contextmanager
    def _transaction(self):
        db = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        db.row_factory = sqlite3.Row
        try:
            db.execute("BEGIN IMMEDIATE")
            yield db
            if db.in_transaction:
                db.execute("COMMIT")
        except BaseException as error:
            if db.in_transaction:
                db.execute("ROLLBACK")
            if isinstance(error, sqlite3.Error):
                raise StorageUnavailable() from None
            raise
        finally:
            db.close()

    def _encrypt(self, operation_id, content):
        nonce = os.urandom(12)
        return nonce + self._cipher.encrypt(
            nonce, json_bytes(content), operation_id.encode()
        )

    def _decrypt(self, row):
        try:
            blob = bytes(row["content"])
            return parse_json(
                self._cipher.decrypt(blob[:12], blob[12:], row["id"].encode())
            )
        except Exception:
            raise StorageUnavailable() from None

    def claim_nonce(self, digest, expires_at):
        with self._transaction() as db:
            db.execute(
                "DELETE FROM nonces WHERE digest IN (SELECT digest FROM nonces WHERE expires <= ? LIMIT 256)",
                (self.clock(),),
            )
            try:
                db.execute("INSERT INTO nonces VALUES (?, ?)", (digest, expires_at))
                return True
            except sqlite3.IntegrityError:
                return False

    def admit(self, binding, inputs, deadline):
        operation_id = binding["operation_id"]
        with self._transaction() as db:
            row = db.execute(
                "SELECT * FROM operations WHERE id=?", (operation_id,)
            ).fetchone()
            if row is not None:
                content = self._decrypt(row)
                if not self._matches(content, binding):
                    raise ProtocolError(
                        "Operation admission conflicts with its existing binding."
                    )
                return self._response(row, content, binding)
            content = {"binding": binding, "inputs": inputs}
            db.execute(
                "INSERT INTO operations(id,configuration,deadline,state,content,created) VALUES(?,?,?,?,?,?)",
                (
                    operation_id,
                    binding["configuration_id"],
                    deadline.timestamp(),
                    "queued",
                    self._encrypt(operation_id, content),
                    self.clock(),
                ),
            )
            return {"binding": binding, "status": "pending", "retry_after_seconds": 10}

    @staticmethod
    def _matches(content, binding):
        if "binding" in content:
            return same_binding(content["binding"], binding)
        import hmac

        return hmac.compare_digest(
            content.get("binding_sha256", ""), sha256(json_bytes(binding)).hexdigest()
        )

    def _bound(self, db, binding):
        row = db.execute(
            "SELECT * FROM operations WHERE id=?", (binding["operation_id"],)
        ).fetchone()
        if row is None:
            raise ProtocolError("Provider operation is unavailable.")
        content = self._decrypt(row)
        if not self._matches(content, binding):
            raise ProtocolError("Provider operation is unavailable.")
        return row, content

    def _response(self, row, content, binding=None):
        bound = content.get("binding", binding)
        if row["state"] in {"completed", "failed"}:
            return {
                "binding": bound,
                "status": row["state"],
                "result": content["result"],
            }
        if row["state"] in {"cancelled", "deleted", "expired"}:
            return {"binding": bound, "status": row["state"]}
        return {
            "binding": bound,
            "status": "pending",
            "retry_after_seconds": 10,
        }

    def poll(self, binding):
        with self._transaction() as db:
            row, content = self._bound(db, binding)
            return self._response(row, content, binding)

    def claim_job(self, *, lease_seconds=30):
        if type(lease_seconds) is not int or not 1 <= lease_seconds <= 300:
            raise ValueError("Choose a bounded worker lease.")
        with self._transaction() as db:
            now = self.clock()
            row = db.execute(
                "SELECT * FROM operations WHERE deadline>? AND (state='queued' OR (state='running' AND lease_until<=?)) ORDER BY created,id LIMIT 1",
                (now, now),
            ).fetchone()
            if row is None:
                return None
            content = self._decrypt(row)
            owner = secrets.token_urlsafe(24)
            generation = row["generation"] + 1
            db.execute(
                "UPDATE operations SET state='running',owner=?,generation=?,lease_until=? WHERE id=?",
                (
                    owner,
                    generation,
                    min(now + lease_seconds, row["deadline"]),
                    row["id"],
                ),
            )
            return WorkerLease(
                row["id"], generation, owner, content["binding"], content["inputs"]
            )

    def renew(self, lease: WorkerLease, *, lease_seconds=30):
        if type(lease_seconds) is not int or not 1 <= lease_seconds <= 300:
            raise ValueError("Choose a bounded worker lease.")
        with self._transaction() as db:
            now = self.clock()
            return (
                db.execute(
                    "UPDATE operations SET lease_until=MIN(?,deadline) WHERE id=? AND state='running' AND owner=? AND generation=? AND lease_until>? AND deadline>?",
                    (
                        now + lease_seconds,
                        lease.operation_id,
                        lease.owner,
                        lease.generation,
                        now,
                        now,
                    ),
                ).rowcount
                == 1
            )

    def complete(self, lease: WorkerLease, result):
        validate_result(lease.binding["capability"], result)
        digest = sha256(json_bytes(result)).hexdigest()
        with self._transaction() as db:
            row, content = self._bound(db, lease.binding)
            if (
                row["state"] in {"completed", "failed"}
                and row["result_digest"] == digest
            ):
                return self._response(row, content)
            if (
                row["state"] != "running"
                or row["owner"] != lease.owner
                or row["generation"] != lease.generation
                or row["lease_until"] <= self.clock()
                or row["deadline"] <= self.clock()
            ):
                raise ProtocolError("Provider worker no longer owns this operation.")
            content["result"] = result
            # Input references/values are no longer needed after the result commits.
            content.pop("inputs", None)
            state = "failed" if result["status"] == "failed" else "completed"
            db.execute(
                "UPDATE operations SET state=?,content=?,result_digest=?,owner='',lease_until=0 WHERE id=?",
                (state, self._encrypt(row["id"], content), digest, row["id"]),
            )
            return {"binding": content["binding"], "status": state, "result": result}

    def control(self, binding, action):
        if action not in {"cancel", "delete"}:
            raise ProtocolError("Unsupported provider control.")
        with self._transaction() as db:
            row, content = self._bound(db, binding)
            if row["state"] == "deleted":
                return {
                    "binding": binding,
                    "status": "deleted" if action == "delete" else "cancelled",
                }
            state = "deleted" if action == "delete" else "cancelled"
            if action == "delete":
                content = {"binding_sha256": sha256(json_bytes(binding)).hexdigest()}
            db.execute(
                "UPDATE operations SET state=?,content=?,owner='',lease_until=0,result_digest='' WHERE id=?",
                (state, self._encrypt(row["id"], content), row["id"]),
            )
            return {"binding": binding, "status": state}

    def expire(self, *, limit=100):
        """Stop overdue work; cancellation preserves content until explicit deletion.

        Deployment retention/hold policy must separately schedule delete controls.
        Expiry cannot invent permission to destroy content under a legal hold.
        """
        if type(limit) is not int or not 1 <= limit <= 1000:
            raise ValueError("Choose a bounded expiry batch.")
        with self._transaction() as db:
            result = db.execute(
                "UPDATE operations SET state='expired',owner='',lease_until=0 WHERE id IN (SELECT id FROM operations WHERE deadline<=? AND state IN ('queued','running') ORDER BY deadline LIMIT ?)",
                (self.clock(), limit),
            )
            return result.rowcount
