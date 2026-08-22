package io.identitycore;

import com.fasterxml.jackson.databind.ObjectMapper;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.List;
import java.util.UUID;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIfEnvironmentVariable;
import static org.junit.jupiter.api.Assertions.*;

@EnabledIfEnvironmentVariable(named = "IDENTITYCORE_COMPAT_URL", matches = ".+")
class LiveCompatibilityTest {

    @Test
    void createGetListErrorAndWebhook() throws Exception {
        var json = new ObjectMapper();
        var client = IdentityCoreClient.builder().apiOrigin(System.getenv("IDENTITYCORE_COMPAT_URL"))
                .clientId(System.getenv("IDENTITYCORE_COMPAT_CLIENT_ID")).clientSecret(System.getenv("IDENTITYCORE_COMPAT_CLIENT_SECRET")).build();
        var reference = "java-" + UUID.randomUUID();
        var input = json.createObjectNode().put("purpose", "SDK compatibility").put("policy_id", System.getenv("IDENTITYCORE_COMPAT_POLICY_ID"))
                .put("external_reference", reference).set("verification_subject", json.createObjectNode().put("full_name", "Java Compatibility"));
        var created = client.verifications.create(input);
        assertEquals(created.path("id").asText(), client.verifications.retrieve(created.path("id").asText()).path("id").asText());
        assertTrue(client.verifications.list(null, reference, 1, 20).path("results").findValuesAsText("id").contains(created.path("id").asText()));
        var error = assertThrows(IdentityCoreApiException.class, () -> client.verifications.retrieve("ver_does_not_exist"));
        assertEquals(404, error.status());

        String eventId = "evt_live_compatibility";
        byte[] payload = ("{\"id\":\"" + eventId + "\",\"schema_version\":\"1\",\"type\":\"verification.completed\"}")
                .getBytes(StandardCharsets.UTF_8);
        String timestamp = Long.toString(Instant.now().getEpochSecond());
        String secret = "webhook-secret";
        String derivedKey = java.util.HexFormat.of().formatHex(
                MessageDigest.getInstance("SHA-256").digest(secret.getBytes(StandardCharsets.UTF_8)));
        Mac mac = Mac.getInstance("HmacSHA256");
        mac.init(new SecretKeySpec(derivedKey.getBytes(StandardCharsets.UTF_8), "HmacSHA256"));
        mac.update((timestamp + "." + eventId + ".").getBytes(StandardCharsets.UTF_8));
        assertTrue(WebhookVerifier.verifyV1(payload,
                "v1=" + java.util.HexFormat.of().formatHex(mac.doFinal(payload)), timestamp, eventId,
                List.of(secret)));
    }
}
