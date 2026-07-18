package io.identitycore;

import java.nio.charset.StandardCharsets;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class WebhookVerifierTest {
    @Test void verifiesRawPayloadAndTimestamp() throws Exception {
        byte[] body="{\"id\":\"evt_1\"}".getBytes(StandardCharsets.UTF_8); String timestamp="1000", key="whsec_test";
        Mac mac=Mac.getInstance("HmacSHA256"); mac.init(new SecretKeySpec(key.getBytes(StandardCharsets.UTF_8),"HmacSHA256"));
        String signature="sha256="+java.util.HexFormat.of().formatHex(mac.doFinal((timestamp+"."+new String(body,StandardCharsets.UTF_8)).getBytes(StandardCharsets.UTF_8)));
        assertTrue(WebhookVerifier.verify(body,signature,timestamp,key,300,1001));
        assertFalse(WebhookVerifier.verify(body,signature,timestamp,key,300,2000));
    }
}

