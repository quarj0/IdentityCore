package io.identitycore;

import com.fasterxml.jackson.databind.JsonNode;

public final class IdentityCoreApiException extends IdentityCoreException {
    private final String code;
    private final int status;
    private final String requestId;
    private final JsonNode details;

    public IdentityCoreApiException(String message, String code, int status, String requestId, JsonNode details) {
        super(message); this.code = code; this.status = status; this.requestId = requestId; this.details = details;
    }
    public String code() { return code; }
    public int status() { return status; }
    public String requestId() { return requestId; }
    public JsonNode details() { return details; }
}

