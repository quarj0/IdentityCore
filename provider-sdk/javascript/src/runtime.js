import { inspect } from "node:util";
import { ProtocolError, jsonBytes, parseJson, sign, verify } from "./wire.js";
import {
  OPERATION_CONTRACT,
  validateBinding,
  validateResult,
} from "./contracts.js";
export class SigningKey {
  #secret;
  constructor({ keyId, secret, tenantId, environment, capabilities }) {
    this.keyId = keyId;
    this.#secret = secret;
    this.tenantId = tenantId;
    this.environment = environment;
    this.capabilities = Object.freeze([...capabilities]);
    Object.freeze(this);
  }
  get secret() {
    return this.#secret;
  }
  [inspect.custom]() {
    return `SigningKey(${this.keyId})`;
  }
}
export class ProviderRuntime {
  constructor({ keys, store, handlers, cancelHandler, deleteHandler }) {
    if (
      !Object.keys(keys).length ||
      !store ||
      typeof cancelHandler !== "function" ||
      typeof deleteHandler !== "function"
    )
      throw new TypeError(
        "Provider keys, durable storage and explicit lifecycle handlers are required.",
      );
    this.keys = Object.fromEntries(
      Object.entries(keys).map(([id, key]) => [
        id,
        key instanceof SigningKey ? key : new SigningKey(key),
      ]),
    );
    this.store = store;
    this.handlers = Object.assign(Object.create(null), handlers);
    this.cancelHandler = cancelHandler;
    this.deleteHandler = deleteHandler;
  }
  async handle({
    method,
    path,
    body,
    headers,
    now = Math.floor(Date.now() / 1000),
  }) {
    let authenticated;
    try {
      authenticated = await verify({
        method,
        path,
        body,
        headers,
        keys: this.keys,
        claimNonce: (hash, expires) => this.store.claimNonce(hash, expires),
        now,
      });
    } catch (error) {
      return {
        status: error instanceof ProtocolError ? 403 : 503,
        body: jsonBytes({
          status: "failed",
          error: {
            code:
              error instanceof ProtocolError
                ? "provider_authentication_failed"
                : "provider_replay_store_unavailable",
          },
        }),
        headers: {
          "Content-Type": "application/json",
          "Cache-Control": "no-store",
        },
      };
    }
    const { key, nonce } = authenticated;
    let status = 200,
      payload;
    try {
      const request = parseJson(body);
      if (method.toUpperCase() !== "POST" || request.contract_version !== "1")
        throw new ProtocolError(
          "Provider request method or version is unsupported.",
        );
      const operation = request.operation;
      if (operation !== undefined && typeof operation !== "string")
        throw new ProtocolError("Provider operation must be a string.");
      if (operation === "connection_test") {
        if (
          Object.keys(request).some(
            (name) =>
              ![
                "contract_version",
                "operation",
                "environment",
                "challenge",
                "capabilities",
                "operation_contract",
              ].includes(name),
          )
        )
          throw new ProtocolError("Connection test fields are unsupported.");
        if (
          request.environment !== key.environment ||
          typeof request.challenge !== "string" ||
          request.challenge.length < 1 ||
          request.challenge.length > 256 ||
          !Array.isArray(request.capabilities) ||
          !request.capabilities.length ||
          request.capabilities.some(
            (value) =>
              typeof value !== "string" || !key.capabilities.includes(value),
          ) ||
          new Set(request.capabilities).size !== request.capabilities.length
        )
          throw new ProtocolError("Provider negotiation scope does not match.");
        if (
          !["sync", OPERATION_CONTRACT].includes(
            request.operation_contract === undefined
              ? "sync"
              : request.operation_contract,
          )
        )
          throw new ProtocolError(
            "Provider operation contract is unsupported.",
          );
        payload = {
          contract_version: "1",
          status: "completed",
          challenge: request.challenge,
          capabilities: request.capabilities,
          ...(request.operation_contract !== undefined
            ? { operation_contract: request.operation_contract }
            : {}),
        };
      } else if (["start", "poll", "cancel", "delete"].includes(operation)) {
        const expected = [
          "contract_version",
          "operation",
          "binding",
          ...(operation === "start" ? ["inputs"] : []),
        ];
        if (Object.keys(request).sort().join() !== expected.sort().join())
          throw new ProtocolError("Provider operation fields are unsupported.");
        const binding = request.binding,
          deadline = validateBinding(binding, key, {
            now: new Date(now * 1000),
            completion: ["start", "poll"].includes(operation),
          });
        if (operation === "start") {
          if (
            !request.inputs ||
            typeof request.inputs !== "object" ||
            Array.isArray(request.inputs)
          )
            throw new ProtocolError("Provider inputs must be an object.");
          payload = await this.store.admit(binding, request.inputs, deadline);
        } else if (operation === "poll")
          payload = await this.store.poll(binding);
        else {
          await this.store.control(binding, "cancel");
          const handler =
            operation === "delete" ? this.deleteHandler : this.cancelHandler;
          if ((await handler(binding)) !== true)
            throw new Error("Lifecycle handler did not acknowledge.");
          payload = await this.store.control(binding, operation);
        }
      } else if (operation === undefined) {
        if (
          Object.keys(request).sort().join() !==
            ["contract_version", "capability", "environment", "inputs"]
              .sort()
              .join() ||
          request.environment !== key.environment ||
          typeof request.capability !== "string" ||
          !key.capabilities.includes(request.capability) ||
          typeof this.handlers[request.capability] !== "function" ||
          !request.inputs ||
          typeof request.inputs !== "object" ||
          Array.isArray(request.inputs)
        )
          throw new ProtocolError("Provider invocation scope does not match.");
        payload = validateResult(
          request.capability,
          await this.handlers[request.capability](null, request.inputs),
        );
      } else throw new ProtocolError("Provider operation is unsupported.");
    } catch (error) {
      status = error instanceof ProtocolError ? 400 : 503;
      payload = {
        contract_version: "1",
        status: "failed",
        error: {
          code:
            status === 400
              ? "provider_invalid_request"
              : "provider_temporarily_unavailable",
          retryable: status === 503,
        },
      };
    }
    const encoded = jsonBytes(payload);
    return {
      status,
      body: encoded,
      headers: {
        ...sign({ method, path, body: encoded, key, timestamp: now, nonce }),
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
      },
    };
  }
  async workOnce({ leaseSeconds = 30 } = {}) {
    const lease = await this.store.claimJob({ leaseSeconds });
    if (!lease) return null;
    let renewing = false;
    const timer = setInterval(
      async () => {
        if (renewing) return;
        renewing = true;
        try {
          if ((await this.store.renew(lease, { leaseSeconds })) !== true)
            clearInterval(timer);
        } catch {
          clearInterval(timer);
        } finally {
          renewing = false;
        }
      },
      Math.max(250, (leaseSeconds * 1000) / 3),
    );
    timer.unref();
    try {
      const capability = lease.binding.capability;
      if (typeof this.handlers[capability] !== "function") throw new Error();
      const result = validateResult(
        capability,
        await this.handlers[capability](lease.operationId, lease.inputs),
      );
      return await this.store.complete(lease, result);
    } catch {
      throw new ProtocolError(
        "Provider processing did not complete; its durable lease will permit retry.",
      );
    } finally {
      clearInterval(timer);
    }
  }
  async callback(binding, { timestamp } = {}) {
    const key = this.keys[binding.configuration_id];
    if (!key) throw new ProtocolError("Provider callback key is unavailable.");
    validateBinding(binding, key);
    const payload = await this.store.poll(binding);
    if (!["completed", "failed"].includes(payload.status))
      throw new ProtocolError(
        "The operation has no terminal result to deliver.",
      );
    const body = jsonBytes(payload);
    return {
      body,
      headers: sign({
        method: "POST",
        path: binding.callback_path,
        body,
        key,
        timestamp,
      }),
    };
  }
}
