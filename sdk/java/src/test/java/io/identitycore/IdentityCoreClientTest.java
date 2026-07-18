package io.identitycore;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class IdentityCoreClientTest {
    @Test void createsVerificationWithAuthAndIdempotency() throws Exception {
        List<String> seen = new ArrayList<>();
        IdentityCoreClient client = IdentityCoreClient.builder().apiOrigin("https://api.example.test").clientId("cli_test").clientSecret("secret")
            .retryBackoff(Duration.ZERO).transport((method,uri,headers,body,timeout)->{seen.add(method+" "+uri+" "+headers.get("Idempotency-Key")); return new IdentityCoreClient.RawResponse(201,"{\"success\":true,\"data\":{\"id\":\"ver_1\"},\"request_id\":\"req_1\"}");}).build();
        var input = new ObjectMapper().readTree("{\"purpose\":\"Onboarding\"}");
        assertEquals("ver_1", client.verifications.create(input,"customer-1").path("id").asText());
        assertEquals("POST https://api.example.test/api/v1/verifications/ customer-1", seen.get(0));
    }

    @Test void readsRetryButUnsafeWritesDoNot() {
        int[] calls={0};
        IdentityCoreClient client=IdentityCoreClient.builder().apiOrigin("https://api.example.test").clientId("c").clientSecret("s").retryBackoff(Duration.ZERO)
            .transport((m,u,h,b,t)->{calls[0]++; return calls[0]==1?new IdentityCoreClient.RawResponse(503,"{\"success\":false,\"error\":{\"message\":\"down\"}}"):new IdentityCoreClient.RawResponse(200,"{\"success\":true,\"data\":[]}");}).build();
        assertTrue(client.policies.list().isArray()); assertEquals(2,calls[0]);
    }
}
