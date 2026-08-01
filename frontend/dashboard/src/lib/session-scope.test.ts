import assert from "node:assert/strict";
import test from "node:test";
import { addDashboardSessionScope } from "./session-scope.ts";

test("identifies dashboard requests so refresh cookies use the dashboard scope", () => {
  const headers = addDashboardSessionScope(new Headers());

  assert.equal(headers.get("X-IdentityCore-Session-Scope"), "dashboard");
});
