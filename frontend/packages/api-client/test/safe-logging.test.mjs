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
  assert.equal(redacted.profile.safe_status, "pending_review");
  assert.equal(redacted.evidence.selfie_image, REDACTED);
  assert.equal(redacted.evidence.face_embedding, REDACTED);
  assert.equal(redacted.evidence.document_storage_key, REDACTED);
  assert.equal(redacted.binary, REDACTED_BINARY);
});

test("redacts secrets and identifiers embedded in free text", () => {
  const output = redactLogText(
    "token=top-secret email=ada@example.test phone=+233241234567 document_number=GHA-123 Authorization: Bearer bearer-secret",
  );

  assert.doesNotMatch(
    output,
    /top-secret|ada@example\.test|233241234567|GHA-123|bearer-secret/,
  );
  assert.match(output, /\[REDACTED\]/);
});
