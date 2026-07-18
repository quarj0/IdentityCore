import assert from "node:assert/strict";
import { createHmac } from "node:crypto";
import test from "node:test";
import { IdentityCoreAPIError, IdentityCoreClient, verifyWebhookSignature } from "../src/index.js";

function response(body, status = 200) { return { status, ok: status < 400, async text() { return typeof body === "string" ? body : JSON.stringify(body); } }; }
function success(data) { return { success: true, data, request_id: "req_test" }; }

test("sends production headers and create payload", async () => {
  const calls = [];
  const client = new IdentityCoreClient({ apiOrigin: "https://api.example.test", clientId: "cli_test", clientSecret: "secret", fetch: async (url, init) => { calls.push({ url, init }); return response(success({ id: "ver_1" }), 201); } });
  await client.verifications.create({ purpose: "Onboarding", policyId: "pol_1", projectId: "prj_1", verificationSubject: { fullName: "Ama" } }, { idempotencyKey: "customer-1" });
  assert.equal(calls[0].init.headers["Idempotency-Key"], "customer-1");
  assert.match(calls[0].init.headers["X-Request-Id"], /^req_/);
  assert.equal(calls[0].init.headers["User-Agent"], "identitycore-node/0.2.0");
  assert.equal(JSON.parse(calls[0].init.body).project_id, "prj_1");
});

test("retries GET but not unsafe POST", async () => {
  let getCalls = 0;
  const getClient = new IdentityCoreClient({ apiOrigin: "https://api.example.test", clientId: "c", clientSecret: "s", retryBackoff: 0, fetch: async () => { getCalls += 1; return getCalls === 1 ? response({ success: false, error: { message: "down" } }, 503) : response(success([])); } });
  assert.deepEqual(await getClient.policies.list(), []);
  let postCalls = 0;
  const postClient = new IdentityCoreClient({ apiOrigin: "https://api.example.test", clientId: "c", clientSecret: "s", retryBackoff: 0, fetch: async () => { postCalls += 1; return response({ success: false, error: { message: "down" } }, 503); } });
  await assert.rejects(() => postClient.request("POST", "/unsafe-action", {}), IdentityCoreAPIError);
  assert.equal(postCalls, 1);
});

test("async iterator follows pagination", async () => {
  let call = 0;
  const client = new IdentityCoreClient({ apiOrigin: "https://api.example.test", clientId: "c", clientSecret: "s", fetch: async () => response(success({ results: [{ id: String(++call) }], pagination: { total_pages: 2 } })) });
  const ids = []; for await (const item of client.verifications.iterate()) ids.push(item.id);
  assert.deepEqual(ids, ["1", "2"]);
});

test("verifies signatures over the raw payload", () => {
  const body = Buffer.from('{"id":"evt_1"}'); const timestamp = "1000"; const signingKey = "whsec_test";
  const signature = `sha256=${createHmac("sha256", signingKey).update(`${timestamp}.`).update(body).digest("hex")}`;
  assert.equal(verifyWebhookSignature(body, { signature, timestamp, signingKey, now: 1001 }), true);
  assert.equal(verifyWebhookSignature(body, { signature, timestamp, signingKey, now: 2000 }), false);
});
