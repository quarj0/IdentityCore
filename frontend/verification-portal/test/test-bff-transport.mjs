/** Real standalone BFF HTTP checks against a strict loopback TLS upstream. */
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { spawn, execFileSync } from "node:child_process";
import { createServer } from "node:https";
import { request as httpRequest } from "node:http";
import { createServer as createNetServer } from "node:net";
import { Readable } from "node:stream";
import { once } from "node:events";
import { mkdtemp, readFile, cp, rm, access, chmod } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const portal = process.argv[2]
  ? resolve(process.argv[2])
  : resolve(dirname(fileURLToPath(import.meta.url)), "..");
const standalone = join(portal, ".next/standalone/verification-portal");
const sessionId = "ses_BffTransport";
const token = "synthetic-bff-transport-token";
const routes = new Set([
  `/api/v1/sessions/${sessionId}`,
  `/api/v1/sessions/${sessionId}/status`,
  `/api/v1/sessions/${sessionId}/consent`,
  `/api/v1/sessions/${sessionId}/consent/withdraw`,
  `/api/v1/sessions/${sessionId}/liveness/challenge`,
  "/api/v1/uploads/",
  "/api/v1/uploads/upl_Test/transfer",
]);
let server,
  browserServer,
  child,
  temporary,
  logs = "",
  upstreamRequests = 0,
  checks = 0;
const appendLog = (chunk) => {
  logs = (logs + chunk.toString()).slice(-16000);
};
const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms).unref());
try {
  await access(join(standalone, "server.js"));
  temporary = await mkdtemp(join(tmpdir(), "identitycore-bff-transport-"));
  const keyPath = join(temporary, "loopback.key"),
    certificatePath = join(temporary, "loopback.crt");
  execFileSync(
    "openssl",
    [
      "req",
      "-x509",
      "-newkey",
      "rsa:2048",
      "-nodes",
      "-keyout",
      keyPath,
      "-out",
      certificatePath,
      "-days",
      "1",
      "-subj",
      "/CN=127.0.0.1",
      "-addext",
      "subjectAltName=IP:127.0.0.1",
    ],
    { stdio: "ignore" },
  );
  await chmod(keyPath, 0o600);
  server = createServer(
    { key: await readFile(keyPath), cert: await readFile(certificatePath) },
    async (request, response) => {
      upstreamRequests++;
      const url = new URL(request.url, "https://127.0.0.1");
      const handoff = url.pathname === "/api/v1/sessions/mobile-handoff/redeem";
      if (
        !handoff &&
        (!routes.has(url.pathname) ||
          request.headers.authorization !== `Bearer ${token}` ||
          request.headers["x-session-id"] !== sessionId)
      ) {
        response.writeHead(404, { "Content-Type": "application/json" });
        response.end("{}");
        return;
      }
      const chunks = [];
      for await (const chunk of request) chunks.push(chunk);
      const body = Buffer.concat(chunks);
      response.writeHead(200, { "Content-Type": "application/json" });
      if (handoff) {
        assert.equal(JSON.parse(body.toString()).handoff, "synthetic-handoff");
        response.end(
          JSON.stringify({
            data: { session_id: sessionId, session_token: token },
          }),
        );
        return;
      }
      response.end(
        JSON.stringify({
          data: {
            path: request.url,
            method: request.method,
            body: body.length < 4096 ? body.toString("hex") : "",
            bodyBytes: body.length,
            bodyDigest: createHash("sha256").update(body).digest("hex"),
            requestId: request.headers["x-request-id"],
          },
        }),
      );
    },
  );
  server.listen(0, "127.0.0.1");
  await once(server, "listening");
  const upstreamPort = server.address().port;
  const reservation = createNetServer();
  reservation.listen(0, "127.0.0.1");
  await once(reservation, "listening");
  const frontendPort = reservation.address().port;
  await new Promise((resolve) => reservation.close(resolve));
  await cp(join(portal, ".next/static"), join(standalone, ".next/static"), {
    recursive: true,
  });
  await cp(join(portal, "public"), join(standalone, "public"), {
    recursive: true,
  });
  const startPortal = (extraEnvironment = {}) => {
    const processChild = spawn(
      process.execPath,
      [join(standalone, "server.js")],
      {
        cwd: portal,
        env: {
          ...process.env,
          VERIFICATION_PUBLIC_ORIGIN: "",
          ...extraEnvironment,
          PORT: String(frontendPort),
          HOSTNAME: "127.0.0.1",
          API_ORIGIN: `https://127.0.0.1:${upstreamPort}`,
          DEPLOYMENT_VERSION: "bff-transport-test",
          NODE_EXTRA_CA_CERTS: certificatePath,
        },
        stdio: ["ignore", "pipe", "pipe"],
      },
    );
    processChild.stdout.on("data", appendLog);
    processChild.stderr.on("data", appendLog);
    return processChild;
  };
  const origin = `http://127.0.0.1:${frontendPort}`;
  const waitForPortal = async () => {
    let ready = false;
    for (let attempt = 0; attempt < 100; attempt++) {
      if (child.exitCode !== null)
        throw new Error(
          "Standalone verification portal exited before readiness",
        );
      try {
        if ((await fetch(`${origin}/api/health`)).status === 200) {
          ready = true;
          break;
        }
      } catch {}
      await delay(100);
    }
    assert(ready, "Standalone verification portal did not become ready");
  };
  child = startPortal();
  await waitForPortal();
  const headers = {
    Cookie: `__Host-identitycore_verify=${token}; __Host-identitycore_verify_id=${sessionId}`,
    Origin: origin,
    "X-Request-Id": "bff-transport-synthetic",
    "Content-Type": "application/json",
  };
  for (const [path, payload] of [
    ["session", { sessionId, sessionToken: token }],
    ["handoff", { handoff: "synthetic-handoff" }],
  ]) {
    const exchanged = await fetch(`${origin}/api/verification/${path}`, {
      method: "POST",
      headers: {
        Origin: origin,
        "Content-Type": "application/json",
        "X-Request-Id": "bff-transport-synthetic",
      },
      body: JSON.stringify(payload),
    });
    assert.equal(exchanged.status, 200);
    assert.equal(
      (await exchanged.text()).includes(token),
      false,
      "Private session token must remain HttpOnly",
    );
    const cookies = exchanged.headers.getSetCookie();
    assert.equal(cookies.length, 2);
    for (const cookie of cookies) {
      assert.match(cookie, /HttpOnly/i);
      assert.match(cookie, /Secure/i);
      assert.match(cookie, /SameSite=Strict/i);
    }
    headers.Cookie = cookies.map((cookie) => cookie.split(";")[0]).join("; ");
    checks++;
  }
  for (const [path, method, body] of [
    [`sessions/${sessionId}`, "GET", undefined],
    [`sessions/${sessionId}/consent`, "POST", '{"accepted":true}'],
    ["uploads/", "POST", '{"kind":"document"}'],
    ["uploads/upl_Test/transfer", "POST", new Uint8Array([0, 255, 1, 254])],
    [`sessions/${sessionId}/status?checkpoint=3`, "GET", undefined],
    [`sessions/${sessionId}/consent/withdraw`, "POST", "{}"],
    [`sessions/${sessionId}/liveness/challenge`, "POST", "{}"],
  ]) {
    const response = await fetch(`${origin}/api/verification/${path}`, {
      method,
      headers,
      body,
    });
    if (response.status !== 200)
      throw new Error(
        `Unexpected status for ${path}: ${response.status} ${await response.text()}`,
      );
    const result = await response.json();
    assert.equal(result.data.path, `/api/v1/${path}`);
    assert.equal(result.data.method, method);
    assert.equal(
      result.data.body,
      body ? Buffer.from(body).toString("hex") : "",
    );
    assert.equal(result.data.requestId, "bff-transport-synthetic");
    assert.match(response.headers.get("cache-control"), /no-store/);
    assert.equal(response.headers.get("x-content-type-options"), "nosniff");
    assert.equal(response.headers.get("x-frame-options"), "DENY");
    assert.match(
      response.headers.get("content-security-policy"),
      /default-src 'none'/,
    );
    checks++;
  }
  const largePayload = Buffer.alloc(11 * 1024 * 1024, 97);
  const largeResponse = await fetch(
    `${origin}/api/verification/uploads/upl_Test/transfer`,
    {
      method: "POST",
      headers: { ...headers, "Content-Type": "application/octet-stream" },
      body: Readable.from([largePayload]),
      duplex: "half",
    },
  );
  assert.equal(largeResponse.status, 200);
  const largeResult = await largeResponse.json();
  assert.equal(largeResult.data.bodyBytes, largePayload.length);
  assert.equal(
    largeResult.data.bodyDigest,
    createHash("sha256").update(largePayload).digest("hex"),
  );
  checks++;
  const beforeDenied = upstreamRequests;
  assert.equal(
    (await fetch(`${origin}/api/verification/sessions/ses_Other`, { headers }))
      .status,
    403,
  );
  checks++;
  assert.equal(
    (
      await fetch(`${origin}/api/verification/uploads/upl_Test/unknown`, {
        headers,
      })
    ).status,
    404,
  );
  checks++;
  assert.equal(
    (
      await fetch(`${origin}/api/verification/sessions/${sessionId}/consent`, {
        method: "POST",
        headers: { ...headers, Origin: "https://attacker.example" },
        body: "{}",
      })
    ).status,
    403,
  );
  checks++;
  async function oversizedRequest(path, chunkBytes, totalChunks) {
    return await new Promise((resolve, reject) => {
      let produced = 0,
        received = false;
      async function* source() {
        const chunk = Buffer.alloc(chunkBytes);
        for (let i = 0; i < totalChunks; i++) {
          produced++;
          yield chunk;
        }
      }
      const body = Readable.from(source());
      const request = httpRequest(
        `${origin}/api/verification/${path}`,
        {
          method: "POST",
          headers: {
            ...headers,
            "Content-Type": "application/octet-stream",
            "Transfer-Encoding": "chunked",
          },
        },
        (response) => {
          received = true;
          body.unpipe(request);
          body.destroy();
          response.resume();
          response.on("error", reject);
          response.on("end", () => {
            request.destroy();
            resolve({ status: response.statusCode, produced });
          });
        },
      );
      request.setTimeout(15000, () =>
        request.destroy(
          new Error("Oversized request was not rejected promptly"),
        ),
      );
      request.on("error", (error) => {
        if (!received) reject(error);
      });
      body.on("error", reject);
      body.pipe(request);
    });
  }
  for (const [path, chunkBytes, totalChunks] of [
    ["uploads", 1024 * 1024, 100],
    ["session", 1024, 100000],
    ["handoff", 1024, 100000],
  ]) {
    const rejected = await oversizedRequest(path, chunkBytes, totalChunks);
    assert.equal(rejected.status, 413);
    assert(
      rejected.produced < totalChunks,
      "Oversized input must stop before the full stream is consumed",
    );
    checks++;
  }
  const badCredential = await fetch(`${origin}/api/verification/session`, {
    method: "POST",
    headers,
    body: JSON.stringify({ sessionId, sessionToken: { unexpected: "object" } }),
  });
  assert.equal(badCredential.status, 400);
  checks++;
  assert.equal(
    upstreamRequests,
    beforeDenied,
    "Rejected requests must not reach the gateway",
  );
  let browserChecks = 0;
  if (process.env.BFF_BROWSER_TEST === "true") {
    const { chromium, webkit } = await import("@playwright/test");
    browserServer = createServer(
      { key: await readFile(keyPath), cert: await readFile(certificatePath) },
      (request, response) => {
        const upstream = httpRequest(
          {
            hostname: "127.0.0.1",
            port: frontendPort,
            path: request.url,
            method: request.method,
            // The ingress intentionally supplies no forwarding scheme.
            headers: request.headers,
          },
          (incoming) => {
            response.writeHead(incoming.statusCode, incoming.headers);
            incoming.pipe(response);
          },
        );
        upstream.on("error", (error) => response.destroy(error));
        request.on("aborted", () => upstream.destroy());
        request.pipe(upstream);
      },
    );
    browserServer.listen(0, "127.0.0.1");
    await once(browserServer, "listening");
    const browserOrigin = `https://127.0.0.1:${browserServer.address().port}`;
    child.kill("SIGTERM");
    await once(child, "exit");
    child = startPortal({ VERIFICATION_PUBLIC_ORIGIN: browserOrigin });
    await waitForPortal();
    for (const engine of [chromium, webkit]) {
      const browser = await engine.launch();
      try {
        // The generated loopback certificate is scoped to this test server.
        const page = await browser.newPage({ ignoreHTTPSErrors: true });
        await page.goto(browserOrigin);
        // Browser requests reach the actual standalone BFF. Only the server's
        // upstream is a mock; page.route never intercepts these requests.
        const result = await page.evaluate(
          async ({ sessionId, token }) => {
            const exchange = await fetch("/api/verification/session", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ sessionId, sessionToken: token }),
            });
            const exchangeBody = await exchange.text();
            const status = await fetch(
              `/api/verification/sessions/${sessionId}/status`,
            );
            const statusBody = await status.json();
            const upload = await fetch("/api/verification/uploads", {
              method: "POST",
              body: new Uint8Array([0, 255, 1, 254]),
            });
            const uploadBody = await upload.json();
            const handoff = await fetch("/api/verification/handoff", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ handoff: "synthetic-handoff" }),
            });
            return {
              exchange: exchange.status,
              exchangeBody,
              status: status.status,
              statusBody,
              upload: upload.status,
              uploadBody,
              handoff: handoff.status,
              handoffBody: await handoff.text(),
              visibleCookies: document.cookie,
            };
          },
          { sessionId, token },
        );
        assert.equal(result.exchange, 200);
        assert(!result.exchangeBody.includes(token));
        assert.equal(result.status, 200);
        assert.equal(
          result.statusBody.data.path,
          `/api/v1/sessions/${sessionId}/status`,
        );
        assert.equal(result.upload, 200);
        assert.equal(result.uploadBody.data.path, "/api/v1/uploads/");
        assert.equal(result.uploadBody.data.body, "00ff01fe");
        assert.equal(result.handoff, 200);
        assert(!result.handoffBody.includes(token));
        assert(!result.visibleCookies.includes(token));
        browserChecks += 4;
      } finally {
        await browser.close();
      }
    }
  }
  console.log(
    JSON.stringify({
      status: "passed",
      http_checks: checks,
      browser_checks: browserChecks,
      upstream_requests: upstreamRequests,
      chunked_body_limit_bytes: 26 * 1024 * 1024,
    }),
  );
} catch (error) {
  console.error(error.message);
  if (logs) console.error(logs);
  process.exitCode = 1;
} finally {
  if (child && child.exitCode === null && child.signalCode === null) {
    child.kill("SIGTERM");
    await Promise.race([once(child, "exit"), delay(5000)]);
    if (child.exitCode === null && child.signalCode === null) {
      child.kill("SIGKILL");
      await once(child, "exit");
    }
  }
  if (browserServer) {
    browserServer.closeAllConnections();
    await new Promise((resolve) => browserServer.close(resolve));
  }
  if (server) {
    server.closeAllConnections();
    await new Promise((resolve) => server.close(resolve));
  }
  if (temporary) await rm(temporary, { recursive: true, force: true });
}
