package io.identitycore.provider;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Base64;
import java.util.HashMap;
import java.util.Map;
import java.util.Set;

/** Synthetic stdin test controls. Never expose these controls on a deployed provider. */
public final class ConformanceHarness {
  public static void main(String[] args) throws Exception {
    long[] now = {1800000000L};
    Path directory = Files.createTempDirectory("identitycore-provider-harness-");
    byte[] encryptionKey = new byte[32];
    for (int i = 0; i < 32; i++) encryptionKey[i] = (byte) i;
    SigningKey key =
        new SigningKey(
            "pec_synthetic",
            "synthetic-wire-secret",
            "ten_synthetic",
            "sandbox",
            Set.of("document_ocr"));
    try (SQLiteStore store =
        new SQLiteStore(directory.resolve("provider.sqlite"), encryptionKey, () -> now[0])) {
      ProviderRuntime runtime =
          new ProviderRuntime(
              Map.of(key.keyId(), key),
              store,
              Map.of(
                  "document_ocr",
                  (id, inputs) -> {
                    Thread.sleep(Math.min(inputs.path("delay_milliseconds").asLong(), 250));
                    ObjectNode result =
                        Wire.JSON
                            .createObjectNode()
                            .put("contract_version", "1")
                            .put("capability", "document_ocr")
                            .put("status", "completed");
                    result.set(
                        "extracted_fields",
                        Wire.JSON
                            .createObjectNode()
                            .put("custom_attribute", "Private synthetic value"));
                    return result;
                  }),
              binding -> true,
              binding -> true);
      Map<String, WorkerLease> leases = new HashMap<>();
      BufferedReader reader =
          new BufferedReader(new InputStreamReader(System.in, StandardCharsets.UTF_8));
      String line;
      while ((line = reader.readLine()) != null) {
        ObjectNode output;
        try {
          ObjectNode command = Wire.parse(line.getBytes(StandardCharsets.UTF_8));
          switch (command.path("action").asText()) {
            case "ping" -> output = Wire.JSON.createObjectNode().put("ready", true);
            case "handle" -> {
              Map<String, String> headers = new HashMap<>();
              command
                  .path("headers")
                  .fields()
                  .forEachRemaining(
                      entry -> headers.put(entry.getKey(), entry.getValue().asText()));
              var response =
                  runtime.handle(
                      "POST",
                      "/invoke",
                      Base64.getDecoder().decode(command.path("body").asText()),
                      headers,
                      now[0]);
              output =
                  Wire.JSON
                      .createObjectNode()
                      .put("status", response.status())
                      .put("body", Base64.getEncoder().encodeToString(response.body()));
              output.set("headers", Wire.JSON.valueToTree(response.headers()));
            }
            case "claim" -> {
              WorkerLease lease = store.claimJob(30);
              if (lease != null) leases.put(lease.operationId(), lease);
              output = Wire.JSON.createObjectNode().put("claimed", lease != null);
            }
            case "complete" ->
                output =
                    store.complete(
                        leases.get(command.path("operation_id").asText()),
                        (ObjectNode) command.get("result"));
            case "callback" -> {
              var response = runtime.callback((ObjectNode) command.get("binding"), now[0]);
              output =
                  Wire.JSON
                      .createObjectNode()
                      .put("body", Base64.getEncoder().encodeToString(response.body()));
              output.set("headers", Wire.JSON.valueToTree(response.headers()));
            }
            case "advance" -> {
              now[0] += command.path("seconds").asLong();
              output = Wire.JSON.createObjectNode().put("now", now[0]);
            }
            case "redaction" -> {
              boolean safe = !key.toString().contains(key.secret());
              try (var files = Files.list(directory)) {
                for (Path file : files.toList())
                  safe &=
                      !new String(Files.readAllBytes(file), StandardCharsets.ISO_8859_1)
                          .contains("Private synthetic value");
              }
              for (var lease : leases.values())
                safe &=
                    !lease.toString().contains("Private synthetic value")
                        && !lease.toString().contains("synthetic-operation-lease-only");
              output = Wire.JSON.createObjectNode().put("safe", safe);
            }
            default -> throw new IllegalArgumentException();
          }
        } catch (Exception ignored) {
          output = Wire.JSON.createObjectNode().put("rejected", true);
        }
        System.out.println(new String(Wire.bytes(output), StandardCharsets.UTF_8));
        System.out.flush();
      }
    } finally {
      try (var files = Files.list(directory)) {
        for (Path file : files.toList()) Files.deleteIfExists(file);
      }
      Files.deleteIfExists(directory);
    }
  }
}
