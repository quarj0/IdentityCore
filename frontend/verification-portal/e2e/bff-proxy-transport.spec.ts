import { expect, test } from "@playwright/test";
import {
  ProxyBodyLimitError,
  readBoundedProxyBody,
  requestIsSameOrigin,
  verificationProxyPath,
} from "../src/lib/bff-proxy";

test("proxy paths preserve Django's collection and slashless action routes", () => {
  expect(verificationProxyPath(["uploads"])).toBe("uploads/");
  for (const path of [
    "uploads/upl_Test/transfer",
    "sessions/ses_Test",
    "sessions/ses_Test/status",
    "sessions/ses_Test/consent",
    "sessions/ses_Test/consent/withdraw",
    "sessions/ses_Test/documents",
    "sessions/ses_Test/selfies",
    "sessions/ses_Test/liveness",
    "sessions/ses_Test/liveness/challenge",
    "sessions/ses_Test/mobile-handoff",
  ]) {
    expect(verificationProxyPath(path.split("/"))).toBe(path);
  }
  for (const path of [
    [],
    [".."],
    ["sessions", "ses_Test", "../admin"],
    ["uploads", "upl_Test", "unknown"],
    ["sessions", "ses_Test", "liveness", "unknown"],
    ["sessions", "ses_Test", "status", "extra"],
  ])
    expect(verificationProxyPath(path)).toBeNull();
});

function requestWithStream(body: ReadableStream<Uint8Array>) {
  const init: RequestInit & { duplex: "half" } = {
    method: "POST",
    body,
    duplex: "half",
  };
  return new Request(
    "https://portal.example.test/api/verification/uploads/",
    init,
  );
}

test("bounded reads preserve exact bytes at the limit without Content-Length", async () => {
  const stream = new ReadableStream<Uint8Array>({
    start(controller) {
      controller.enqueue(new Uint8Array([0, 255]));
      controller.enqueue(new Uint8Array([1, 254]));
      controller.close();
    },
  });
  const request = requestWithStream(stream);
  expect(request.headers.has("content-length")).toBe(false);
  const bytes = await readBoundedProxyBody(
    request,
    new AbortController().signal,
    4,
  );
  expect(Array.from(new Uint8Array(bytes!))).toEqual([0, 255, 1, 254]);
});

test("oversized chunked requests stop consumption and release the reader", async () => {
  let pulls = 0,
    cancelled = false;
  const stream = new ReadableStream<Uint8Array>({
    pull(controller) {
      pulls++;
      controller.enqueue(new Uint8Array(3));
      if (pulls === 100) controller.close();
    },
    cancel() {
      cancelled = true;
    },
  });
  await expect(
    readBoundedProxyBody(
      requestWithStream(stream),
      new AbortController().signal,
      4,
    ),
  ).rejects.toBeInstanceOf(ProxyBodyLimitError);
  expect(stream.locked).toBe(false);
  expect(pulls).toBeLessThan(100);
  await stream.cancel();
  expect(cancelled).toBe(true);
});

test("proxy timeout releases a blocked request-body read", async () => {
  let cancelled = false;
  const stream = new ReadableStream<Uint8Array>({
    cancel() {
      cancelled = true;
    },
  });
  const controller = new AbortController();
  const pending = readBoundedProxyBody(
    requestWithStream(stream),
    controller.signal,
    4,
  );
  controller.abort();
  await expect(pending).rejects.toMatchObject({ name: "AbortError" });
  expect(stream.locked).toBe(false);
  await stream.cancel();
  expect(cancelled).toBe(true);
});

test("same-origin validation uses the incoming Host without trusting forwarded hosts", () => {
  const request = (headers: Record<string, string>) =>
    new Request("http://localhost:3002/api/verification/uploads/", { headers });
  expect(
    requestIsSameOrigin(
      request({ Host: "127.0.0.1:3002", Origin: "http://127.0.0.1:3002" }),
    ),
  ).toBe(true);
  expect(
    requestIsSameOrigin(
      request({ Host: "127.0.0.1:3002", Origin: "https://attacker.example" }),
    ),
  ).toBe(false);
  expect(
    requestIsSameOrigin(
      request({
        Host: "127.0.0.1:3002",
        Origin: "http://127.0.0.1:3002",
        "Sec-Fetch-Site": "cross-site",
      }),
    ),
  ).toBe(false);
  expect(
    requestIsSameOrigin(
      request({
        Host: "127.0.0.1:3002",
        Origin: "http://attacker.example",
        "X-Forwarded-Host": "attacker.example",
      }),
    ),
  ).toBe(false);
  expect(
    requestIsSameOrigin(
      request({
        Host: "victim.example/private",
        Origin: "http://victim.example",
      }),
    ),
  ).toBe(false);
});

test("configured HTTPS origin supports an HTTP ingress hop without forwarding headers", () => {
  const previous = process.env.VERIFICATION_PUBLIC_ORIGIN;
  process.env.VERIFICATION_PUBLIC_ORIGIN = "https://verify.example.test";
  try {
    const request = (host: string, origin: string) =>
      new Request("http://localhost:3002/api/verification/session", {
        headers: { Host: host, Origin: origin, "X-Forwarded-Proto": "http" },
      });
    expect(
      requestIsSameOrigin(
        request("verify.example.test", "https://verify.example.test"),
      ),
    ).toBe(true);
    expect(
      requestIsSameOrigin(
        request("verify.example.test", "http://verify.example.test"),
      ),
    ).toBe(false);
    expect(
      requestIsSameOrigin(
        request("evil.example.test", "https://verify.example.test"),
      ),
    ).toBe(false);
    for (const invalid of [
      "https://verify.example.test/path",
      "https://user@verify.example.test",
      "https://verify.example.test?query=1",
      "not-an-origin",
    ]) {
      process.env.VERIFICATION_PUBLIC_ORIGIN = invalid;
      expect(
        requestIsSameOrigin(
          request("verify.example.test", "https://verify.example.test"),
        ),
      ).toBe(false);
    }
  } finally {
    if (previous === undefined) delete process.env.VERIFICATION_PUBLIC_ORIGIN;
    else process.env.VERIFICATION_PUBLIC_ORIGIN = previous;
  }
});
