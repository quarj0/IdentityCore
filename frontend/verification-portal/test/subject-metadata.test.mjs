import assert from "node:assert/strict";
import { createHmac } from "node:crypto";
import { test } from "node:test";
import { subjectMetadataHeaders } from "../src/lib/bff-subject-metadata.ts";

const secret = "synthetic-metadata-secret-at-least-32-characters";
const headersFor = (headers = {}) =>
  subjectMetadataHeaders(
    new Request("https://verify.example.test/api/verification", { headers }),
    "https://api.example.test/api/v1/sessions/ses_test",
    "GET",
    "Bearer synthetic",
    "synthetic-request",
  );

test("metadata uses only an explicitly trusted single-address ingress header", () => {
  const previousSecret = process.env.VERIFICATION_METADATA_SECRET;
  const previousHeader = process.env.VERIFICATION_CLIENT_IP_HEADER;
  try {
    process.env.VERIFICATION_METADATA_SECRET = secret;
    delete process.env.VERIFICATION_CLIENT_IP_HEADER;
    const values = {
      "user-agent": "ApplicantBrowser/1.0",
      "x-forwarded-for": "8.8.8.8",
      "x-real-ip": "192.0.2.40",
      "x-ic-subject-metadata": "forged",
      "x-ic-subject-signature": "forged",
    };
    let result = headersFor(values);
    let payload = JSON.parse(
      Buffer.from(result["X-IC-Subject-Metadata"], "base64url"),
    );
    assert.equal(payload.ip, null);
    assert.equal(payload.user_agent, values["user-agent"]);
    assert.equal(
      result["X-IC-Subject-Signature"],
      createHmac("sha256", secret)
        .update(result["X-IC-Subject-Metadata"])
        .digest("hex"),
    );
    process.env.VERIFICATION_CLIENT_IP_HEADER = "x-real-ip";
    for (const address of [
      "192.0.2.40",
      "2001:db8::1",
      "spoof, 192.0.2.1",
      "fe80::1%eth0",
      "garbage",
    ]) {
      result = headersFor({ ...values, "x-real-ip": address });
      payload = JSON.parse(
        Buffer.from(result["X-IC-Subject-Metadata"], "base64url"),
      );
      assert.equal(
        payload.ip,
        ["192.0.2.40", "2001:db8::1"].includes(address) ? address : null,
      );
    }
    process.env.VERIFICATION_METADATA_SECRET = "short";
    assert.throws(() => headersFor(values));
  } finally {
    if (previousSecret === undefined)
      delete process.env.VERIFICATION_METADATA_SECRET;
    else process.env.VERIFICATION_METADATA_SECRET = previousSecret;
    if (previousHeader === undefined)
      delete process.env.VERIFICATION_CLIENT_IP_HEADER;
    else process.env.VERIFICATION_CLIENT_IP_HEADER = previousHeader;
  }
});
