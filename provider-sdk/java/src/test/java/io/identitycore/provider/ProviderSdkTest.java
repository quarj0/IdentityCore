package io.identitycore.provider;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.Callable;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

public final class ProviderSdkTest {
  static final long NOW = 1800000000L;
  @TempDir Path directory;
  SQLiteStore store;
  SigningKey key;
  ObjectNode binding;
  ProviderRuntime runtime;
  List<String> processed;

  private static byte[] storageKey() {
    byte[] result = new byte[32];
    for (int i = 0; i < 32; i++) result[i] = (byte) i;
    return result;
  }

  @BeforeEach
  void setup() {
    store = new SQLiteStore(directory.resolve("provider.sqlite"), storageKey(), () -> NOW);
    key =
        new SigningKey(
            "pec_synthetic",
            "synthetic-wire-secret",
            "ten_synthetic",
            "sandbox",
            Set.of("document_ocr"));
    processed = new ArrayList<>();
    runtime =
        new ProviderRuntime(
            Map.of(key.keyId(), key),
            store,
            Map.of(
                "document_ocr",
                (id, inputs) -> {
                  processed.add(id);
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
                          .put("custom_attribute", inputs.path("custom_attribute").asText()));
                  return result;
                }),
            _binding -> true,
            _binding -> true);
    binding =
        Wire.JSON
            .createObjectNode()
            .put("operation_contract", Contracts.OPERATION_CONTRACT)
            .put("operation_id", "pop_synthetic")
            .put("configuration_id", key.keyId())
            .put("tenant_id", key.tenantId())
            .put("project_id", "prj_synthetic")
            .put("environment", "sandbox")
            .put("capability", "document_ocr")
            .put("contract_version", "1")
            .put("request_sha256", "0".repeat(64))
            .put("lease_generation", 1)
            .put("deadline", Instant.ofEpochSecond(NOW + 900).toString())
            .put("callback_path", "/api/v1/providers/operations/pop_synthetic/callback")
            .put("lease_token", "synthetic-operation-lease-only");
  }

  ObjectNode request(String action) {
    ObjectNode value =
        Wire.JSON.createObjectNode().put("contract_version", "1").put("operation", action);
    value.set("binding", binding);
    if (action.equals("start"))
      value.set(
          "inputs",
          Wire.JSON.createObjectNode().put("custom_attribute", "Private synthetic value"));
    return value;
  }

  ProviderRuntime.Response send(ObjectNode request) {
    byte[] body = Wire.bytes(request);
    return runtime.handle(
        "POST",
        "/invoke",
        body,
        Wire.sign("POST", "/invoke", body, key, NOW, Wire.randomToken()),
        NOW);
  }

  void start() {
    var response = send(request("start"));
    assertEquals(200, response.status());
    assertEquals("pending", Wire.parse(response.body()).path("status").asText());
  }

  @Test
  void exactWireFixtureAndTampering() throws Exception {
    ObjectNode fixture =
        Wire.parse(Files.readAllBytes(Path.of("../../docs/fixtures/provider-signing-v1.json")));
    SigningKey fixtureKey =
        new SigningKey(
            fixture.path("key_id").asText(),
            fixture.path("secret").asText(),
            "ten_fixture",
            "sandbox",
            Set.of());
    byte[] body = fixture.path("canonical_body").asText().getBytes(StandardCharsets.UTF_8);
    var headers =
        Wire.sign(
            "POST",
            fixture.path("path").asText(),
            body,
            fixtureKey,
            fixture.path("timestamp").asLong(),
            fixture.path("nonce").asText());
    assertEquals(fixture.path("signature").asText(), headers.get("X-IC-Signature"));
    Wire.verify(
        "POST",
        fixture.path("path").asText(),
        body,
        headers,
        Map.of(fixtureKey.keyId(), fixtureKey),
        store::claimNonce,
        fixture.path("timestamp").asLong(),
        null,
        "provider-request");
    assertThrows(
        ProtocolError.class,
        () ->
            Wire.verify(
                "POST",
                fixture.path("path").asText(),
                (fixture.path("canonical_body").asText() + " ").getBytes(StandardCharsets.UTF_8),
                headers,
                Map.of(fixtureKey.keyId(), fixtureKey),
                store::claimNonce,
                fixture.path("timestamp").asLong(),
                null,
                "provider-request"));
  }

  @Test
  void durableAdmissionReopenWorkerAndCallback() throws Exception {
    start();
    start();
    ObjectNode result = runtime.workOnce(30);
    assertEquals(
        "Private synthetic value",
        result.path("result").path("extracted_fields").path("custom_attribute").asText());
    assertEquals(List.of("pop_synthetic"), processed);
    assertNull(runtime.workOnce(30));
    try (SQLiteStore reopened =
        new SQLiteStore(directory.resolve("provider.sqlite"), storageKey(), () -> NOW)) {
      assertEquals("completed", reopened.poll(binding).path("status").asText());
    }
    var callback = runtime.callback(binding, NOW);
    Wire.verify(
        "POST",
        binding.path("callback_path").asText(),
        callback.body(),
        callback.headers(),
        Map.of(key.keyId(), key),
        (_digest, _expires) -> true,
        NOW,
        null,
        "core-callback");
    String raw =
        new String(
            Files.readAllBytes(directory.resolve("provider.sqlite")), StandardCharsets.ISO_8859_1);
    assertFalse(raw.contains("Private synthetic value"));
    assertFalse(raw.contains(binding.path("lease_token").asText()));
    assertFalse(key.toString().contains(key.secret()));
  }

  @Test
  void oneWorkerAndStaleGenerationFencing() throws Exception {
    start();
    var executor = Executors.newFixedThreadPool(4);
    try {
      List<Callable<WorkerLease>> calls = new ArrayList<>();
      for (int i = 0; i < 4; i++) calls.add(() -> store.claimJob(30));
      List<WorkerLease> leases = new ArrayList<>();
      for (var future : executor.invokeAll(calls)) {
        WorkerLease lease = future.get();
        if (lease != null) leases.add(lease);
      }
      assertEquals(1, leases.size());
      WorkerLease first = leases.get(0);
      assertFalse(first.toString().contains("Private synthetic value"));
      try (SQLiteStore advanced =
          new SQLiteStore(directory.resolve("provider.sqlite"), storageKey(), () -> NOW + 31)) {
        WorkerLease replacement = advanced.claimJob(30);
        assertEquals(first.generation() + 1, replacement.generation());
        ObjectNode result =
            Wire.JSON
                .createObjectNode()
                .put("contract_version", "1")
                .put("capability", "document_ocr")
                .put("status", "completed");
        assertThrows(ProtocolError.class, () -> advanced.complete(first, result));
        advanced.complete(replacement, result);
      }
    } finally {
      executor.shutdownNow();
    }
  }

  @Test
  void cancelAndDeleteFenceWorkersAndClearRawLease() throws Exception {
    start();
    WorkerLease lease = store.claimJob(30);
    assertEquals("cancelled", Wire.parse(send(request("cancel")).body()).path("status").asText());
    ObjectNode result =
        Wire.JSON
            .createObjectNode()
            .put("contract_version", "1")
            .put("capability", "document_ocr")
            .put("status", "completed");
    assertThrows(ProtocolError.class, () -> store.complete(lease, result));
    assertEquals("deleted", Wire.parse(send(request("delete")).body()).path("status").asText());
    assertEquals("deleted", Wire.parse(send(request("delete")).body()).path("status").asText());
    assertNull(store.poll(binding).get("result"));
  }

  @Test
  void invalidScopeDuplicateJsonAndRotationReplayAreRejected() {
    ObjectNode wrong = request("start");
    ((ObjectNode) wrong.get("binding")).put("tenant_id", "ten_foreign");
    assertEquals(400, send(wrong).status());
    byte[] duplicate =
        "{\"contract_version\":\"1\",\"contract_version\":\"999\"}"
            .getBytes(StandardCharsets.UTF_8);
    assertEquals(
        400,
        runtime
            .handle(
                "POST",
                "/invoke",
                duplicate,
                Wire.sign("POST", "/invoke", duplicate, key, NOW, Wire.randomToken()),
                NOW)
            .status());
    byte[] body = Wire.bytes(Wire.JSON.createObjectNode());
    String nonce = "same-nonce-across-key-rotation";
    Wire.verify(
        "POST",
        "/invoke",
        body,
        Wire.sign("POST", "/invoke", body, key, NOW, nonce),
        Map.of(key.keyId(), key),
        store::claimNonce,
        NOW,
        null,
        "provider-request");
    SigningKey rotated =
        new SigningKey(
            "pec_rotated",
            "synthetic-rotated-secret",
            key.tenantId(),
            key.environment(),
            key.capabilities());
    assertThrows(
        ProtocolError.class,
        () ->
            Wire.verify(
                "POST",
                "/invoke",
                body,
                Wire.sign("POST", "/invoke", body, rotated, NOW, nonce),
                Map.of(rotated.keyId(), rotated),
                store::claimNonce,
                NOW,
                null,
                "provider-request"));
  }

  @Test
  void replayIsAtomicAcrossIndependentJvms() throws Exception {
    List<Process> processes = new ArrayList<>();
    for (int i = 0; i < 4; i++)
      processes.add(
          new ProcessBuilder(
                  Path.of(System.getProperty("java.home"), "bin", "java").toString(),
                  "-cp",
                  System.getProperty("java.class.path"),
                  getClass().getName(),
                  "nonce",
                  directory.resolve("provider.sqlite").toString())
              .start());
    List<String> results = new ArrayList<>();
    for (Process process : processes) {
      assertTrue(process.waitFor(20, TimeUnit.SECONDS));
      assertEquals(0, process.exitValue());
      results.add(new String(process.getInputStream().readAllBytes(), StandardCharsets.UTF_8));
    }
    results.sort(String::compareTo);
    assertEquals(List.of("false", "false", "false", "true"), results);
  }

  public static void main(String[] args) {
    if (args.length != 2 || !args[0].equals("nonce")) throw new IllegalArgumentException();
    try (SQLiteStore store = new SQLiteStore(Path.of(args[1]), storageKey(), () -> NOW)) {
      System.out.print(store.claimNonce("shared-nonce", NOW + 300));
    }
  }
}
