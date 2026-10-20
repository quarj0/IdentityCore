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

function failure(
  status: number,
  requestId: string,
  message = "internal secret",
) {
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
          JSON.stringify({
            success: true,
            data: { ok: true },
            request_id: "req_retry",
          }),
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
          JSON.stringify({
            success: true,
            data: { id: "verification" },
            request_id: "req_idempotent",
          }),
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
      JSON.stringify({
        success: true,
        data: { ok: true },
        request_id: "req_backoff",
      }),
      { status: 200 },
    );
  };

  assert.deepEqual(await client().rest("/profile"), { ok: true });
  assert.equal(attempts, 2);
});

test("MFA password login returns a transaction without persisting access", async () => {
  const writes: Array<string | null> = [];
  const transaction = {
    mfa_required: true,
    mfa_enrollment_required: false,
    mfa_token: "synthetic-proof",
  };
  globalThis.fetch = async () =>
    new Response(JSON.stringify({ success: true, data: transaction }), {
      status: 202,
    });
  const api = createIdentityCoreClient({
    apiOrigin: "https://api.example.test",
    setAccessToken: (value) => {
      writes.push(value);
    },
  });
  assert.deepEqual(
    await api.beginLogin("staff@example.test", "synthetic-password"),
    transaction,
  );
  await assert.rejects(
    api.login("staff@example.test", "synthetic-password"),
    (error: unknown) => {
      assert.ok(error instanceof IdentityCoreApiError);
      assert.equal(error.code, "mfa_required");
      return true;
    },
  );
  assert.deepEqual(writes, []);
});

test("failed MFA verification never refreshes or retries a factor", async () => {
  const paths: string[] = [];
  globalThis.fetch = async (input) => {
    paths.push(String(input));
    return failure(401, "req_mfa");
  };
  await assert.rejects(
    client().rest("/auth/mfa/challenge", { method: "POST", body: "{}" }),
  );
  assert.deepEqual(paths, [
    "https://api.example.test/api/v1/auth/mfa/challenge",
  ]);
});

test("binary downloads refresh expired credentials and preserve bytes", async () => {
  let token = "expired";
  const calls: { url: string; headers: Headers }[] = [];
  const api = createIdentityCoreClient({
    apiOrigin: "https://api.example.test",
    getAccessToken: () => token,
    setAccessToken: (next) => {
      token = next ?? "";
    },
    sessionScope: "dashboard",
  });
  globalThis.fetch = async (input, init) => {
    const url = String(input);
    const headers = new Headers(init?.headers);
    calls.push({ url, headers });
    if (url.endsWith("/auth/refresh"))
      return new Response(
        JSON.stringify({
          success: true,
          data: { tokens: { access: "fresh" } },
        }),
        { status: 200 },
      );
    if (headers.get("Authorization") === "Bearer expired")
      return failure(401, "req_expired");
    assert.equal(init?.redirect, "error");
    return new Response(new Uint8Array([0, 255, 1, 254]), {
      headers: { "Content-Type": "application/pdf" },
    });
  };
  const blob = await api.download(
    "/verifications/ver_test/evidence-report/download.pdf",
  );
  assert.deepEqual(
    [...new Uint8Array(await blob.arrayBuffer())],
    [0, 255, 1, 254],
  );
  assert.equal(calls.length, 3);
  assert.equal(calls[2].headers.get("Authorization"), "Bearer fresh");
  assert.equal(
    calls[2].headers.get("X-IdentityCore-Session-Scope"),
    "dashboard",
  );
});

test("binary download failures use safe API errors and cannot target another origin", async () => {
  globalThis.fetch = async () => failure(403, "req_download");
  await assert.rejects(
    client().download("/verifications/ver_test/evidence-report/download"),
    (error: unknown) => {
      assert.ok(error instanceof IdentityCoreApiError);
      assert.equal(error.requestId, "req_download");
      assert.equal(error.message.includes("internal secret"), false);
      return true;
    },
  );
  globalThis.fetch = async () => {
    throw new Error("must not fetch");
  };
  for (const path of [
    "https://other.test/report",
    "//other.test/report",
    "/../auth",
    "/%2e%2e/auth",
    "/report?redirect=1",
  ]) {
    await assert.rejects(client().download(path), IdentityCoreApiError);
  }
});

test("logout clears local credentials even if server revocation fails", async () => {
  let token: string | null = "synthetic";
  globalThis.fetch = async () => failure(503, "req_logout");
  const api = createIdentityCoreClient({
    apiOrigin: "https://api.example.test",
    getAccessToken: () => token,
    setAccessToken: (value) => {
      token = value;
    },
  });
  await assert.rejects(api.logout());
  assert.equal(token, null);
});
