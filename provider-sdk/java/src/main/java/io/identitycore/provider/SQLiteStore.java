package io.identitycore.provider;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.nio.file.attribute.PosixFilePermissions;
import java.security.MessageDigest;
import java.security.SecureRandom;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.time.Instant;
import java.util.Arrays;
import java.util.function.DoubleSupplier;
import javax.crypto.Cipher;
import javax.crypto.spec.GCMParameterSpec;
import javax.crypto.spec.SecretKeySpec;

/** Encrypted local single-host SQLite/WAL reference implementation. */
public final class SQLiteStore implements OperationStore, AutoCloseable {
  private final Path path;
  private final byte[] key;
  private final DoubleSupplier clock;

  private record Row(
      String id,
      double deadline,
      String state,
      byte[] content,
      long generation,
      String owner,
      double leaseUntil,
      String resultDigest) {}

  @FunctionalInterface
  private interface Work<T> {
    T run(Connection db) throws Exception;
  }

  public SQLiteStore(Path path, byte[] encryptionKey) {
    this(path, encryptionKey, () -> System.currentTimeMillis() / 1000.0);
  }

  public SQLiteStore(Path path, byte[] encryptionKey, DoubleSupplier clock) {
    if (encryptionKey.length != 32)
      throw new IllegalArgumentException(
          "Supply a separate 32-byte provider-storage encryption key.");
    this.path = path.toAbsolutePath();
    this.key = encryptionKey.clone();
    this.clock = clock;
    try {
      try (FileChannel ignored =
          FileChannel.open(
              this.path,
              StandardOpenOption.CREATE,
              StandardOpenOption.READ,
              StandardOpenOption.WRITE,
              LinkOption.NOFOLLOW_LINKS)) {}
      try {
        Files.setPosixFilePermissions(this.path, PosixFilePermissions.fromString("rw-------"));
      } catch (UnsupportedOperationException ignored) {
      }
      try (Connection db = connection();
          var statement = db.createStatement()) {
        statement.execute("PRAGMA journal_mode=WAL");
        statement.execute(
            "CREATE TABLE IF NOT EXISTS nonces(digest TEXT PRIMARY KEY,expires REAL NOT NULL)");
        statement.execute("CREATE INDEX IF NOT EXISTS nonce_expiry ON nonces(expires)");
        statement.execute(
            "CREATE TABLE IF NOT EXISTS operations(id TEXT PRIMARY KEY,configuration TEXT NOT"
                + " NULL,deadline REAL NOT NULL,state TEXT NOT NULL,content BLOB NOT"
                + " NULL,generation INTEGER NOT NULL DEFAULT 0,owner TEXT NOT NULL DEFAULT"
                + " '',lease_until REAL NOT NULL DEFAULT 0,result_digest TEXT NOT NULL DEFAULT"
                + " '',created REAL NOT NULL)");
        statement.execute(
            "CREATE INDEX IF NOT EXISTS operation_work ON operations(state,deadline,lease_until)");
      }
    } catch (Exception ignored) {
      throw new StorageUnavailable();
    }
  }

  private Connection connection() throws SQLException {
    Connection db = DriverManager.getConnection("jdbc:sqlite:" + path);
    try (var statement = db.createStatement()) {
      statement.execute("PRAGMA busy_timeout=10000");
    }
    return db;
  }

  private <T> T transaction(Work<T> work) {
    try (Connection db = connection();
        var statement = db.createStatement()) {
      statement.execute("BEGIN IMMEDIATE");
      try {
        T result = work.run(db);
        statement.execute("COMMIT");
        return result;
      } catch (Exception error) {
        try {
          statement.execute("ROLLBACK");
        } catch (SQLException ignored) {
        }
        if (error instanceof ProtocolError failure) throw failure;
        throw new StorageUnavailable();
      }
    } catch (SQLException ignored) {
      throw new StorageUnavailable();
    }
  }

  private static PreparedStatement prepared(Connection db, String sql, Object... values)
      throws SQLException {
    PreparedStatement query = db.prepareStatement(sql);
    for (int index = 0; index < values.length; index++) query.setObject(index + 1, values[index]);
    return query;
  }

  private static int update(Connection db, String sql, Object... values) throws SQLException {
    try (var query = prepared(db, sql, values)) {
      return query.executeUpdate();
    }
  }

  private static Row select(Connection db, String sql, Object... values) throws SQLException {
    try (var query = prepared(db, sql, values);
        ResultSet result = query.executeQuery()) {
      if (!result.next()) return null;
      return new Row(
          result.getString("id"),
          result.getDouble("deadline"),
          result.getString("state"),
          result.getBytes("content"),
          result.getLong("generation"),
          result.getString("owner"),
          result.getDouble("lease_until"),
          result.getString("result_digest"));
    }
  }

  private byte[] encrypt(String id, ObjectNode content) {
    try {
      byte[] nonce = new byte[12];
      new SecureRandom().nextBytes(nonce);
      Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
      cipher.init(
          Cipher.ENCRYPT_MODE, new SecretKeySpec(key, "AES"), new GCMParameterSpec(128, nonce));
      cipher.updateAAD(id.getBytes(StandardCharsets.UTF_8));
      byte[] encrypted = cipher.doFinal(Wire.bytes(content));
      return ByteBuffer.allocate(nonce.length + encrypted.length).put(nonce).put(encrypted).array();
    } catch (Exception ignored) {
      throw new StorageUnavailable();
    }
  }

  private ObjectNode decrypt(Row row) {
    try {
      byte[] nonce = Arrays.copyOfRange(row.content, 0, 12);
      Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
      cipher.init(
          Cipher.DECRYPT_MODE, new SecretKeySpec(key, "AES"), new GCMParameterSpec(128, nonce));
      cipher.updateAAD(row.id.getBytes(StandardCharsets.UTF_8));
      return Wire.parse(cipher.doFinal(Arrays.copyOfRange(row.content, 12, row.content.length)));
    } catch (Exception ignored) {
      throw new StorageUnavailable();
    }
  }

  private boolean matches(ObjectNode content, ObjectNode binding) {
    String hash =
        content.has("binding")
            ? Contracts.bindingDigest(content.get("binding"))
            : content.path("binding_sha256").asText();
    return MessageDigest.isEqual(
        hash.getBytes(StandardCharsets.US_ASCII),
        Contracts.bindingDigest(binding).getBytes(StandardCharsets.US_ASCII));
  }

  private Row bound(Connection db, ObjectNode binding) throws SQLException {
    Row row =
        select(db, "SELECT * FROM operations WHERE id=?", binding.path("operation_id").asText());
    if (row == null || !matches(decrypt(row), binding))
      throw new ProtocolError("Provider operation is unavailable.");
    return row;
  }

  private ObjectNode response(Row row, ObjectNode content, ObjectNode binding) {
    ObjectNode output = Wire.JSON.createObjectNode();
    output.set("binding", binding);
    if (row.state.equals("completed") || row.state.equals("failed")) {
      output.put("status", row.state);
      output.set("result", content.get("result"));
    } else if (java.util.Set.of("cancelled", "deleted", "expired").contains(row.state))
      output.put("status", row.state);
    else output.put("status", "pending").put("retry_after_seconds", 10);
    return output;
  }

  @Override
  public boolean claimNonce(String digest, long expiresAt) {
    return transaction(
        db -> {
          update(
              db,
              "DELETE FROM nonces WHERE digest IN (SELECT digest FROM nonces WHERE expires<=? LIMIT"
                  + " 256)",
              clock.getAsDouble());
          return update(db, "INSERT OR IGNORE INTO nonces VALUES(?,?)", digest, expiresAt) == 1;
        });
  }

  @Override
  public ObjectNode admit(ObjectNode binding, ObjectNode inputs, Instant deadline) {
    return transaction(
        db -> {
          String id = binding.path("operation_id").asText();
          Row row = select(db, "SELECT * FROM operations WHERE id=?", id);
          if (row != null) {
            ObjectNode content = decrypt(row);
            if (!matches(content, binding))
              throw new ProtocolError("Operation admission conflicts with its existing binding.");
            return response(row, content, binding);
          }
          ObjectNode content = Wire.JSON.createObjectNode();
          content.set("binding", binding);
          content.set("inputs", inputs);
          update(
              db,
              "INSERT INTO operations(id,configuration,deadline,state,content,created)"
                  + " VALUES(?,?,?,?,?,?)",
              id,
              binding.path("configuration_id").asText(),
              deadline.toEpochMilli() / 1000.0,
              "queued",
              encrypt(id, content),
              clock.getAsDouble());
          ObjectNode output = Wire.JSON.createObjectNode();
          output.set("binding", binding);
          return output.put("status", "pending").put("retry_after_seconds", 10);
        });
  }

  @Override
  public ObjectNode poll(ObjectNode binding) {
    return transaction(
        db -> {
          Row row = bound(db, binding);
          return response(row, decrypt(row), binding);
        });
  }

  private static void leaseLimit(int seconds) {
    if (seconds < 1 || seconds > 300)
      throw new IllegalArgumentException("Choose a bounded worker lease.");
  }

  @Override
  public WorkerLease claimJob(int leaseSeconds) {
    leaseLimit(leaseSeconds);
    return transaction(
        db -> {
          double now = clock.getAsDouble();
          Row row =
              select(
                  db,
                  "SELECT * FROM operations WHERE deadline>? AND (state='queued' OR"
                      + " (state='running' AND lease_until<=?)) ORDER BY created,id LIMIT 1",
                  now,
                  now);
          if (row == null) return null;
          ObjectNode content = decrypt(row);
          String owner = Wire.randomToken();
          long generation = row.generation + 1;
          update(
              db,
              "UPDATE operations SET state='running',owner=?,generation=?,lease_until=? WHERE id=?",
              owner,
              generation,
              Math.min(now + leaseSeconds, row.deadline),
              row.id);
          return new WorkerLease(
              row.id,
              generation,
              owner,
              (ObjectNode) content.get("binding"),
              (ObjectNode) content.get("inputs"));
        });
  }

  @Override
  public boolean renew(WorkerLease lease, int leaseSeconds) {
    leaseLimit(leaseSeconds);
    return transaction(
        db -> {
          double now = clock.getAsDouble();
          return update(
                  db,
                  "UPDATE operations SET lease_until=MIN(?,deadline) WHERE id=? AND state='running'"
                      + " AND owner=? AND generation=? AND lease_until>? AND deadline>?",
                  now + leaseSeconds,
                  lease.operationId(),
                  lease.owner(),
                  lease.generation(),
                  now,
                  now)
              == 1;
        });
  }

  @Override
  public ObjectNode complete(WorkerLease lease, ObjectNode result) {
    Contracts.validateResult(lease.binding().path("capability").asText(), result);
    String hash = Wire.digest(Wire.bytes(Wire.canonical(result)));
    return transaction(
        db -> {
          Row row = bound(db, lease.binding());
          ObjectNode content = decrypt(row);
          if (java.util.Set.of("completed", "failed").contains(row.state)
              && row.resultDigest.equals(hash)) return response(row, content, lease.binding());
          double now = clock.getAsDouble();
          if (!row.state.equals("running")
              || !row.owner.equals(lease.owner())
              || row.generation != lease.generation()
              || row.leaseUntil <= now
              || row.deadline <= now)
            throw new ProtocolError("Provider worker no longer owns this operation.");
          content.remove("inputs");
          content.set("result", result);
          String state = result.path("status").asText().equals("failed") ? "failed" : "completed";
          update(
              db,
              "UPDATE operations SET state=?,content=?,result_digest=?,owner='',lease_until=0 WHERE"
                  + " id=?",
              state,
              encrypt(row.id, content),
              hash,
              row.id);
          ObjectNode output = Wire.JSON.createObjectNode();
          output.set("binding", lease.binding());
          output.set("result", result);
          return output.put("status", state);
        });
  }

  @Override
  public ObjectNode control(ObjectNode binding, String action) {
    if (!java.util.Set.of("cancel", "delete").contains(action))
      throw new ProtocolError("Unsupported provider control.");
    return transaction(
        db -> {
          Row row = bound(db, binding);
          ObjectNode output = Wire.JSON.createObjectNode();
          output.set("binding", binding);
          String state = action.equals("delete") ? "deleted" : "cancelled";
          if (row.state.equals("deleted")) return output.put("status", state);
          ObjectNode content =
              action.equals("delete")
                  ? Wire.JSON
                      .createObjectNode()
                      .put("binding_sha256", Contracts.bindingDigest(binding))
                  : decrypt(row);
          update(
              db,
              "UPDATE operations SET state=?,content=?,owner='',lease_until=0,result_digest=''"
                  + " WHERE id=?",
              state,
              encrypt(row.id, content),
              row.id);
          return output.put("status", state);
        });
  }

  public int expire(int limit) {
    if (limit < 1 || limit > 1000)
      throw new IllegalArgumentException("Choose a bounded expiry batch.");
    return transaction(
        db ->
            update(
                db,
                "UPDATE operations SET state='expired',owner='',lease_until=0 WHERE id IN (SELECT"
                    + " id FROM operations WHERE deadline<=? AND state IN ('queued','running')"
                    + " ORDER BY deadline LIMIT ?)",
                clock.getAsDouble(),
                limit));
  }

  @Override
  public void close() {
    Arrays.fill(key, (byte) 0);
  }
}
