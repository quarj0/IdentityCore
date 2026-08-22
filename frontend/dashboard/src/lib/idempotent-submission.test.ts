import assert from "node:assert/strict";
import test from "node:test";
import {
  idempotencyHeaders,
  idempotentSubmission,
} from "./idempotent-submission.ts";

test("retains a key when the same logical submission is retried", () => {
  const first = idempotentSubmission(
    { name: "Primary", scopes: ["verifications:read"] },
    null,
    () => "first-uuid",
  );
  const retry = idempotentSubmission(
    { name: "Primary", scopes: ["verifications:read"] },
    first,
    () => "unused-uuid",
  );

  assert.equal(first.key, "ik_firstuuid");
  assert.equal(retry, first);
});

test("rotates the key when the submitted payload changes", () => {
  const first = idempotentSubmission(
    { decision: "verified" },
    null,
    () => "one",
  );
  const changed = idempotentSubmission(
    { decision: "rejected" },
    first,
    () => "two",
  );

  assert.equal(changed.key, "ik_two");
  assert.notEqual(changed, first);
});

test("uses the required public API header name", () => {
  assert.deepEqual(idempotencyHeaders("logical-attempt"), {
    "Idempotency-Key": "logical-attempt",
  });
});
