import { expect, test } from "@playwright/test";

test("organization usage separates sandbox and production", async ({ page }) => {
  await page.route("https://api.example.test/**", async (route) => {
    const request = route.request(), path = new URL(request.url()).pathname;
    const headers = { "Access-Control-Allow-Origin": "http://127.0.0.1:3005", "Access-Control-Allow-Credentials": "true", "Access-Control-Allow-Headers": "Authorization, Content-Type, X-Request-Id, X-IdentityCore-Session-Scope", "Access-Control-Allow-Methods": "GET, POST, OPTIONS" };
    if (request.method() === "OPTIONS") { await route.fulfill({ status: 204, headers }); return; }
    let data: unknown = {};
    if (path.includes("/auth/refresh")) data = { tokens: { access: "browser-access" } };
    else if (path.includes("/auth/me")) data = { user: { id: "usr_browser", email: "browser@example.test", full_name: "Usage manager" } };
    else if (path.includes("/projects")) data = { results: [] };
    else if (path.includes("/organization/me")) data = { status: "active" };
    else if (path.endsWith("/api-clients/usage")) data = { results: ["sandbox", "production"].map((environment, index) => ({ environment, minute: { limit: 100, accepted: 11 + index, denied: 3 + index, remaining: 89 - index, resets_at: "2026-10-04T13:01:00Z" }, month: { limit: 10000, accepted: 111 + index, denied: 5, remaining: 9889 - index, resets_at: "2026-11-01T00:00:00Z" } })) };
    await route.fulfill({ status: 200, headers, json: { success: true, data, request_id: "req_synthetic" } });
  });
  await page.goto("/api-usage");
  await expect(page.getByRole("heading", { name: "API usage", exact: true })).toBeVisible();
  const sandbox = page.locator("section").filter({ has: page.getByRole("heading", { name: "sandbox", exact: true }) });
  const production = page.locator("section").filter({ has: page.getByRole("heading", { name: "production", exact: true }) });
  await expect(sandbox.getByRole("cell", { name: "11", exact: true })).toBeVisible();
  await expect(production.getByRole("cell", { name: "12", exact: true })).toBeVisible();
  await expect(sandbox.getByRole("cell", { name: "3", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Refresh usage" }).click();
  await expect(production.getByRole("cell", { name: "12", exact: true })).toBeVisible();
});
