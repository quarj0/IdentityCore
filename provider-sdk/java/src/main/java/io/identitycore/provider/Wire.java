package io.identitycore.provider;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadConstraints;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.SecureRandom;
import java.time.Instant;
import java.util.Base64;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.Locale;
import java.util.Map;
import java.util.TreeMap;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;

public final class Wire {
  private Wire() {}

  public static final String VERSION = "ic-provider-v1";
  public static final int MAX_BODY_BYTES = 256 * 1024;
  public static final ObjectMapper JSON =
      new ObjectMapper(
              JsonFactory.builder()
                  .enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION)
                  .streamReadConstraints(
                      StreamReadConstraints.builder()
                          .maxNestingDepth(64)
                          .maxStringLength(MAX_BODY_BYTES)
                          .build())
                  .build())
          .enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS);

  @FunctionalInterface
  public interface NonceStore {
    boolean claim(String digest, long expiresAt);
  }

  public record Auth(SigningKey key, String nonce) {}

  public static String randomToken() {
    byte[] value = new byte[24];
    new SecureRandom().nextBytes(value);
    return Base64.getUrlEncoder().withoutPadding().encodeToString(value);
  }

  public static byte[] bytes(JsonNode value) {
    try {
      finite(value, 0);
      return JSON.writeValueAsBytes(value);
    } catch (Exception ignored) {
      throw new ProtocolError("Provider JSON is invalid.");
    }
  }

  public static JsonNode canonical(JsonNode value) {
    if (value.isObject()) {
      ObjectNode output = JSON.createObjectNode();
      TreeMap<String, JsonNode> fields = new TreeMap<>();
      value.fields().forEachRemaining(entry -> fields.put(entry.getKey(), entry.getValue()));
      fields.forEach((key, item) -> output.set(key, canonical(item)));
      return output;
    }
    if (value.isArray()) {
      ArrayNode output = JSON.createArrayNode();
      value.forEach(item -> output.add(canonical(item)));
      return output;
    }
    return value;
  }

  public static String digest(byte[] value) {
    try {
      return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(value));
    } catch (Exception ignored) {
      throw new ProtocolError("Provider cryptography is unavailable.");
    }
  }

  private static String hmac(String secret, byte[] value) {
    try {
      Mac mac = Mac.getInstance("HmacSHA256");
      mac.init(new SecretKeySpec(secret.getBytes(StandardCharsets.UTF_8), "HmacSHA256"));
      return HexFormat.of().formatHex(mac.doFinal(value));
    } catch (Exception ignored) {
      throw new ProtocolError("Provider cryptography is unavailable.");
    }
  }

  public static String deriveSigningSecret(String apiKey) {
    if (!apiKey.chars().allMatch(c -> c < 128))
      throw new ProtocolError("Provider credential is invalid.");
    return hmac(apiKey, "identitycore-provider-hmac-v1".getBytes(StandardCharsets.US_ASCII));
  }

  public static byte[] message(
      String method, String path, long timestamp, String nonce, byte[] body) {
    return String.join(
            "\n",
            VERSION,
            method.toUpperCase(Locale.ROOT),
            path,
            Long.toString(timestamp),
            nonce,
            digest(body))
        .getBytes(StandardCharsets.UTF_8);
  }

  public static Map<String, String> sign(
      String method, String path, byte[] body, SigningKey key, long timestamp, String nonce) {
    return Map.of(
        "X-IC-Key-Id",
        key.keyId(),
        "X-IC-Timestamp",
        Long.toString(timestamp),
        "X-IC-Nonce",
        nonce,
        "X-IC-Signature-Version",
        VERSION,
        "X-IC-Signature",
        hmac(key.secret(), message(method, path, timestamp, nonce, body)));
  }

  public static Map<String, String> sign(String method, String path, byte[] body, SigningKey key) {
    return sign(method, path, body, key, Instant.now().getEpochSecond(), randomToken());
  }

  public static Auth verify(
      String method,
      String path,
      byte[] body,
      Map<String, String> headers,
      Map<String, SigningKey> keys,
      NonceStore nonceStore,
      long now,
      String expectedNonce,
      String replayNamespace) {
    if (body.length > MAX_BODY_BYTES || nonceStore == null)
      throw new ProtocolError("Provider authentication is unavailable.");
    Map<String, String> lower = new LinkedHashMap<>();
    headers.forEach((name, value) -> lower.put(name.toLowerCase(Locale.ROOT), value));
    if (lower.size() != headers.size()) throw new ProtocolError("Provider authentication failed.");
    Map<String, String> patterns =
        Map.of(
            "x-ic-key-id",
            "[A-Za-z0-9_.-]{1,128}",
            "x-ic-timestamp",
            "[0-9]{1,12}",
            "x-ic-nonce",
            "[A-Za-z0-9_-]{1,256}",
            "x-ic-signature",
            "[0-9a-f]{64}");
    if (patterns.entrySet().stream()
            .anyMatch(
                entry ->
                    lower.get(entry.getKey()) == null
                        || !lower.get(entry.getKey()).matches(entry.getValue()))
        || !VERSION.equals(lower.get("x-ic-signature-version")))
      throw new ProtocolError("Provider authentication failed.");
    SigningKey key = keys.get(lower.get("x-ic-key-id"));
    long timestamp = Long.parseLong(lower.get("x-ic-timestamp"));
    String nonce = lower.get("x-ic-nonce");
    if (key == null
        || Math.abs(now - timestamp) > 300
        || (expectedNonce != null
            && !MessageDigest.isEqual(
                nonce.getBytes(StandardCharsets.US_ASCII),
                expectedNonce.getBytes(StandardCharsets.US_ASCII))))
      throw new ProtocolError("Provider authentication failed.");
    String expected = sign(method, path, body, key, timestamp, nonce).get("X-IC-Signature");
    if (!MessageDigest.isEqual(
        expected.getBytes(StandardCharsets.US_ASCII),
        lower.get("x-ic-signature").getBytes(StandardCharsets.US_ASCII)))
      throw new ProtocolError("Provider authentication failed.");
    ArrayNode scope =
        JSON.createArrayNode()
            .add(VERSION)
            .add(replayNamespace)
            .add(key.tenantId())
            .add(key.environment())
            .add(nonce);
    if (!nonceStore.claim(digest(bytes(scope)), timestamp + 301))
      throw new ProtocolError("Provider nonce was already used.");
    return new Auth(key, nonce);
  }

  private static void finite(JsonNode node, int depth) {
    if (depth > 64) throw new ProtocolError("Provider JSON exceeds its depth limit.");
    if (node.isFloatingPointNumber() && !Double.isFinite(node.doubleValue()))
      throw new ProtocolError("Nonfinite JSON is forbidden.");
    if (node.isContainerNode()) node.forEach(child -> finite(child, depth + 1));
  }

  public static ObjectNode parse(byte[] body) {
    if (body.length > MAX_BODY_BYTES)
      throw new ProtocolError("Provider message exceeds its size limit.");
    try {
      JsonNode parsed = JSON.readTree(body);
      if (!(parsed instanceof ObjectNode object))
        throw new ProtocolError("Provider messages must be objects.");
      finite(parsed, 0);
      return object;
    } catch (Exception ignored) {
      throw new ProtocolError("Provider JSON is invalid.");
    }
  }
}
