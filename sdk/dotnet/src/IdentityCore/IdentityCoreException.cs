using System.Text.Json;

namespace IdentityCore;

public class IdentityCoreException : Exception
{
    public IdentityCoreException(string message, Exception? inner = null) : base(message, inner) { }
}

public sealed class IdentityCoreApiException : IdentityCoreException
{
    public string Code { get; }
    public int Status { get; }
    public string RequestId { get; }
    public JsonElement Details { get; }

    public IdentityCoreApiException(string message, string code, int status, string requestId, JsonElement details)
        : base(message) => (Code, Status, RequestId, Details) = (code, status, requestId, details);
}

public class IdentityCoreConnectionException : IdentityCoreException
{
    public IdentityCoreConnectionException(string message, Exception? inner = null) : base(message, inner) { }
}

public sealed class IdentityCoreTimeoutException : IdentityCoreConnectionException
{
    public IdentityCoreTimeoutException(string message, Exception? inner = null) : base(message, inner) { }
}
