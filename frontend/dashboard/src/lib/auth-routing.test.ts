import assert from "node:assert/strict";
import test from "node:test";
import { getSafeReturnTo } from "./auth-routing.ts";

test("accepts an internal application route", () => {
  assert.equal(
    getSafeReturnTo("/onboarding/first-workflow?source=login"),
    "/onboarding/first-workflow?source=login",
  );
});

test("rejects absolute and protocol-relative redirects", () => {
  assert.equal(getSafeReturnTo("https://attacker.example"), null);
  assert.equal(getSafeReturnTo("//attacker.example/path"), null);
});

test("rejects recursive login redirects and empty values", () => {
  assert.equal(getSafeReturnTo("/login"), null);
  assert.equal(getSafeReturnTo("/login?returnTo=/onboarding"), null);
  assert.equal(getSafeReturnTo(null), null);
});
