import { DatabaseSync } from "node:sqlite";
import { createCipheriv, createDecipheriv, randomBytes } from "node:crypto";
import { openSync, closeSync, chmodSync, constants } from "node:fs";
import { inspect } from "node:util";
import { ProtocolError, jsonBytes, parseJson, digest } from "./wire.js";
import { bindingDigest, validateResult } from "./contracts.js";

export class StorageUnavailable extends Error {
  constructor() {
    super("Provider operation storage is unavailable.");
    this.name = "StorageUnavailable";
  }
}
export class WorkerLease {
  #owner;
  #binding;
  #inputs;
  constructor(id, generation, owner, binding, inputs) {
    this.operationId = id;
    this.generation = generation;
    this.#owner = owner;
    this.#binding = binding;
    this.#inputs = inputs;
    Object.freeze(this);
  }
  get owner() {
    return this.#owner;
  }
  get binding() {
    return this.#binding;
  }
  get inputs() {
    return this.#inputs;
  }
  toJSON() {
    return { operationId: this.operationId, generation: this.generation };
  }
  [inspect.custom]() {
    return `WorkerLease(${this.operationId}, generation=${this.generation})`;
  }
}
export class SQLiteStore {
  #db;
  #key;
  constructor(path, { encryptionKey, clock = () => Date.now() / 1000 }) {
    if (!Buffer.isBuffer(encryptionKey) || encryptionKey.length !== 32)
      throw new TypeError(
        "Supply a separate 32-byte provider-storage encryption key.",
      );
    const fd = openSync(
      path,
      constants.O_RDWR | constants.O_CREAT | constants.O_NOFOLLOW,
      0o600,
    );
    closeSync(fd);
    chmodSync(path, 0o600);
    this.#key = Buffer.from(encryptionKey);
    this.clock = clock;
    this.#db = new DatabaseSync(path);
    this.#db.exec(`PRAGMA busy_timeout=10000; PRAGMA journal_mode=WAL;
   CREATE TABLE IF NOT EXISTS nonces(digest TEXT PRIMARY KEY,expires REAL NOT NULL); CREATE INDEX IF NOT EXISTS nonce_expiry ON nonces(expires);
   CREATE TABLE IF NOT EXISTS operations(id TEXT PRIMARY KEY,configuration TEXT NOT NULL,deadline REAL NOT NULL,state TEXT NOT NULL,content BLOB NOT NULL,generation INTEGER NOT NULL DEFAULT 0,owner TEXT NOT NULL DEFAULT '',lease_until REAL NOT NULL DEFAULT 0,result_digest TEXT NOT NULL DEFAULT '',created REAL NOT NULL);
   CREATE INDEX IF NOT EXISTS operation_work ON operations(state,deadline,lease_until);`);
  }
  close() {
    this.#db.close();
    this.#key.fill(0);
  }
  transaction(callback) {
    this.#db.exec("BEGIN IMMEDIATE");
    try {
      const result = callback(this.#db);
      this.#db.exec("COMMIT");
      return result;
    } catch (error) {
      try {
        this.#db.exec("ROLLBACK");
      } catch {}
      throw error;
    }
  }
  encrypt(id, content) {
    const nonce = randomBytes(12),
      cipher = createCipheriv("aes-256-gcm", this.#key, nonce);
    cipher.setAAD(Buffer.from(id));
    return Buffer.concat([
      nonce,
      cipher.update(jsonBytes(content)),
      cipher.final(),
      cipher.getAuthTag(),
    ]);
  }
  decrypt(row) {
    try {
      const blob = Buffer.from(row.content),
        decipher = createDecipheriv(
          "aes-256-gcm",
          this.#key,
          blob.subarray(0, 12),
        );
      decipher.setAAD(Buffer.from(row.id));
      decipher.setAuthTag(blob.subarray(-16));
      return parseJson(
        Buffer.concat([
          decipher.update(blob.subarray(12, -16)),
          decipher.final(),
        ]),
      );
    } catch {
      throw new StorageUnavailable();
    }
  }
  claimNonce(hash, expires) {
    return this.transaction((db) => {
      db.prepare(
        "DELETE FROM nonces WHERE digest IN (SELECT digest FROM nonces WHERE expires <= ? LIMIT 256)",
      ).run(this.clock());
      return (
        db
          .prepare("INSERT OR IGNORE INTO nonces VALUES(?,?)")
          .run(hash, expires).changes === 1
      );
    });
  }
  matches(content, binding) {
    return (
      (content.binding
        ? bindingDigest(content.binding)
        : content.binding_sha256) === bindingDigest(binding)
    );
  }
  bound(db, binding) {
    const row = db
      .prepare("SELECT * FROM operations WHERE id=?")
      .get(binding.operation_id);
    if (!row) throw new ProtocolError("Provider operation is unavailable.");
    const content = this.decrypt(row);
    if (!this.matches(content, binding))
      throw new ProtocolError("Provider operation is unavailable.");
    return { row, content };
  }
  response(row, content, binding = content.binding) {
    if (["completed", "failed"].includes(row.state))
      return { binding, status: row.state, result: content.result };
    if (["cancelled", "deleted", "expired"].includes(row.state))
      return { binding, status: row.state };
    return { binding, status: "pending", retry_after_seconds: 10 };
  }
  admit(binding, inputs, deadline) {
    return this.transaction((db) => {
      const row = db
        .prepare("SELECT * FROM operations WHERE id=?")
        .get(binding.operation_id);
      if (row) {
        const content = this.decrypt(row);
        if (!this.matches(content, binding))
          throw new ProtocolError(
            "Operation admission conflicts with its existing binding.",
          );
        return this.response(row, content, binding);
      }
      db.prepare(
        "INSERT INTO operations(id,configuration,deadline,state,content,created) VALUES(?,?,?,?,?,?)",
      ).run(
        binding.operation_id,
        binding.configuration_id,
        deadline.getTime() / 1000,
        "queued",
        this.encrypt(binding.operation_id, { binding, inputs }),
        this.clock(),
      );
      return { binding, status: "pending", retry_after_seconds: 10 };
    });
  }
  poll(binding) {
    return this.transaction((db) => {
      const { row, content } = this.bound(db, binding);
      return this.response(row, content, binding);
    });
  }
  claimJob({ leaseSeconds = 30 } = {}) {
    if (
      !Number.isSafeInteger(leaseSeconds) ||
      leaseSeconds < 1 ||
      leaseSeconds > 300
    )
      throw new TypeError("Choose a bounded worker lease.");
    return this.transaction((db) => {
      const now = this.clock(),
        row = db
          .prepare(
            "SELECT * FROM operations WHERE deadline>? AND (state='queued' OR (state='running' AND lease_until<=?)) ORDER BY created,id LIMIT 1",
          )
          .get(now, now);
      if (!row) return null;
      const content = this.decrypt(row),
        owner = randomBytes(24).toString("base64url"),
        generation = row.generation + 1;
      db.prepare(
        "UPDATE operations SET state='running',owner=?,generation=?,lease_until=? WHERE id=?",
      ).run(
        owner,
        generation,
        Math.min(now + leaseSeconds, row.deadline),
        row.id,
      );
      return new WorkerLease(
        row.id,
        generation,
        owner,
        content.binding,
        content.inputs,
      );
    });
  }
  renew(lease, { leaseSeconds = 30 } = {}) {
    if (
      !Number.isSafeInteger(leaseSeconds) ||
      leaseSeconds < 1 ||
      leaseSeconds > 300
    )
      throw new TypeError("Choose a bounded worker lease.");
    return this.transaction((db) => {
      const now = this.clock();
      return (
        db
          .prepare(
            "UPDATE operations SET lease_until=MIN(?,deadline) WHERE id=? AND state='running' AND owner=? AND generation=? AND lease_until>? AND deadline>?",
          )
          .run(
            now + leaseSeconds,
            lease.operationId,
            lease.owner,
            lease.generation,
            now,
            now,
          ).changes === 1
      );
    });
  }
  complete(lease, result) {
    validateResult(lease.binding.capability, result);
    const hash = digest(jsonBytes(result));
    return this.transaction((db) => {
      const { row, content } = this.bound(db, lease.binding);
      if (
        ["completed", "failed"].includes(row.state) &&
        row.result_digest === hash
      )
        return this.response(row, content);
      if (
        row.state !== "running" ||
        row.owner !== lease.owner ||
        row.generation !== lease.generation ||
        row.lease_until <= this.clock() ||
        row.deadline <= this.clock()
      )
        throw new ProtocolError(
          "Provider worker no longer owns this operation.",
        );
      delete content.inputs;
      content.result = result;
      const state = result.status === "failed" ? "failed" : "completed";
      db.prepare(
        "UPDATE operations SET state=?,content=?,result_digest=?,owner='',lease_until=0 WHERE id=?",
      ).run(state, this.encrypt(row.id, content), hash, row.id);
      return { binding: content.binding, status: state, result };
    });
  }
  control(binding, action) {
    if (!["cancel", "delete"].includes(action))
      throw new ProtocolError("Unsupported provider control.");
    return this.transaction((db) => {
      const { row, content } = this.bound(db, binding);
      if (row.state === "deleted")
        return {
          binding,
          status: action === "delete" ? "deleted" : "cancelled",
        };
      const state = action === "delete" ? "deleted" : "cancelled",
        retained =
          action === "delete"
            ? { binding_sha256: bindingDigest(binding) }
            : content;
      db.prepare(
        "UPDATE operations SET state=?,content=?,owner='',lease_until=0,result_digest='' WHERE id=?",
      ).run(state, this.encrypt(row.id, retained), row.id);
      return { binding, status: state };
    });
  }
  expire({ limit = 100 } = {}) {
    if (!Number.isSafeInteger(limit) || limit < 1 || limit > 1000)
      throw new TypeError("Choose a bounded expiry batch.");
    return this.transaction(
      (db) =>
        db
          .prepare(
            "UPDATE operations SET state='expired',owner='',lease_until=0 WHERE id IN (SELECT id FROM operations WHERE deadline<=? AND state IN ('queued','running') ORDER BY deadline LIMIT ?)",
          )
          .run(this.clock(), limit).changes,
    );
  }
}
