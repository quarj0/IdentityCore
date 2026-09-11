import assert from "node:assert/strict";
import test from "node:test";

import { containsUnsafeConsoleUse } from "./check-safe-logging.mjs";

for (const source of [
  'console["error"]("secret")',
  'window.console.error("secret")',
  'globalThis.console["warn"]("secret")',
  'window["console"]["info"]("secret")',
  'const { error } = console; error("secret")',
  'const { warn: report } = globalThis.console; report("secret")',
  'const report = console.error; report("secret")',
  'console.table({ accessToken: "secret" })',
  'console.dir({ credentials: "secret" })',
  'console.assert(false, "secret")',
  'console[method]("secret")',
]) {
  test(`rejects equivalent console use: ${source}`, () => {
    assert.equal(containsUnsafeConsoleUse("fixture.ts", source), true);
  });
}

test("allows unrelated methods and safe logging", () => {
  assert.equal(containsUnsafeConsoleUse("fixture.ts", 'safeLog("error", "event")'), false);
  assert.equal(containsUnsafeConsoleUse("fixture.ts", 'reporter.error("safe code")'), false);
});
