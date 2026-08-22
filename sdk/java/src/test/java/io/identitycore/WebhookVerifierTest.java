package io.identitycore;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashSet;
import java.util.List;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;

class WebhookVerifierTest {
    @Test
    void verifiesCanonicalV1FixtureRotationToleranceAndReplay() throws Exception {
        JsonNode fixture = new ObjectMapper().readTree(
                Files.readString(Path.of("..", "fixtures", "webhook-signature-v1.json")));
        byte[] body = fixture.get("raw_body").asText().getBytes(StandardCharsets.UTF_8);
        var seen = new HashSet<String>();
        var secrets = List.of(fixture.get("current_secret").asText(), fixture.get("previous_secret").asText());
        assertTrue(WebhookVerifier.verifyV1(body, fixture.get("previous_signature").asText(),
                fixture.get("timestamp").asText(), fixture.get("event_id").asText(), secrets, 300,
                fixture.get("now_within_tolerance").asLong(), seen));
        assertFalse(WebhookVerifier.verifyV1(body, fixture.get("previous_signature").asText(),
                fixture.get("timestamp").asText(), fixture.get("event_id").asText(), secrets, 300,
                fixture.get("now_within_tolerance").asLong(), seen));
        assertFalse(WebhookVerifier.verifyV1(body, fixture.get("current_signature").asText(),
                fixture.get("timestamp").asText(), fixture.get("event_id").asText(), secrets, 300,
                fixture.get("now_outside_tolerance").asLong(), null));
        String currentSignature = fixture.get("current_signature").asText();
        long now = fixture.get("now_within_tolerance").asLong();
        assertTrue(WebhookVerifier.verifyV1(body, currentSignature, fixture.get("timestamp").asText(),
                fixture.get("event_id").asText(), secrets, 300, now, null));
        assertFalse(WebhookVerifier.verifyV1(body, currentSignature.replace("v1=", "v2="),
                fixture.get("timestamp").asText(), fixture.get("event_id").asText(), secrets, 300, now, null));
        assertFalse(WebhookVerifier.verifyV1(body, currentSignature, fixture.get("timestamp").asText(),
                "evt_other", secrets, 300, now, null));
        assertFalse(WebhookVerifier.verifyV1((fixture.get("raw_body").asText() + " ").getBytes(StandardCharsets.UTF_8),
                currentSignature, fixture.get("timestamp").asText(), fixture.get("event_id").asText(), secrets, 300,
                now, null));
        assertFalse(WebhookVerifier.verifyV1(fixture.get("non_object_raw_body").asText().getBytes(StandardCharsets.UTF_8),
                fixture.get("non_object_signature").asText(), fixture.get("timestamp").asText(),
                fixture.get("event_id").asText(), secrets, 300, now, null));
        assertFalse(WebhookVerifier.verifyV1(fixture.get("invalid_schema_raw_body").asText().getBytes(StandardCharsets.UTF_8),
                fixture.get("invalid_schema_signature").asText(), fixture.get("timestamp").asText(),
                fixture.get("event_id").asText(), secrets, 300, now, null));
        assertFalse(WebhookVerifier.verifyV1(body, currentSignature, Long.toString(Long.MIN_VALUE),
                fixture.get("event_id").asText(), secrets, 300, 0, null));
    }
}
