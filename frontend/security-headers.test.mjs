import assert from "node:assert/strict";
import { test } from "node:test";
import { contentSecurityPolicy } from "./security-headers.ts";

const directive = (csp, name) =>
  csp
    .split("; ")
    .find((part) => part.startsWith(name + " "))
    .split(" ")
    .slice(1);

test("approved asset and upload origins use distinct CSP directives", () => {
  const csp = contentSecurityPolicy("test-nonce", {
    apiOrigin: "https://api.example.test/v1",
    assetOrigins: [
      "https://assets.example.test/public/",
      "https://assets.example.test",
    ],
    uploadOrigins: [
      "https://bucket.storage.example.test/uploads/",
      "https://second-bucket.example.test",
    ],
  });
  assert.deepEqual(directive(csp, "img-src"), [
    "'self'",
    "data:",
    "blob:",
    "https://assets.example.test",
  ]);
  assert.deepEqual(directive(csp, "connect-src"), [
    "'self'",
    "https://api.example.test",
    "https://bucket.storage.example.test",
    "https://second-bucket.example.test",
  ]);
  assert.match(csp, /style-src-attr 'none'/);
  assert.match(csp, /script-src 'self' 'nonce-test-nonce' 'strict-dynamic'/);
  assert.doesNotMatch(csp, /unsafe-inline|unsafe-eval/);
});

test("resource allowlists reject wildcard, credential, malformed and insecure production sources", () => {
  const invalid = [
    "https://*.example.test",
    "https://user:password@example.test",
    "data:text/plain,hello",
    "not a URL",
    "http://localhost:9000",
  ];
  const csp = contentSecurityPolicy("nonce", {
    assetOrigins: invalid,
    uploadOrigins: invalid,
  });
  assert.deepEqual(directive(csp, "img-src"), ["'self'", "data:", "blob:"]);
  assert.deepEqual(directive(csp, "connect-src"), ["'self'"]);
});

test("explicit development resource origins may use HTTP", () => {
  const csp = contentSecurityPolicy("nonce", {
    development: true,
    assetOrigins: ["http://localhost:9000/public"],
    uploadOrigins: ["http://localhost:9000/uploads"],
  });
  assert.ok(directive(csp, "img-src").includes("http://localhost:9000"));
  assert.ok(directive(csp, "connect-src").includes("http://localhost:9000"));
});
