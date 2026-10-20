import assert from "node:assert/strict";
import { test } from "node:test";
import {
  consumeSessionCredentials,
  clearSessionCredentials,
} from "../src/lib/session-credentials.ts";
import { securityHeaders } from "../src/security-headers.ts";

async function withBrowser(url, run) {
  const originalWindow = globalThis.window;
  const originalFetch = globalThis.fetch;
  let location = new URL(url);
  globalThis.window = {
    get location() {
      return location;
    },
    history: {
      replaceState(_state, _title, path) {
        location = new URL(path, location);
      },
    },
    setTimeout,
    clearTimeout,
  };
  try {
    await run();
  } finally {
    globalThis.fetch = originalFetch;
    if (originalWindow === undefined) delete globalThis.window;
    else globalThis.window = originalWindow;
  }
}

test("failed exchange preserves the link for reload and success clears only the fragment", async () => {
  await withBrowser(
    "https://verify.example.test/verify/ses_retry?locale=en#token=synthetic-retry",
    async () => {
      let calls = 0;
      globalThis.fetch = async () =>
        ++calls === 1
          ? new Response("unavailable", { status: 502 })
          : Response.json({ success: true });
      await assert.rejects(consumeSessionCredentials("ses_retry"));
      assert.equal(window.location.hash, "#token=synthetic-retry");
      await consumeSessionCredentials("ses_retry");
      assert.equal(calls, 2);
      assert.equal(
        window.location.href,
        "https://verify.example.test/verify/ses_retry?locale=en",
      );
    },
  );
});

test("duplicate initialization shares a pending exchange until the credential is accepted", async () => {
  await withBrowser(
    "https://verify.example.test/verify/ses_pending#token=synthetic-pending",
    async () => {
      let release,
        calls = 0;
      globalThis.fetch = async () => {
        calls++;
        return new Promise((resolve) => {
          release = resolve;
        });
      };
      const first = consumeSessionCredentials("ses_pending");
      const second = consumeSessionCredentials("ses_pending");
      assert.equal(calls, 1);
      assert.equal(window.location.hash, "#token=synthetic-pending");
      release(Response.json({ success: true }));
      assert.deepEqual(await Promise.all([first, second]), [
        { sessionId: "ses_pending" },
        { sessionId: "ses_pending" },
      ]);
      assert.equal(window.location.hash, "");
    },
  );
});

test("network rejection and invalid success envelopes keep credentials retryable", async () => {
  await withBrowser(
    "https://verify.example.test/verify/ses_network#token=synthetic-network",
    async () => {
      globalThis.fetch = async () => {
        throw new TypeError("Network failure");
      };
      await assert.rejects(consumeSessionCredentials("ses_network"));
      assert.equal(window.location.hash, "#token=synthetic-network");
      globalThis.fetch = async () => Response.json({ success: false });
      await assert.rejects(consumeSessionCredentials("ses_network"));
      assert.equal(window.location.hash, "#token=synthetic-network");
      globalThis.fetch = async () => Response.json({ success: true });
      await consumeSessionCredentials("ses_network");
      assert.equal(window.location.hash, "");
    },
  );
});

test("clearing a flow selects only its session", async () => {
  await withBrowser("https://verify.example.test/", async () => {
    let init;
    globalThis.fetch = async (_url, options) => {
      init = options;
      return Response.json({ success: true });
    };
    clearSessionCredentials("ses_selected");
    assert.equal(init.method, "DELETE");
    assert.equal(init.headers["X-Session-Id"], "ses_selected");
  });
});

test("eval is permitted for development hot reload and forbidden in production", () => {
  const original = process.env.NODE_ENV;
  try {
    process.env.NODE_ENV = "development";
    assert.match(
      securityHeaders("synthetic-nonce")["Content-Security-Policy"],
      /'unsafe-eval'/,
    );
    process.env.NODE_ENV = "production";
    const policy =
      securityHeaders("synthetic-nonce")["Content-Security-Policy"];
    assert.doesNotMatch(policy, /'unsafe-eval'|'unsafe-inline'/);
    assert.match(policy, /'nonce-synthetic-nonce'/);
  } finally {
    if (original === undefined) delete process.env.NODE_ENV;
    else process.env.NODE_ENV = original;
  }
});
