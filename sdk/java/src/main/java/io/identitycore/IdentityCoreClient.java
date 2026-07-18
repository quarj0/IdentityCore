package io.identitycore;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.net.URI;
import java.net.URLEncoder;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

public final class IdentityCoreClient {
    public static final String VERSION = "0.2.0";
    private static final List<Integer> RETRYABLE = List.of(408, 429, 500, 502, 503, 504);
    private final URI apiOrigin; private final String clientId; private final String clientSecret;
    private final Duration timeout; private final int maxRetries; private final Duration retryBackoff;
    private final ObjectMapper json; private final Transport transport;
    public final Policies policies = new Policies(); public final Verifications verifications = new Verifications();

    public static Builder builder() { return new Builder(); }
    private IdentityCoreClient(Builder b) {
        if (b.apiOrigin == null || !b.apiOrigin.isAbsolute() || b.apiOrigin.getHost() == null || !List.of("http", "https").contains(b.apiOrigin.getScheme())) throw new IdentityCoreException("apiOrigin must be an absolute HTTP(S) URL.");
        if (b.clientId == null || b.clientId.isBlank() || b.clientSecret == null || b.clientSecret.isBlank()) throw new IdentityCoreException("clientId and clientSecret are required.");
        if (b.timeout.isZero() || b.timeout.isNegative() || b.maxRetries < 0 || b.retryBackoff.isNegative()) throw new IdentityCoreException("Retry and timeout settings are invalid.");
        this.apiOrigin = URI.create(b.apiOrigin.toString().replaceAll("/$", "")); this.clientId=b.clientId; this.clientSecret=b.clientSecret;
        this.timeout=b.timeout; this.maxRetries=b.maxRetries; this.retryBackoff=b.retryBackoff; this.json=b.json; this.transport=b.transport != null ? b.transport : defaultTransport();
    }

    public JsonNode health() { return request("GET", "/health", null, null); }

    public JsonNode request(String method, String path, JsonNode body, String idempotencyKey) {
        method = method.toUpperCase();
        boolean retryableMethod = List.of("GET", "HEAD", "OPTIONS").contains(method) || (idempotencyKey != null && !idempotencyKey.isBlank());
        String requestId = "req_" + UUID.randomUUID().toString().replace("-", "");
        Map<String,String> headers = new LinkedHashMap<>();
        headers.put("Accept", "application/json"); headers.put("Authorization", "Bearer " + clientSecret); headers.put("X-Client-Id", clientId);
        headers.put("X-Request-Id", requestId); headers.put("User-Agent", "identitycore-java/" + VERSION);
        if (body != null) headers.put("Content-Type", "application/json");
        if (idempotencyKey != null && !idempotencyKey.isBlank()) headers.put("Idempotency-Key", idempotencyKey);
        String encoded = body == null ? null : body.toString();
        for (int attempt=0; attempt<=maxRetries; attempt++) {
            try {
                RawResponse response = transport.send(method, URI.create(apiOrigin + "/api/v1" + path), headers, encoded, timeout);
                if (retryableMethod && RETRYABLE.contains(response.status()) && attempt < maxRetries) { pause(attempt); continue; }
                return parse(response);
            } catch (IOException error) {
                if (retryableMethod && attempt < maxRetries) { pause(attempt); continue; }
                throw new IdentityCoreException("Could not connect to IdentityCore.", error);
            } catch (InterruptedException error) { Thread.currentThread().interrupt(); throw new IdentityCoreException("The request was interrupted.", error); }
        }
        throw new IdentityCoreException("Could not connect to IdentityCore.");
    }

    private JsonNode parse(RawResponse response) {
        final JsonNode envelope;
        try { envelope = json.readTree(response.body()); } catch (JsonProcessingException error) { throw new IdentityCoreApiException("The service returned an invalid response.", "invalid_response", response.status(), "", json.createObjectNode()); }
        if (response.status() >= 400 || !envelope.path("success").asBoolean(false)) {
            JsonNode error = envelope.path("error");
            throw new IdentityCoreApiException(error.path("message").asText("Request failed."), error.path("code").asText("request_failed"), response.status(), envelope.path("request_id").asText(""), error.path("details"));
        }
        return envelope.path("data");
    }
    private void pause(int attempt) { try { Thread.sleep(retryBackoff.toMillis() * (1L << attempt)); } catch (InterruptedException e) { Thread.currentThread().interrupt(); throw new IdentityCoreException("Retry interrupted.", e); } }
    private Transport defaultTransport() {
        HttpClient http = HttpClient.newBuilder().connectTimeout(timeout).build();
        return (method, uri, headers, body, requestTimeout) -> {
            HttpRequest.Builder request = HttpRequest.newBuilder(uri).timeout(requestTimeout);
            headers.forEach(request::header);
            request.method(method, body == null ? HttpRequest.BodyPublishers.noBody() : HttpRequest.BodyPublishers.ofString(body));
            HttpResponse<String> response = http.send(request.build(), HttpResponse.BodyHandlers.ofString());
            return new RawResponse(response.statusCode(), response.body());
        };
    }

    public final class Policies {
        public JsonNode list() { return request("GET", "/policies/", null, null); }
        public JsonNode retrieve(String id) { return request("GET", "/policies/" + segment(id), null, null); }
    }
    public final class Verifications {
        public JsonNode create(JsonNode input) { return create(input, "ik_" + UUID.randomUUID().toString().replace("-", "")); }
        public JsonNode create(JsonNode input, String idempotencyKey) { return request("POST", "/verifications/", input, idempotencyKey); }
        public JsonNode list(String status, String externalReference, Integer page, Integer pageSize) {
            Map<String,Object> q = new LinkedHashMap<>(); q.put("status",status); q.put("external_reference",externalReference); q.put("page",page); q.put("page_size",pageSize);
            return request("GET", "/verifications/" + query(q), null, null);
        }
        public Iterable<JsonNode> iterate(String status, String externalReference, int pageSize) {
            return () -> new java.util.Iterator<>() { int page=1,index=0,totalPages=1; JsonNode items=json.createArrayNode();
                public boolean hasNext() { loadIfNeeded(); return index < items.size(); }
                public JsonNode next() { loadIfNeeded(); if(index>=items.size()) throw new java.util.NoSuchElementException(); return items.get(index++); }
                private void loadIfNeeded() { while(index>=items.size() && page<=totalPages){ JsonNode result=list(status,externalReference,page,pageSize); items=result.path("results"); index=0; totalPages=result.path("pagination").path("total_pages").asInt(page); page++; if(items.size()>0)return; } }
            };
        }
        public JsonNode retrieve(String id) { return request("GET", "/verifications/" + segment(id), null, null); }
        public JsonNode cancel(String id, String reason) { ObjectNode body=json.createObjectNode().put("reason", reason == null ? "" : reason); return request("POST", "/verifications/"+segment(id)+"/cancel", body, null); }
        public JsonNode resendLink(String id) { ObjectNode body=json.createObjectNode().put("channel","email"); return request("POST", "/verifications/"+segment(id)+"/resend-link", body, null); }
        public JsonNode evidenceReport(String id) { return request("GET", "/verifications/"+segment(id)+"/evidence-report", null, null); }
    }

    private static String segment(String value) { return URLEncoder.encode(value, StandardCharsets.UTF_8).replace("+", "%20"); }
    private static String query(Map<String,Object> params) { StringBuilder q=new StringBuilder(); params.forEach((k,v)->{if(v!=null&&!v.toString().isBlank())q.append(q.isEmpty()?"?":"&").append(segment(k)).append("=").append(segment(v.toString()));}); return q.toString(); }
    public record RawResponse(int status, String body) {}
    @FunctionalInterface public interface Transport { RawResponse send(String method, URI uri, Map<String,String> headers, String body, Duration timeout) throws IOException, InterruptedException; }
    public static final class Builder {
        private URI apiOrigin; private String clientId; private String clientSecret; private Duration timeout=Duration.ofSeconds(30); private int maxRetries=2; private Duration retryBackoff=Duration.ofMillis(250); private ObjectMapper json=new ObjectMapper(); private Transport transport;
        public Builder apiOrigin(String value){this.apiOrigin=URI.create(value);return this;} public Builder clientId(String value){this.clientId=value;return this;} public Builder clientSecret(String value){this.clientSecret=value;return this;}
        public Builder timeout(Duration value){this.timeout=value;return this;} public Builder maxRetries(int value){this.maxRetries=value;return this;} public Builder retryBackoff(Duration value){this.retryBackoff=value;return this;} public Builder objectMapper(ObjectMapper value){this.json=value;return this;} public Builder transport(Transport value){this.transport=value;return this;}
        public IdentityCoreClient build(){return new IdentityCoreClient(this);}
    }
}
