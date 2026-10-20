import { expect, test } from "@playwright/test";

const png = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=",
  "base64",
);

test("production CSP permits approved branding transfers and native onboarding progress", async ({
  page,
  baseURL,
}) => {
  await page.route("https://api.example.test/**", async (route) => {
    const request = route.request();
    const headers = {
      "Access-Control-Allow-Origin": baseURL!,
      "Access-Control-Allow-Credentials": "true",
      "Access-Control-Allow-Headers":
        "Authorization, Content-Type, X-Request-Id, X-IdentityCore-Session-Scope",
      "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    };
    if (request.method() === "OPTIONS")
      return route.fulfill({ status: 204, headers });
    if (new URL(request.url()).pathname === "/api/graphql") {
      return route.fulfill({
        headers,
        json: {
          data: {
            organizationOnboarding: {
              organizationName: "Synthetic CSP workspace",
              organizationTier: "sandbox",
              organizationStatus: "pending_review",
              tenantStatus: "active",
              currentStep: "administrator_identity_verification",
              onboardingStatus: "in_progress",
              emailVerifiedAt: "2026-10-01T00:00:00Z",
              organizationVerificationSubmittedAt: "2026-10-02T00:00:00Z",
              organizationVerificationReviewStatus: "submitted",
              administratorIdentityVerificationStatus: "not_started",
            },
          },
        },
      });
    }
    const data = request.url().includes("/auth/refresh")
      ? { tokens: { access: "synthetic-access" } }
      : { user: { email: "synthetic@example.test" } };
    return route.fulfill({ headers, json: { success: true, data } });
  });
  let images = 0;
  let uploads = 0;
  let unlistedRequests = 0;
  await page.route("https://assets.example.test/**", async (route) => {
    images++;
    await route.fulfill({ contentType: "image/png", body: png });
  });
  await page.route("https://bucket.storage.example.test/**", async (route) => {
    if (route.request().method() === "PUT") uploads++;
    await route.fulfill({
      status: route.request().method() === "OPTIONS" ? 204 : 200,
      headers: {
        "Access-Control-Allow-Origin": baseURL!,
        "Access-Control-Allow-Methods": "PUT, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
      },
    });
  });
  await page.route("https://unlisted.example.test/**", async (route) => {
    unlistedRequests++;
    await route.fulfill({
      status: 200,
      headers: { "Access-Control-Allow-Origin": "*" },
    });
  });

  const response = await page.goto("/onboarding");
  expect(response).not.toBeNull();
  if (!response) throw new Error("Missing page response");
  const csp = response.headers()["content-security-policy"];
  expect(csp).toContain("https://assets.example.test");
  expect(csp).toContain("https://bucket.storage.example.test");
  expect(csp).toContain("style-src-attr 'none'");
  expect(csp).not.toMatch(/unsafe-inline|unsafe-eval/);
  const nonce = csp.match(/'nonce-([^']+)'/)?.[1];
  const scripts =
    (await response.text()).match(
      /<script\b[^>]*\bsrc="[^"]*\/_next\/[^\"]*"[^>]*>/g,
    ) ?? [];
  expect(scripts.length).toBeGreaterThan(0);
  for (const script of scripts) expect(script).toContain(`nonce="${nonce}"`);

  await expect(
    page.getByRole("progressbar", { name: "Onboarding progress" }),
  ).toHaveAttribute("aria-valuenow", "40");
  const native = page.locator("progress");
  await expect(native).toBeVisible();
  await expect(native).toHaveJSProperty("value", 40);
  await expect(native).toHaveJSProperty("max", 100);
  expect(await native.getAttribute("style")).toBeNull();

  expect(
    await page.evaluate(
      () =>
        new Promise<boolean>((resolve) => {
          const image = new Image();
          image.onload = () => resolve(true);
          image.onerror = () => resolve(false);
          image.src = "https://assets.example.test/public/logo.png";
        }),
    ),
  ).toBe(true);
  expect(
    await page.evaluate(
      async () =>
        (
          await fetch("https://bucket.storage.example.test/branding/logo.png", {
            method: "PUT",
            headers: { "Content-Type": "image/png" },
            body: new Uint8Array([1, 2, 3]),
          })
        ).status,
    ),
  ).toBe(200);
  expect(images).toBe(1);
  expect(uploads).toBe(1);
  expect(
    await page.evaluate(async () => {
      try {
        await fetch("https://unlisted.example.test/blocked");
        return "allowed";
      } catch {
        return "blocked";
      }
    }),
  ).toBe("blocked");
  expect(unlistedRequests).toBe(0);
});
