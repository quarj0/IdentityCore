package io.identitycore;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.time.Instant;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;

public final class WebhookVerifier {
    private WebhookVerifier() {}

    public static boolean verify(byte[] rawBody, String signature, String timestamp, String signingKey) {
        return verify(rawBody, signature, timestamp, signingKey, 300, Instant.now().getEpochSecond());
    }

    public static boolean verify(byte[] rawBody, String signature, String timestamp, String signingKey, long toleranceSeconds, long now) {
        if (signingKey == null || signingKey.isBlank()) throw new IdentityCoreException("signingKey is required.");
        if (toleranceSeconds < 0) throw new IdentityCoreException("toleranceSeconds cannot be negative.");
        final long sentAt;
        try { sentAt = Long.parseLong(timestamp); } catch (RuntimeException error) { throw new IdentityCoreException("Webhook timestamp is invalid.", error); }
        if (Math.abs(now - sentAt) > toleranceSeconds) return false;
        try {
            Mac mac = Mac.getInstance("HmacSHA256");
            mac.init(new SecretKeySpec(signingKey.getBytes(StandardCharsets.UTF_8), "HmacSHA256"));
            mac.update((timestamp + ".").getBytes(StandardCharsets.UTF_8));
            String expected = "sha256=" + java.util.HexFormat.of().formatHex(mac.doFinal(rawBody));
            return MessageDigest.isEqual(expected.getBytes(StandardCharsets.UTF_8), String.valueOf(signature).getBytes(StandardCharsets.UTF_8));
        } catch (Exception error) { throw new IdentityCoreException("Webhook signature verification failed.", error); }
    }
}

