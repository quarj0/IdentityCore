using System.Security.Cryptography;
using System.Text;
using System.Text.Json.Nodes;
using System.Text.Json.Serialization;
using Microsoft.Data.Sqlite;

namespace IdentityCore.Provider;

public sealed class WorkerLease(string operationId, long generation, string owner, JsonObject binding, JsonObject inputs)
{
    public string OperationId { get; } = operationId;
    public long Generation { get; } = generation;
    [JsonIgnore] public string Owner { get; } = owner;
    [JsonIgnore] public JsonObject Binding { get; } = binding;
    [JsonIgnore] public JsonObject Inputs { get; } = inputs;
    public override string ToString() => $"ProviderWorkerLease({OperationId}, {Generation})";
}

/// <summary>Use a shared transactional implementation for multi-host deployments.</summary>
public interface IOperationStore
{
    Task<bool> ClaimNonceAsync(string digest, long expiresAt);
    Task<JsonObject> AdmitAsync(JsonObject binding, JsonObject inputs, DateTimeOffset deadline);
    Task<JsonObject> PollAsync(JsonObject binding);
    Task<WorkerLease?> ClaimJobAsync(int leaseSeconds);
    Task<bool> RenewAsync(WorkerLease lease, int leaseSeconds);
    Task<JsonObject> CompleteAsync(WorkerLease lease, JsonObject result);
    Task<JsonObject> ControlAsync(JsonObject binding, string action);
}

/// <summary>Encrypted SQLite/WAL reference store for a private directory on one host.</summary>
public sealed class SQLiteStore : IOperationStore, IDisposable
{
    private readonly string connectionString;
    private readonly byte[] key;
    private readonly Func<double> clock;
    private bool disposed;
    private sealed record Row(string Id, double Deadline, string State, byte[] Content, long Generation, string Owner, double LeaseUntil, string ResultDigest);
    public SQLiteStore(string path, byte[] encryptionKey, Func<double>? clock = null)
    {
        if (encryptionKey.Length != 32) throw new ArgumentException("Supply a separate 32-byte provider-storage encryption key.");
        this.key = (byte[])encryptionKey.Clone(); this.clock = clock ?? (() => DateTimeOffset.UtcNow.ToUnixTimeMilliseconds() / 1000.0);
        try
        {
            var fullPath = Path.GetFullPath(path);
            // Store in a private directory: SQLite also opens WAL/SHM sidecars here.
            if (File.Exists(fullPath) && new FileInfo(fullPath).LinkTarget is not null) throw new StorageUnavailable();
            using (var file = new FileStream(fullPath, FileMode.OpenOrCreate, FileAccess.ReadWrite, FileShare.ReadWrite)) { }
            if (!OperatingSystem.IsWindows()) File.SetUnixFileMode(fullPath, UnixFileMode.UserRead | UnixFileMode.UserWrite);
            connectionString = new SqliteConnectionStringBuilder { DataSource = fullPath, Pooling = false, DefaultTimeout = 10 }.ToString();
            using var db = Connection();
            Execute(db, null, "PRAGMA journal_mode=WAL");
            Execute(db, null, "CREATE TABLE IF NOT EXISTS nonces(digest TEXT PRIMARY KEY,expires REAL NOT NULL)");
            Execute(db, null, "CREATE INDEX IF NOT EXISTS nonce_expiry ON nonces(expires)");
            Execute(db, null, "CREATE TABLE IF NOT EXISTS operations(id TEXT PRIMARY KEY,configuration TEXT NOT NULL,deadline REAL NOT NULL,state TEXT NOT NULL,content BLOB NOT NULL,generation INTEGER NOT NULL DEFAULT 0,owner TEXT NOT NULL DEFAULT '',lease_until REAL NOT NULL DEFAULT 0,result_digest TEXT NOT NULL DEFAULT '',created REAL NOT NULL)");
            Execute(db, null, "CREATE INDEX IF NOT EXISTS operation_work ON operations(state,deadline,lease_until)");
        }
        catch { CryptographicOperations.ZeroMemory(this.key); throw new StorageUnavailable(); }
    }
    private SqliteConnection Connection()
    {
        if (disposed) throw new StorageUnavailable();
        var db = new SqliteConnection(connectionString); db.Open(); return db;
    }
    private T Transaction<T>(Func<SqliteConnection, SqliteTransaction, T> work)
    {
        try
        {
            using var db = Connection(); using var transaction = db.BeginTransaction(deferred: false);
            var result = work(db, transaction); transaction.Commit(); return result;
        }
        catch (ProtocolError) { throw; }
        catch { throw new StorageUnavailable(); }
    }
    private static SqliteCommand Command(SqliteConnection db, SqliteTransaction? tx, string sql, params object[] values)
    {
        var command = db.CreateCommand(); command.Transaction = tx;
        // Positional '?' placeholders are replaced with named parameters without interpolating values.
        for (var index = 0; index < values.Length; index++)
        {
            var offset = sql.IndexOf('?'); if (offset < 0) throw new StorageUnavailable();
            var name = "$v" + index; sql = sql[..offset] + name + sql[(offset + 1)..]; command.Parameters.AddWithValue(name, values[index]);
        }
        command.CommandText = sql; return command;
    }
    private static int Execute(SqliteConnection db, SqliteTransaction? tx, string sql, params object[] values) { using var command = Command(db, tx, sql, values); return command.ExecuteNonQuery(); }
    private static Row? Select(SqliteConnection db, SqliteTransaction tx, string sql, params object[] values)
    {
        using var command = Command(db, tx, sql, values); using var reader = command.ExecuteReader(); if (!reader.Read()) return null;
        return new Row(reader.GetString(reader.GetOrdinal("id")), reader.GetDouble(reader.GetOrdinal("deadline")), reader.GetString(reader.GetOrdinal("state")), (byte[])reader["content"], reader.GetInt64(reader.GetOrdinal("generation")), reader.GetString(reader.GetOrdinal("owner")), reader.GetDouble(reader.GetOrdinal("lease_until")), reader.GetString(reader.GetOrdinal("result_digest")));
    }
    private byte[] Encrypt(string id, JsonObject content)
    {
        var plain = Wire.Bytes(content); var nonce = RandomNumberGenerator.GetBytes(12); var encrypted = new byte[plain.Length]; var tag = new byte[16];
        using var cipher = new AesGcm(key, 16); cipher.Encrypt(nonce, plain, encrypted, tag, Encoding.UTF8.GetBytes(id));
        return [.. nonce, .. encrypted, .. tag];
    }
    private JsonObject Decrypt(Row row)
    {
        if (row.Content.Length < 28) throw new StorageUnavailable(); var plain = new byte[row.Content.Length - 28]; using var cipher = new AesGcm(key, 16);
        cipher.Decrypt(row.Content.AsSpan(0, 12), row.Content.AsSpan(12, plain.Length), row.Content.AsSpan(12 + plain.Length, 16), plain, Encoding.UTF8.GetBytes(row.Id));
        try { return Wire.Parse(plain); } finally { CryptographicOperations.ZeroMemory(plain); }
    }
    private static bool Matches(JsonObject content, JsonObject binding)
    {
        var hash = content["binding"] is JsonObject saved ? Contracts.BindingDigest(saved) : Contracts.Text(content["binding_sha256"]);
        return CryptographicOperations.FixedTimeEquals(Encoding.ASCII.GetBytes(hash), Encoding.ASCII.GetBytes(Contracts.BindingDigest(binding)));
    }
    private Row Bound(SqliteConnection db, SqliteTransaction tx, JsonObject binding)
    {
        var row = Select(db, tx, "SELECT * FROM operations WHERE id=?", Contracts.Text(binding["operation_id"]));
        if (row is null || !Matches(Decrypt(row), binding)) throw new ProtocolError("Provider operation is unavailable."); return row;
    }
    private static JsonObject Response(Row row, JsonObject content, JsonObject binding)
    {
        var result = new JsonObject { ["binding"] = binding.DeepClone() };
        if (row.State is "completed" or "failed") { result["status"] = row.State; result["result"] = content["result"]?.DeepClone(); }
        else if (row.State is "cancelled" or "deleted" or "expired") result["status"] = row.State;
        else { result["status"] = "pending"; result["retry_after_seconds"] = 10; } return result;
    }
    public Task<bool> ClaimNonceAsync(string digest, long expiresAt) => Task.FromResult(Transaction((db, tx) =>
    {
        Execute(db, tx, "DELETE FROM nonces WHERE digest IN (SELECT digest FROM nonces WHERE expires<=? LIMIT 256)", clock());
        return Execute(db, tx, "INSERT OR IGNORE INTO nonces VALUES(?,?)", digest, expiresAt) == 1;
    }));
    public Task<JsonObject> AdmitAsync(JsonObject binding, JsonObject inputs, DateTimeOffset deadline) => Task.FromResult(Transaction((db, tx) =>
    {
        var id = Contracts.Text(binding["operation_id"]); var row = Select(db, tx, "SELECT * FROM operations WHERE id=?", id);
        if (row is not null) { var content = Decrypt(row); if (!Matches(content, binding)) throw new ProtocolError("Operation admission conflicts with its existing binding."); return Response(row, content, binding); }
        var record = new JsonObject { ["binding"] = binding.DeepClone(), ["inputs"] = inputs.DeepClone() };
        Execute(db, tx, "INSERT INTO operations(id,configuration,deadline,state,content,created) VALUES(?,?,?,?,?,?)", id, Contracts.Text(binding["configuration_id"]), deadline.ToUnixTimeMilliseconds() / 1000.0, "queued", Encrypt(id, record), clock());
        return new JsonObject { ["binding"] = binding.DeepClone(), ["status"] = "pending", ["retry_after_seconds"] = 10 };
    }));
    public Task<JsonObject> PollAsync(JsonObject binding) => Task.FromResult(Transaction((db, tx) => { var row = Bound(db, tx, binding); return Response(row, Decrypt(row), binding); }));
    private static void LeaseLimit(int seconds) { if (seconds < 1 || seconds > 300) throw new ArgumentException("Choose a bounded worker lease."); }
    public Task<WorkerLease?> ClaimJobAsync(int leaseSeconds)
    {
        LeaseLimit(leaseSeconds); return Task.FromResult(Transaction<WorkerLease?>((db, tx) =>
        {
            var now = clock(); var row = Select(db, tx, "SELECT * FROM operations WHERE deadline>? AND (state='queued' OR (state='running' AND lease_until<=?)) ORDER BY created,id LIMIT 1", now, now); if (row is null) return null;
            var content = Decrypt(row); var owner = Wire.RandomToken(); var generation = row.Generation + 1;
            Execute(db, tx, "UPDATE operations SET state='running',owner=?,generation=?,lease_until=? WHERE id=?", owner, generation, Math.Min(now + leaseSeconds, row.Deadline), row.Id);
            return new WorkerLease(row.Id, generation, owner, (JsonObject)content["binding"]!, (JsonObject)content["inputs"]!);
        }));
    }
    public Task<bool> RenewAsync(WorkerLease lease, int leaseSeconds)
    {
        LeaseLimit(leaseSeconds); return Task.FromResult(Transaction((db, tx) => { var now = clock(); return Execute(db, tx, "UPDATE operations SET lease_until=MIN(?,deadline) WHERE id=? AND state='running' AND owner=? AND generation=? AND lease_until>? AND deadline>?", now + leaseSeconds, lease.OperationId, lease.Owner, lease.Generation, now, now) == 1; }));
    }
    public Task<JsonObject> CompleteAsync(WorkerLease lease, JsonObject result)
    {
        Contracts.ValidateResult(Contracts.Text(lease.Binding["capability"]), result); var hash = Wire.Digest(Wire.Bytes(Wire.Canonical(result)));
        return Task.FromResult(Transaction((db, tx) =>
        {
            var row = Bound(db, tx, lease.Binding); var content = Decrypt(row);
            if ((row.State is "completed" or "failed") && row.ResultDigest == hash) return Response(row, content, lease.Binding);
            var now = clock(); if (row.State != "running" || row.Owner != lease.Owner || row.Generation != lease.Generation || row.LeaseUntil <= now || row.Deadline <= now) throw new ProtocolError("Provider worker no longer owns this operation.");
            content.Remove("inputs"); content["result"] = result.DeepClone(); var state = Contracts.Text(result["status"]) == "failed" ? "failed" : "completed";
            Execute(db, tx, "UPDATE operations SET state=?,content=?,result_digest=?,owner='',lease_until=0 WHERE id=?", state, Encrypt(row.Id, content), hash, row.Id);
            return new JsonObject { ["binding"] = lease.Binding.DeepClone(), ["result"] = result.DeepClone(), ["status"] = state };
        }));
    }
    public Task<JsonObject> ControlAsync(JsonObject binding, string action)
    {
        if (action is not ("cancel" or "delete")) throw new ProtocolError("Unsupported provider control.");
        return Task.FromResult(Transaction((db, tx) =>
        {
            var row = Bound(db, tx, binding); var state = action == "delete" ? "deleted" : "cancelled";
            if (row.State != "deleted")
            {
                var content = action == "delete" ? new JsonObject { ["binding_sha256"] = Contracts.BindingDigest(binding) } : Decrypt(row);
                Execute(db, tx, "UPDATE operations SET state=?,content=?,owner='',lease_until=0,result_digest='' WHERE id=?", state, Encrypt(row.Id, content), row.Id);
            }
            return new JsonObject { ["binding"] = binding.DeepClone(), ["status"] = state };
        }));
    }
    public Task<int> ExpireAsync(int limit = 100)
    {
        if (limit < 1 || limit > 1000) throw new ArgumentException("Choose a bounded expiry batch.");
        return Task.FromResult(Transaction((db, tx) => Execute(db, tx, "UPDATE operations SET state='expired',owner='',lease_until=0 WHERE id IN (SELECT id FROM operations WHERE deadline<=? AND state IN ('queued','running') ORDER BY deadline LIMIT ?)", clock(), limit)));
    }
    public void Dispose() { disposed = true; CryptographicOperations.ZeroMemory(key); }
}
