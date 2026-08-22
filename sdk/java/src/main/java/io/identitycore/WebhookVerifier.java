package io.identitycore;

import java.nio.charset.StandardCharsets;
import java.security.InvalidKeyException;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Instant;
import java.util.List;
import java.util.Set;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;

public final class WebhookVerifier {

    private static final ObjectMapper JSON = new ObjectMapper();

    private WebhookVerifier() {
    }

    public static boolean verify(byte[] rawBody, String signature, String timestamp, String signingKey) {
        return verify(rawBody, signature, timestamp, signingKey, 300, Instant.now().getEpochSecond());
    }

    public static boolean verify(byte[] rawBody, String signature, String timestamp, String signingKey, long toleranceSeconds, long now) {
        if (signingKey == null || signingKey.isBlank()) {
            throw new IdentityCoreException("signingKey is required.");
        }
        if (toleranceSeconds < 0) {
            throw new IdentityCoreException("toleranceSeconds cannot be negative.");
        }
        final long sentAt;
        try {
            sentAt = Long.parseLong(timestamp);
        } catch (RuntimeException error) {
            throw new IdentityCoreException("Webhook timestamp is invalid.", error);
        }
        final long age;
        try {
            age = Math.subtractExact(now, sentAt);
        } catch (ArithmeticException error) {
            return false;
        }
        if (age > toleranceSeconds || age < -toleranceSeconds) return false;
        try {
            Mac mac = Mac.getInstance("HmacSHA256");
            mac.init(new SecretKeySpec(signingKey.getBytes(StandardCharsets.UTF_8), "HmacSHA256"));
            mac.update((timestamp + ".").getBytes(StandardCharsets.UTF_8));
            String expected = "sha256=" + java.util.HexFormat.of().formatHex(mac.doFinal(rawBody));
            return MessageDigest.isEqual(expected.getBytes(StandardCharsets.UTF_8), String.valueOf(signature).getBytes(StandardCharsets.UTF_8));
        } catch (IllegalStateException | InvalidKeyException | NoSuchAlgorithmException error) {
            throw new IdentityCoreException("Webhook signature verification failed.", error);
        }
    }

    public static boolean verifyV1(byte[] rawBody, String signature, String timestamp, String eventId,
            List<String> signingSecrets, long toleranceSeconds, long now, Set<String> seenEventIds) {
        if (eventId == null || eventId.isBlank()) throw new IdentityCoreException("eventId is required for v1 signatures.");
        if (signingSecrets == null || signingSecrets.stream().noneMatch(secret -> secret != null && !secret.isBlank())) {
            throw new IdentityCoreException("At least one signing secret is required.");
        }
        if (toleranceSeconds < 0) throw new IdentityCoreException("toleranceSeconds cannot be negative.");
        final long sentAt;
        try { sentAt = Long.parseLong(timestamp); }
        catch (RuntimeException error) { throw new IdentityCoreException("Webhook timestamp is invalid.", error); }
        final long age;
        try { age = Math.subtractExact(now, sentAt); }
        catch (ArithmeticException error) { return false; }
        if (age > toleranceSeconds || age < -toleranceSeconds) return false;
        try {
            boolean valid = false;
            byte[] messagePrefix = (timestamp + "." + eventId + ".").getBytes(StandardCharsets.UTF_8);
            for (String secret : signingSecrets) {
                if (secret == null || secret.isBlank()) continue;
                MessageDigest sha256 = MessageDigest.getInstance("SHA-256");
                String derivedKey = java.util.HexFormat.of().formatHex(sha256.digest(secret.getBytes(StandardCharsets.UTF_8)));
                Mac mac = Mac.getInstance("HmacSHA256");
                mac.init(new SecretKeySpec(derivedKey.getBytes(StandardCharsets.UTF_8), "HmacSHA256"));
                mac.update(messagePrefix);
                String expected = "v1=" + java.util.HexFormat.of().formatHex(mac.doFinal(rawBody));
                valid |= MessageDigest.isEqual(expected.getBytes(StandardCharsets.UTF_8), String.valueOf(signature).getBytes(StandardCharsets.UTF_8));
            }
            if (!valid) return false;
            JsonNode document = JSON.readTree(rawBody);
            JsonNode payloadEventId = document == null ? null : document.get("id");
            JsonNode schemaVersion = document == null ? null : document.get("schema_version");
            if (payloadEventId == null || !payloadEventId.isTextual() || !eventId.equals(payloadEventId.textValue())
                    || schemaVersion == null || !schemaVersion.isTextual() || !"1".equals(schemaVersion.textValue())) return false;
            if (seenEventIds != null && !seenEventIds.add(eventId)) return false;
            return true;
        } catch (Exception error) {
            return false;
        }
    }
}
