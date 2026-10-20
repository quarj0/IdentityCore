import test from "node:test";
import assert from "node:assert/strict";
import { IdentityCoreClient } from "../src/index.js";

test("governed clients preserve project/purpose and keep capabilities out of URLs", async () => {
  const calls = [];
  const client = new IdentityCoreClient({
    apiOrigin: "https://api.example.test",
    clientId: "recipient",
    clientSecret: "synthetic-secret",
    fetch: async (url, init) => {
      calls.push({ url, init });
      return {
        status: 200,
        ok: true,
        text: async () => JSON.stringify({ success: true, data: { ok: true } }),
      };
    },
  });
  await client.governed.getEvidence("evd_one/../../claims?x=y", {
    query: {
      project_id: "prj_one",
      purpose: "address & employment",
      include_payload: false,
    },
  });
  let last = calls.at(-1);
  assert.ok(last.url.includes("evd_one%2F..%2F..%2Fclaims%3Fx%3Dy"));
  assert.equal(
    new URL(last.url).searchParams.get("purpose"),
    "address & employment",
  );
  await client.governed.redeemClaimDisclosure(
    "dcl_one",
    { project_id: "prj_one" },
    { disclosureToken: "synthetic-capability", idempotencyKey: "redeem-once" },
  );
  last = calls.at(-1);
  assert.equal(last.init.headers["X-Disclosure-Token"], "synthetic-capability");
  assert.equal(last.init.headers["Idempotency-Key"], "redeem-once");
  assert.ok(!last.url.includes("synthetic-capability"));
  assert.ok(!last.init.body.includes("synthetic-capability"));
});

test("human approvals authenticate with a user token and omit the client id", async () => {
  let headers;
  const client = new IdentityCoreClient({
    apiOrigin: "https://api.example.test",
    accessToken: "synthetic-user-jwt",
    fetch: async (_url, init) => {
      headers = init.headers;
      return {
        status: 200,
        ok: true,
        text: async () => '{"success":true,"data":{}}',
      };
    },
  });
  await client.governed.approvePurposeAuthorization("paz_one", {});
  assert.equal(headers.Authorization, "Bearer synthetic-user-jwt");
  assert.ok(!("X-Client-Id" in headers));
});

test("disclosure redemption requires an explicit token", () => {
  const client = new IdentityCoreClient({
    apiOrigin: "https://api.example.test",
    clientId: "recipient",
    clientSecret: "synthetic-secret",
  });
  assert.throws(
    () =>
      client.governed.redeemClaimDisclosure("dcl_one", {
        project_id: "prj_one",
      }),
    /disclosure token/,
  );
});
