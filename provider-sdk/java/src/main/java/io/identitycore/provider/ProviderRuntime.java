package io.identitycore.provider;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.time.Instant;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

/** Framework-neutral signed endpoint; HTTP transports must preserve exact bytes. */
public final class ProviderRuntime {
  @FunctionalInterface
  public interface CapabilityHandler {
    ObjectNode run(String operationId, ObjectNode inputs) throws Exception;
  }

  @FunctionalInterface
  public interface LifecycleHandler {
    boolean run(ObjectNode binding) throws Exception;
  }

  public record Response(
      int status, @JsonIgnore byte[] body, @JsonIgnore Map<String, String> headers) {
    @Override
    public String toString() {
      return "ProviderResponse(" + status + ")";
    }
  }

  public record Callback(@JsonIgnore byte[] body, @JsonIgnore Map<String, String> headers) {
    @Override
    public String toString() {
      return "ProviderCallback(redacted)";
    }
  }

  private final Map<String, SigningKey> keys;
  private final OperationStore store;
  private final Map<String, CapabilityHandler> handlers;
  private final LifecycleHandler cancelHandler;
  private final LifecycleHandler deleteHandler;

  public ProviderRuntime(
      Map<String, SigningKey> keys,
      OperationStore store,
      Map<String, CapabilityHandler> handlers,
      LifecycleHandler cancelHandler,
      LifecycleHandler deleteHandler) {
    if (keys.isEmpty() || store == null || cancelHandler == null || deleteHandler == null)
      throw new IllegalArgumentException(
          "Provider keys, durable storage and explicit lifecycle handlers are required.");
    this.keys = Map.copyOf(keys);
    this.store = store;
    this.handlers = Map.copyOf(handlers);
    this.cancelHandler = cancelHandler;
    this.deleteHandler = deleteHandler;
  }

  private static ObjectNode error(String code, boolean retryable) {
    ObjectNode output =
        Wire.JSON.createObjectNode().put("contract_version", "1").put("status", "failed");
    output.set("error", Wire.JSON.createObjectNode().put("code", code).put("retryable", retryable));
    return output;
  }

  public Response handle(String method, String path, byte[] body, Map<String, String> headers) {
    return handle(method, path, body, headers, Instant.now().getEpochSecond());
  }

  public Response handle(
      String method, String path, byte[] body, Map<String, String> headers, long now) {
    Wire.Auth auth;
    try {
      auth =
          Wire.verify(
              method, path, body, headers, keys, store::claimNonce, now, null, "provider-request");
    } catch (ProtocolError ignored) {
      return new Response(
          403,
          Wire.bytes(error("provider_authentication_failed", false)),
          Map.of("Content-Type", "application/json", "Cache-Control", "no-store"));
    } catch (Exception ignored) {
      return new Response(
          503,
          Wire.bytes(error("provider_replay_store_unavailable", true)),
          Map.of("Content-Type", "application/json", "Cache-Control", "no-store"));
    }
    int status = 200;
    ObjectNode payload;
    try {
      ObjectNode request = Wire.parse(body);
      SigningKey key = auth.key();
      if (!method.equalsIgnoreCase("POST")
          || !request.path("contract_version").isTextual()
          || !"1".equals(request.path("contract_version").asText()))
        throw new ProtocolError("Provider request method or version is unsupported.");
      JsonNode rawOperation = request.get("operation");
      if (rawOperation != null && !rawOperation.isTextual())
        throw new ProtocolError("Provider operation must be a string.");
      String operation = rawOperation == null ? "" : rawOperation.asText();
      if (operation.equals("connection_test")) {
        Set<String> allowed =
            Set.of(
                "contract_version",
                "operation",
                "environment",
                "challenge",
                "capabilities",
                "operation_contract");
        if (!allowed.containsAll(Contracts.fields(request))
            || !key.environment().equals(request.path("environment").asText())
            || !request.path("challenge").isTextual()
            || request.path("challenge").asText().isEmpty()
            || request.path("challenge").asText().length() > 256
            || !request.path("capabilities").isArray()
            || request.path("capabilities").isEmpty())
          throw new ProtocolError("Provider negotiation scope does not match.");
        Set<String> seen = new java.util.HashSet<>();
        for (JsonNode capability : request.path("capabilities"))
          if (!capability.isTextual()
              || !key.capabilities().contains(capability.asText())
              || !seen.add(capability.asText()))
            throw new ProtocolError("Provider negotiation scope does not match.");
        if (request.has("operation_contract") && !request.path("operation_contract").isTextual())
          throw new ProtocolError("Provider operation contract is unsupported.");
        String contract = request.path("operation_contract").asText("sync");
        if (!Set.of("sync", Contracts.OPERATION_CONTRACT).contains(contract))
          throw new ProtocolError("Provider operation contract is unsupported.");
        payload =
            Wire.JSON
                .createObjectNode()
                .put("contract_version", "1")
                .put("status", "completed")
                .put("challenge", request.path("challenge").asText());
        payload.set("capabilities", request.get("capabilities"));
        if (request.has("operation_contract")) payload.put("operation_contract", contract);
      } else if (Set.of("start", "poll", "cancel", "delete").contains(operation)) {
        Set<String> expected =
            operation.equals("start")
                ? Set.of("contract_version", "operation", "binding", "inputs")
                : Set.of("contract_version", "operation", "binding");
        if (!Contracts.fields(request).equals(expected)
            || !(request.get("binding") instanceof ObjectNode binding))
          throw new ProtocolError("Provider operation fields are unsupported.");
        Instant deadline =
            Contracts.validateBinding(
                binding,
                key,
                Instant.ofEpochSecond(now),
                operation.equals("start") || operation.equals("poll"));
        if (operation.equals("start")) {
          if (!(request.get("inputs") instanceof ObjectNode inputs))
            throw new ProtocolError("Provider inputs must be an object.");
          payload = store.admit(binding, inputs, deadline);
        } else if (operation.equals("poll")) payload = store.poll(binding);
        else {
          store.control(binding, "cancel");
          LifecycleHandler handler = operation.equals("delete") ? deleteHandler : cancelHandler;
          if (!handler.run(binding))
            throw new IllegalStateException("Lifecycle handler did not acknowledge.");
          payload = store.control(binding, operation);
        }
      } else if (rawOperation == null) {
        if (!Contracts.fields(request)
                .equals(Set.of("contract_version", "capability", "environment", "inputs"))
            || !key.environment().equals(request.path("environment").asText())
            || !request.path("capability").isTextual()
            || !key.capabilities().contains(request.path("capability").asText())
            || !(request.get("inputs") instanceof ObjectNode inputs))
          throw new ProtocolError("Provider invocation scope does not match.");
        String capability = request.path("capability").asText();
        CapabilityHandler handler = handlers.get(capability);
        if (handler == null) throw new ProtocolError("Provider capability handler is unavailable.");
        payload = Contracts.validateResult(capability, handler.run(null, inputs));
      } else throw new ProtocolError("Provider operation is unsupported.");
    } catch (ProtocolError ignored) {
      status = 400;
      payload = error("provider_invalid_request", false);
    } catch (Exception ignored) {
      status = 503;
      payload = error("provider_temporarily_unavailable", true);
    }
    byte[] encoded = Wire.bytes(payload);
    Map<String, String> responseHeaders =
        new LinkedHashMap<>(Wire.sign(method, path, encoded, auth.key(), now, auth.nonce()));
    responseHeaders.put("Content-Type", "application/json");
    responseHeaders.put("Cache-Control", "no-store");
    return new Response(status, encoded, Map.copyOf(responseHeaders));
  }

  public ObjectNode workOnce(int leaseSeconds) {
    WorkerLease lease = store.claimJob(leaseSeconds);
    if (lease == null) return null;
    var heartbeat =
        Executors.newSingleThreadScheduledExecutor(
            runnable -> {
              Thread thread = new Thread(runnable, "identitycore-provider-heartbeat");
              thread.setDaemon(true);
              return thread;
            });
    var future =
        heartbeat.scheduleAtFixedRate(
            () -> {
              try {
                if (!store.renew(lease, leaseSeconds)) heartbeat.shutdown();
              } catch (Exception ignored) {
                heartbeat.shutdown();
              }
            },
            Math.max(250, leaseSeconds * 1000L / 3),
            Math.max(250, leaseSeconds * 1000L / 3),
            TimeUnit.MILLISECONDS);
    try {
      String capability = lease.binding().path("capability").asText();
      CapabilityHandler handler = handlers.get(capability);
      if (handler == null) throw new ProtocolError("Provider capability handler is unavailable.");
      ObjectNode result =
          Contracts.validateResult(capability, handler.run(lease.operationId(), lease.inputs()));
      return store.complete(lease, result);
    } catch (Exception ignored) {
      throw new ProtocolError(
          "Provider processing did not complete; its durable lease will permit retry.");
    } finally {
      future.cancel(false);
      heartbeat.shutdownNow();
    }
  }

  public Callback callback(ObjectNode binding) {
    return callback(binding, Instant.now().getEpochSecond());
  }

  public Callback callback(ObjectNode binding, long timestamp) {
    SigningKey key = keys.get(binding.path("configuration_id").asText());
    if (key == null) throw new ProtocolError("Provider callback key is unavailable.");
    Contracts.validateBinding(binding, key, Instant.now(), true);
    ObjectNode payload = store.poll(binding);
    if (!Set.of("completed", "failed").contains(payload.path("status").asText()))
      throw new ProtocolError("The operation has no terminal result to deliver.");
    byte[] body = Wire.bytes(payload);
    return new Callback(
        body,
        Wire.sign(
            "POST",
            binding.path("callback_path").asText(),
            body,
            key,
            timestamp,
            Wire.randomToken()));
  }
}
