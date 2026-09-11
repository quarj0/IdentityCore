import assert from "node:assert/strict";
import { rmSync } from "node:fs";
import { createRequire } from "node:module";
import { after, test } from "node:test";

const require = createRequire(import.meta.url);
const {
  REDACTED,
  REDACTED_BINARY,
  redactLogText,
  redactLogValue,
} = require("../.safe-logging-test/safe-logging.js");

after(() => {
  rmSync(new URL("../.safe-logging-test", import.meta.url), {
    force: true,
    recursive: true,
  });
});

test("redacts nested credentials, PII, evidence, and binary values", () => {
  const redacted = redactLogValue({
    authorization: "Bearer secret-token",
    profile: {
      email: "ada@example.test",
      phone_number: "+233241234567",
      document_number: "GHA-123456789",
      external_reference: "customer-4482",
      device_fingerprint: "device-secret",
      user_agent: "browser-fingerprint",
      verification_subject_id: "vs_sensitive",
      safe_status: "pending_review",
    },
    evidence: {
      selfie_image: "base64-selfie",
      face_embedding: [0.1, 0.2],
      document_storage_key: "tenant/evidence/front.jpg",
    },
    binary: new Uint8Array([1, 2, 3]),
  });

  assert.equal(redacted.authorization, REDACTED);
  assert.equal(redacted.profile.email, REDACTED);
  assert.equal(redacted.profile.phone_number, REDACTED);
  assert.equal(redacted.profile.document_number, REDACTED);
  assert.equal(redacted.profile.external_reference, REDACTED);
  assert.equal(redacted.profile.device_fingerprint, REDACTED);
  assert.equal(redacted.profile.user_agent, REDACTED);
  assert.equal(redacted.profile.verification_subject_id, REDACTED);
  assert.equal(redacted.profile.safe_status, "pending_review");
  assert.equal(redacted.evidence.selfie_image, REDACTED);
  assert.equal(redacted.evidence.face_embedding, REDACTED);
  assert.equal(redacted.evidence.document_storage_key, REDACTED);
  assert.equal(redacted.binary, REDACTED_BINARY);
});

test("redacts secrets and multiword identifiers embedded in free text", () => {
  const output = redactLogText(
    "full_name=Ada Lovelace; token=top-secret; email=ada@example.test; phone=+233241234567; external_reference=customer-4482; document_number=GHA-123; Authorization: Bearer bearer-secret",
  );

  assert.doesNotMatch(
    output,
    /Ada Lovelace|top-secret|ada@example\.test|233241234567|customer-4482|GHA-123|bearer-secret/,
  );
  assert.match(output, /\[REDACTED\]/);
});

test("redacts quoted keys, credential spellings, and nested serialized values", () => {
  for (const key of [
    "access_token",
    "id_token",
    "private_key",
    "secret_access_key",
    "document_number",
    "csrfmiddlewaretoken",
    "storage_key",
    "face_embedding",
  ]) {
    for (const spelling of [key, key.replaceAll("_", "-"), key.toUpperCase()]) {
      for (const value of [
        `{"${spelling}":"private-value"}`,
        `?${spelling}=private-value&status=failed`,
        `${spelling}='private-value'; status=failed`,
      ]) {
        assert.doesNotMatch(redactLogText(value), /private-value/);
      }
    }
  }
  for (const value of [
    '{"context":{"access_token":"private-value"}}',
    '{"face_embedding":["private-value", "second-private"]}',
    '{"private_key":"private-value\\"still-private"}',
    "full_name=Doe, Jane",
    'face_embedding=[\n  0.123,\n  0.456\n], "status":"failed"',
  ]) {
    assert.doesNotMatch(
      redactLogText(value),
      /private-value|second-private|still-private|Jane|0\.123|0\.456/,
    );
  }
});

test("redacts all binary array views before object traversal", () => {
  for (const view of [
    new Uint8ClampedArray([17]),
    new Uint16Array([18]),
    new Float32Array([0.25]),
    new DataView(new ArrayBuffer(4)),
  ]) {
    assert.deepEqual(redactLogValue({ imageData: view }), {
      imageData: REDACTED_BINARY,
    });
  }
});

test("redacts deployed credential names, signatures, and IPv6 addresses", () => {
  for (const key of [
    "SECRET_KEY",
    "DJANGO_SECRET_KEY",
    "object_storage_access_key_id",
    "object_storage_secret_access_key",
    "aws_access_key_id",
    "aws_secret_access_key",
    "X-Amz-Signature",
    "X-IdentityCore-Signature",
  ]) {
    assert.equal(redactLogValue({ [key]: "private-value" })[key], REDACTED);
    assert.doesNotMatch(
      redactLogText(`?${key}=private-value&status=ok`),
      /private-value/,
    );
  }
  for (const address of [
    "2001:db8:1234:5678:9abc:def0:1234:5678",
    "2001:db8::1",
    "::1",
    "::ffff:192.0.2.1",
    "fe80::1%eth0",
  ]) {
    assert.ok(
      !redactLogText(`client connected from [${address}]`).includes(address),
    );
  }
  assert.equal(
    redactLogText("time 12:34:56; status=ok"),
    "time 12:34:56; status=ok",
  );
  assert.doesNotMatch(
    redactLogText("token=[REDACTED]private-value; status=ok"),
    /private-value/,
  );
});

test("redacts camelCase credential and identity keys", () => {
  const redacted = redactLogValue({
    accessToken: "access-private",
    sessionToken: "session-private",
    clientSecret: "client-private",
    fullName: "Ada Private",
    safeStatus: "ready",
  });
  assert.equal(redacted.accessToken, REDACTED);
  assert.equal(redacted.sessionToken, REDACTED);
  assert.equal(redacted.clientSecret, REDACTED);
  assert.equal(redacted.fullName, REDACTED);
  assert.equal(redacted.safeStatus, "ready");
});
