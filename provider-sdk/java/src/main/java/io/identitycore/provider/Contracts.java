package io.identitycore.provider;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.time.Instant;
import java.time.OffsetDateTime;
import java.util.HashSet;
import java.util.Set;

public final class Contracts {
  private Contracts() {}

  public static final String OPERATION_CONTRACT = "ic-provider-operations-v1";
  private static final Set<String> FIELDS =
      Set.of(
          "operation_contract",
          "operation_id",
          "configuration_id",
          "tenant_id",
          "project_id",
          "environment",
          "capability",
          "contract_version",
          "request_sha256",
          "lease_generation",
          "deadline",
          "callback_path",
          "lease_token");

  public static Set<String> fields(JsonNode value) {
    Set<String> names = new HashSet<>();
    value.fieldNames().forEachRemaining(names::add);
    return names;
  }

  public static Instant validateBinding(
      ObjectNode binding, SigningKey key, Instant now, boolean completion) {
    if (!fields(binding).equals(FIELDS))
      throw new ProtocolError("Operation binding is incomplete.");
    for (String name : FIELDS)
      if (!name.equals("lease_generation") && !binding.path(name).isTextual())
        throw new ProtocolError("Operation binding field types are invalid.");
    if (!OPERATION_CONTRACT.equals(binding.path("operation_contract").asText())
        || !"1".equals(binding.path("contract_version").asText())
        || !key.keyId().equals(binding.path("configuration_id").asText())
        || !key.tenantId().equals(binding.path("tenant_id").asText())
        || !key.environment().equals(binding.path("environment").asText())
        || !key.capabilities().contains(binding.path("capability").asText())
        || !binding.path("lease_generation").isIntegralNumber()
        || !binding.path("lease_generation").canConvertToLong()
        || binding.path("lease_generation").asLong() < 1)
      throw new ProtocolError("Operation scope does not match this provider key.");
    for (String name : Set.of("operation_id", "configuration_id", "tenant_id", "project_id"))
      if (!binding.path(name).asText().matches("[A-Za-z0-9_-]{1,64}"))
        throw new ProtocolError("Operation identifiers are invalid.");
    if (!binding.path("request_sha256").asText().matches("[0-9a-f]{64}")
        || !binding.path("lease_token").asText().matches("[A-Za-z0-9_-]{16,256}"))
      throw new ProtocolError("Operation fingerprint or lease is invalid.");
    if (!("/api/v1/providers/operations/" + binding.path("operation_id").asText() + "/callback")
        .equals(binding.path("callback_path").asText()))
      throw new ProtocolError("Operation callback path is invalid.");
    if (binding.path("lease_generation").asLong() > 9007199254740991L
        || !binding
            .path("deadline")
            .asText()
            .matches(
                "[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\\.[0-9]{1,6})?(?:Z|[+-][0-9]{2}:[0-9]{2})"))
      throw new ProtocolError("Operation deadline or generation is invalid.");
    try {
      var parsed = OffsetDateTime.parse(binding.path("deadline").asText());
      if (parsed.getYear() < 1 || Math.abs(parsed.getOffset().getTotalSeconds()) > 14 * 3600)
        throw new ProtocolError("Operation deadline is invalid.");
      Instant deadline = parsed.toInstant();
      if (completion && !deadline.isAfter(now))
        throw new ProtocolError("Operation deadline has expired.");
      return deadline;
    } catch (Exception ignored) {
      throw new ProtocolError("Operation deadline is invalid or expired.");
    }
  }

  public static ObjectNode validateResult(String capability, JsonNode result) {
    if (!(result instanceof ObjectNode object)
        || !result.path("contract_version").isTextual()
        || !"1".equals(result.path("contract_version").asText())
        || !capability.equals(result.path("capability").asText())
        || !result.path("status").isTextual()
        || !Set.of("completed", "failed", "inconclusive").contains(result.path("status").asText()))
      throw new ProtocolError("Provider result envelope is invalid.");
    byte[] encoded = Wire.bytes(result);
    if (encoded.length > 200 * 1024)
      throw new ProtocolError("Provider result exceeds its size limit.");
    Wire.parse(encoded);
    if (capability.equals("liveness") && "completed".equals(result.path("status").asText())) {
      JsonNode metrics = result.path("metrics");
      double confidence = metrics.path("avg_detection_confidence").asDouble(-1);
      if (!metrics.path("face_count").isIntegralNumber()
          || metrics.path("face_count").asLong(-1) < 0
          || !metrics.path("avg_detection_confidence").isNumber()
          || !Double.isFinite(confidence)
          || confidence < 0
          || confidence > 1) throw new ProtocolError("Liveness result metrics are invalid.");
      for (String name : Set.of("model_name", "model_version"))
        if (!result.path(name).isTextual()
            || result.path(name).asText().isBlank()
            || result.path(name).asText().length() > (name.equals("model_name") ? 120 : 64))
          throw new ProtocolError("Liveness model provenance is required.");
    }
    return object;
  }

  public static String bindingDigest(JsonNode binding) {
    return Wire.digest(Wire.bytes(Wire.canonical(binding)));
  }
}
