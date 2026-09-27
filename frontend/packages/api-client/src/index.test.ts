import assert from "node:assert/strict";
import { afterEach, test } from "node:test";

import { createIdentityCoreClient, IdentityCoreApiError } from "./index.ts";

const originalFetch = globalThis.fetch;

afterEach(() => {
  globalThis.fetch = originalFetch;
});

function client() {
  return createIdentityCoreClient({ apiOrigin: "https://api.example.test" });
}

function failure(status: number, requestId: string, message = "internal secret") {
  return new Response(
    JSON.stringify({
      success: false,
      request_id: requestId,
      error: { code: "internal_error", message, details: { secret: message } },
    }),
    { status, headers: { "Content-Type": "application/json" } },
  );
}

test("safe failures retain a support request ID without exposing server details", async () => {
  globalThis.fetch = async () => failure(500, "req_support123");

  await assert.rejects(client().rest("/profile"), (error: unknown) => {
    assert.ok(error instanceof IdentityCoreApiError);
    assert.equal(error.requestId, "req_support123");
    assert.equal(error.message.includes("internal secret"), false);
    return true;
  });
});

test("GET retries one transient failure", async () => {
  let attempts = 0;
  globalThis.fetch = async () => {
    attempts += 1;
    return attempts === 1
      ? failure(503, "req_retry")
      : new Response(
          JSON.stringify({ success: true, data: { ok: true }, request_id: "req_retry" }),
          { status: 200 },
        );
  };

  assert.deepEqual(await client().rest("/profile"), { ok: true });
  assert.equal(attempts, 2);
});

test("POST without an idempotency key is never retried", async () => {
  let attempts = 0;
  globalThis.fetch = async () => {
    attempts += 1;
    return failure(503, "req_post");
  };

  await assert.rejects(
    client().rest("/verifications", { method: "POST", body: "{}" }),
  );
  assert.equal(attempts, 1);
});

test("POST with an idempotency key may retry once", async () => {
  let attempts = 0;
  globalThis.fetch = async () => {
    attempts += 1;
    return attempts === 1
      ? failure(503, "req_idempotent")
      : new Response(
          JSON.stringify({ success: true, data: { id: "verification" }, request_id: "req_idempotent" }),
          { status: 200 },
        );
  };

  const result = await client().rest("/verifications", {
    method: "POST",
    headers: { "Idempotency-Key": "logical-attempt" },
    body: "{}",
  });
  assert.deepEqual(result, { id: "verification" });
  assert.equal(attempts, 2);
});

test("POST with an empty idempotency key is never retried", async () => {
  let attempts = 0;
  globalThis.fetch = async () => {
    attempts += 1;
    return failure(503, "req_empty_key");
  };

  await assert.rejects(
    client().rest("/verifications", {
      method: "POST",
      headers: { "Idempotency-Key": "   " },
      body: "{}",
    }),
  );
  assert.equal(attempts, 1);
});

test("caller cancellation stops a safe request without retry", async () => {
  const controller = new AbortController();
  controller.abort();
  let attempts = 0;
  globalThis.fetch = async (_input, init) => {
    attempts += 1;
    assert.equal(init?.signal?.aborted, true);
    throw new DOMException("Aborted by caller", "AbortError");
  };

  await assert.rejects(
    client().rest("/profile", { signal: controller.signal }),
    (error: unknown) => {
      assert.ok(error instanceof DOMException);
      assert.equal(error.name, "AbortError");
      return true;
    },
  );
  assert.equal(attempts, 1);
});

test("missing Retry-After uses the bounded fallback delay", async () => {
  let attempts = 0;
  let startedAt = 0;
  globalThis.fetch = async () => {
    attempts += 1;
    if (attempts === 1) {
      startedAt = Date.now();
      return failure(503, "req_backoff");
    }
    assert.ok(Date.now() - startedAt >= 200);
    return new Response(
      JSON.stringify({ success: true, data: { ok: true }, request_id: "req_backoff" }),
      { status: 200 },
    );
  };

  assert.deepEqual(await client().rest("/profile"), { ok: true });
  assert.equal(attempts, 2);
});
