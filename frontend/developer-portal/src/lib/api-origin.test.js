import assert from "node:assert/strict";
import test from "node:test";

import { configuredApiOrigin } from "./api-origin.ts";

test("prefers the current API origin setting", () => {
  assert.equal(
    configuredApiOrigin({
      NODE_ENV: "production",
      NEXT_PUBLIC_API_ORIGIN: "https://api.identitycore.example/v1",
      NEXT_PUBLIC_API_URL: "https://legacy.identitycore.example/v1",
    }),
    "https://api.identitycore.example",
  );
});

test("uses the legacy API URL as the CSP origin", () => {
  assert.equal(
    configuredApiOrigin({
      NODE_ENV: "production",
      NEXT_PUBLIC_API_URL: "https://legacy.identitycore.example/api/v1",
    }),
    "https://legacy.identitycore.example",
  );
});

test("rejects missing or insecure production API configuration", () => {
  assert.throws(
    () => configuredApiOrigin({ NODE_ENV: "production" }),
    /must be configured/,
  );
  assert.throws(
    () =>
      configuredApiOrigin({
        NODE_ENV: "production",
        NEXT_PUBLIC_API_URL: "http://api.identitycore.example",
      }),
    /must use HTTPS/,
  );
});

test("permits an unconfigured development environment", () => {
  assert.equal(configuredApiOrigin({ NODE_ENV: "development" }), undefined);
});
