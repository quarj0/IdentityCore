import assert from "node:assert/strict";
import test from "node:test";

import { requiredHeadersTemplate } from "./request-template.ts";

test("renders required operation headers as caller-provided environment values", () => {
  assert.equal(
    requiredHeadersTemplate(["Idempotency-Key"]),
    ' \\\n  -H "Idempotency-Key: $IDENTITYCORE_IDEMPOTENCY_KEY"',
  );
});

test("renders no extra curl arguments when an operation has no required headers", () => {
  assert.equal(requiredHeadersTemplate(), "");
});
