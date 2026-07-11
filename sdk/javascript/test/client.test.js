import assert from "node:assert/strict";
import test from "node:test";

import { IdentityCoreAPIError, IdentityCoreClient } from "../src/index.js";

function response(body, { status = 200, ok = status < 400 } = {}) {
  return {
    status,
    ok,
    async text() {
      return typeof body === "string" ? body : JSON.stringify(body);
    },
  };
}

function success(data) {
  return { success: true, data, request_id: "req_test" };
}

test("sends API-client auth headers", async () => {
  const calls = [];
  const client = new IdentityCoreClient({
    apiOrigin: "https://api.example.test",
    clientId: "cli_test",
    clientSecret: "secret",
    fetch: async (url, init) => {
      calls.push({ url, init });
      return response(success([{ id: "pol_123" }]));
    },
  });

  const policies = await client.policies.list();

  assert.deepEqual(policies, [{ id: "pol_123" }]);
  assert.equal(calls[0].url, "https://api.example.test/api/v1/policies/");
  assert.equal(calls[0].init.headers["X-Client-Id"], "cli_test");
  assert.equal(calls[0].init.headers.Authorization, "Bearer secret");
});

test("creates verification with API payload shape", async () => {
  const calls = [];
  const client = new IdentityCoreClient({
    apiOrigin: "https://api.example.test",
    clientId: "cli_test",
    clientSecret: "secret",
    fetch: async (url, init) => {
      calls.push({ url, init });
      return response(success({ id: "ver_123" }), { status: 201 });
    },
  });

  const result = await client.verifications.create({
    purpose: "Customer onboarding",
    policyId: "pol_123",
    verificationSubject: { fullName: "Kwame Mensah", email: "kwame@example.com" },
    externalReference: "customer_123",
  });

  assert.equal(result.id, "ver_123");
  assert.equal(calls[0].url, "https://api.example.test/api/v1/verifications/");
  assert.deepEqual(JSON.parse(calls[0].init.body), {
    purpose: "Customer onboarding",
    policy_id: "pol_123",
    verification_subject: {
      full_name: "Kwame Mensah",
      email: "kwame@example.com",
      phone_number: "",
      metadata: {},
    },
    external_reference: "customer_123",
    redirect_url: "",
    metadata: {},
  });
});

test("raises API error for error envelopes", async () => {
  const client = new IdentityCoreClient({
    apiOrigin: "https://api.example.test",
    clientId: "cli_test",
    clientSecret: "secret",
    fetch: async () =>
      response(
        {
          success: false,
          error: {
            code: "validation_error",
            message: "Choose an active verification template.",
            details: { policy_id: ["Required."] },
          },
          request_id: "req_test",
        },
        { status: 400, ok: false },
      ),
  });

  await assert.rejects(
    () => client.policies.list(),
    (error) => {
      assert.ok(error instanceof IdentityCoreAPIError);
      assert.equal(error.status, 400);
      assert.equal(error.code, "validation_error");
      assert.equal(error.requestId, "req_test");
      assert.deepEqual(error.details, { policy_id: ["Required."] });
      return true;
    },
  );
});

test("normalizes invalid JSON responses", async () => {
  const client = new IdentityCoreClient({
    apiOrigin: "https://api.example.test",
    clientId: "cli_test",
    clientSecret: "secret",
    fetch: async () => response("InvalidTag", { status: 502, ok: false }),
  });

  await assert.rejects(
    () => client.policies.list(),
    /The service is temporarily unavailable. Please try again shortly./,
  );
});

test("verification helper paths match public API", async () => {
  const calls = [];
  const client = new IdentityCoreClient({
    apiOrigin: "https://api.example.test",
    clientId: "cli_test",
    clientSecret: "secret",
    fetch: async (url, init) => {
      calls.push({ url, init });
      return response(success({ ok: true }));
    },
  });

  await client.verifications.list({ status: "verified", page: 2, pageSize: 10 });
  await client.verifications.retrieve("ver_123");
  await client.verifications.cancel("ver_123", { reason: "Duplicate" });
  await client.verifications.resendLink("ver_123");
  await client.verifications.evidenceReport("ver_123");

  assert.deepEqual(
    calls.map((call) => call.url),
    [
      "https://api.example.test/api/v1/verifications/?status=verified&page=2&page_size=10",
      "https://api.example.test/api/v1/verifications/ver_123",
      "https://api.example.test/api/v1/verifications/ver_123/cancel",
      "https://api.example.test/api/v1/verifications/ver_123/resend-link",
      "https://api.example.test/api/v1/verifications/ver_123/evidence-report",
    ],
  );
});
