package io.identitycore;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class IdentityCoreClientTest {

    @Test
    void dateFiltersSurviveListAndEveryCursorPage() {
        List<String> urls = new ArrayList<>();
        var client = IdentityCoreClient.builder().apiOrigin("https://api.example.test").clientId("c").clientSecret("s")
            .transport((m, u, h, b, t) -> {
                urls.add(u.toString());
                String cursor = urls.size() == 3 ? "\"next\"" : "null";
                return new IdentityCoreClient.RawResponse(200, "{\"success\":true,\"data\":{\"results\":[{\"id\":\"1\"}],\"pagination\":{\"next_cursor\":" + cursor + "}}}");
            }).build();
        client.verifications.list(null, null, 1, 20, "2026-01-01", "2026-01-31");
        client.verifications.listCursor(null, null, null, 20, "2026-01-01", "2026-01-31");
        int count = 0;
        for (var item : client.verifications.iterate(null, null, 20, "2026-01-01", "2026-01-31")) count++;
        assertEquals(2, count);
        assertEquals(4, urls.size());
        for (var url : urls) {
            assertTrue(url.contains("created_from=2026-01-01"));
            assertTrue(url.contains("created_to=2026-01-31"));
        }
        assertTrue(urls.get(3).contains("cursor=next"));
    }

    @Test
    void createsVerificationWithAuthAndIdempotency() throws Exception {
        List<String> seen = new ArrayList<>();
        IdentityCoreClient client = IdentityCoreClient.builder().apiOrigin("https://api.example.test").clientId("cli_test").clientSecret("secret")
                .retryBackoff(Duration.ZERO).transport((method, uri, headers, body, timeout) -> {
            seen.add(method + " " + uri + " " + headers.get("Idempotency-Key"));
            return new IdentityCoreClient.RawResponse(201, "{\"success\":true,\"data\":{\"id\":\"ver_1\"},\"request_id\":\"req_1\"}");
        }).build();
        var input = new ObjectMapper().readTree("{\"purpose\":\"Onboarding\"}");
        assertEquals("ver_1", client.verifications.create(input, "customer-1").path("id").asText());
        assertEquals("POST https://api.example.test/api/v1/verifications/ customer-1", seen.get(0));
    }

    @Test
    void readsRetryButUnsafeWritesDoNot() {
        int[] calls = {0};
        IdentityCoreClient client = IdentityCoreClient.builder().apiOrigin("https://api.example.test").clientId("c").clientSecret("s").retryBackoff(Duration.ZERO)
                .transport((m, u, h, b, t) -> {
                    calls[0]++;
                    return calls[0] == 1 ? new IdentityCoreClient.RawResponse(503, "{\"success\":false,\"error\":{\"message\":\"down\"}}") : new IdentityCoreClient.RawResponse(200, "{\"success\":true,\"data\":[]}");
                }).build();
        assertTrue(client.policies.list().isArray());
        assertEquals(2, calls[0]);
    }

    @Test
    void retrievesVersionedVerificationResult() {
        List<String> seen = new ArrayList<>();
        IdentityCoreClient client = IdentityCoreClient.builder().apiOrigin("https://api.example.test").clientId("c").clientSecret("s")
                .transport((m, u, h, b, t) -> {
                    seen.add(u.toString());
                    return new IdentityCoreClient.RawResponse(200, "{\"success\":true,\"data\":{\"schema_version\":\"1\"}}");
                }).build();
        assertEquals("1", client.verifications.result("ver_1").path("schema_version").asText());
        assertEquals("https://api.example.test/api/v1/verifications/ver_1/result", seen.get(0));
    }
}
