import assert from "node:assert/strict";
import { createHmac } from "node:crypto";
import test from "node:test";
import { IdentityCoreAPIError, IdentityCoreClient, verifyWebhookSignature } from "../src/index.js";

test("live create/get/list/error/webhook compatibility", { skip: !process.env.IDENTITYCORE_COMPAT_URL }, async () => {
  const client = new IdentityCoreClient({ apiOrigin: process.env.IDENTITYCORE_COMPAT_URL, clientId: process.env.IDENTITYCORE_COMPAT_CLIENT_ID, clientSecret: process.env.IDENTITYCORE_COMPAT_CLIENT_SECRET });
  const externalReference = `javascript-${crypto.randomUUID()}`;
  const created = await client.verifications.create({ purpose: "SDK compatibility", policyId: process.env.IDENTITYCORE_COMPAT_POLICY_ID, verificationSubject: { fullName: "JavaScript Compatibility" }, externalReference });
  assert.equal((await client.verifications.retrieve(created.id)).id, created.id);
  const listed = await client.verifications.list({ externalReference });
  assert.ok(listed.results.some((item) => item.id === created.id));
  await assert.rejects(() => client.verifications.retrieve("ver_does_not_exist"), (error) => error instanceof IdentityCoreAPIError && error.status === 404);
  const payload = Buffer.from('{"type":"verification.completed"}'); const timestamp = String(Math.floor(Date.now() / 1000)); const signingKey = "webhook-secret";
  const signature = `sha256=${createHmac("sha256", signingKey).update(`${timestamp}.`).update(payload).digest("hex")}`;
  assert.equal(verifyWebhookSignature(payload, { signature, timestamp, signingKey }), true);
});
