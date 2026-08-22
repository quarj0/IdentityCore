import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { IdentityCoreAPIError, IdentityCoreClient, verifyWebhookSignature, verifyWebhookSignatureWithReplayClaim } from "../src/index.js";

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
  const urls = [];
  const client = new IdentityCoreClient({ apiOrigin: "https://api.example.test", clientId: "c", clientSecret: "s", fetch: async (url) => { urls.push(url); call += 1; return response(success({ results: [{ id: String(call) }], pagination: { next_cursor: call === 1 ? "next" : null } })); } });
  const ids = []; for await (const item of client.verifications.iterate()) ids.push(item.id);
  assert.deepEqual(ids, ["1", "2"]);
  assert.match(urls[1], /cursor=next/);
});

test("retrieves the versioned verification result", async () => {
  const urls = [];
  const client = new IdentityCoreClient({ apiOrigin: "https://api.example.test", clientId: "c", clientSecret: "s", fetch: async (url) => { urls.push(url); return response(success({ schema_version: "1" })); } });
  assert.equal((await client.verifications.result("ver_1")).schema_version, "1");
  assert.equal(urls[0], "https://api.example.test/api/v1/verifications/ver_1/result");
});

test("verifies signatures over the raw payload", async () => {
  const fixture = JSON.parse(readFileSync(new URL("../../fixtures/webhook-signature-v1.json", import.meta.url)));
  const seenEventIds = new Set();
  const claimEventId = async (eventId) => {
    if (seenEventIds.has(eventId)) return false;
    seenEventIds.add(eventId);
    return true;
  };
  const options = { signature: fixture.rotation_signature_header, timestamp: fixture.timestamp, eventId: fixture.event_id, signingKeys: [fixture.previous_secret], now: fixture.now_within_tolerance };
  assert.equal(verifyWebhookSignature(fixture.raw_body, options), true);
  assert.equal(await verifyWebhookSignatureWithReplayClaim(fixture.raw_body, { ...options, claimEventId }), true);
  assert.equal(await verifyWebhookSignatureWithReplayClaim(fixture.raw_body, { ...options, claimEventId }), false);
  assert.equal(verifyWebhookSignature(fixture.raw_body, { ...options, signature: fixture.current_signature, signingKey: fixture.current_secret, signingKeys: [], now: fixture.now_outside_tolerance }), false);
  const validOptions = { ...options, signature: fixture.current_signature, signingKey: fixture.current_secret, signingKeys: [] };
  assert.equal(verifyWebhookSignature(fixture.raw_body, { ...validOptions, signature: fixture.rotation_signature_header }), true);
  assert.equal(verifyWebhookSignature(fixture.raw_body, validOptions), true);
  assert.equal(verifyWebhookSignature(fixture.raw_body, { ...validOptions, signature: fixture.current_signature.replace("v1=", "v2=") }), false);
  assert.equal(verifyWebhookSignature(fixture.raw_body, { ...validOptions, eventId: "evt_other" }), false);
  assert.equal(verifyWebhookSignature(`${fixture.raw_body} `, validOptions), false);
  assert.equal(verifyWebhookSignature(fixture.non_object_raw_body, { ...validOptions, signature: fixture.non_object_signature }), false);
  assert.equal(verifyWebhookSignature(fixture.invalid_schema_raw_body, { ...validOptions, signature: fixture.invalid_schema_signature }), false);
  assert.throws(() => verifyWebhookSignature(fixture.raw_body, { ...validOptions, timestamp: Number.MAX_SAFE_INTEGER + 1 }));
  assert.equal(verifyWebhookSignature(fixture.raw_body, { signature: fixture.legacy_signature, timestamp: fixture.timestamp, signingKey: fixture.legacy_signing_key, now: fixture.now_within_tolerance }), true);
});
