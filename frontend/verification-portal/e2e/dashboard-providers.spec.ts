import { expect, test } from "@playwright/test";

test("provider setup keeps credentials private and requires a new production proposal", async ({ page }) => {
  type Configuration = { id: string; environment: string; version: number; status: string; configuration: { endpoint_url: string }; diff: Record<string, unknown>; test_succeeded: boolean; tested_at: string | null; approved_by: string | null };
  const configs: Configuration[] = [];
  const submissions: Record<string, unknown>[] = [];
  const provider = { id: "prv_browser", tenant_id: "ten_browser", name: "Synthetic Provider", manifest: { capabilities: { risk_check: { countries: ["*"], document_types: ["*"] } } } };
  await page.route("https://api.example.test/**", async (route) => {
    const request = route.request(), path = new URL(request.url()).pathname;
    const headers = { "Access-Control-Allow-Origin": "http://127.0.0.1:3005", "Access-Control-Allow-Credentials": "true", "Access-Control-Allow-Headers": "Authorization, Content-Type, X-Request-Id, X-IdentityCore-Session-Scope", "Access-Control-Allow-Methods": "GET, POST, OPTIONS" };
    if (request.method() === "OPTIONS") { await route.fulfill({ status: 204, headers }); return; }
    let data: unknown = {};
    if (path.includes("/auth/refresh")) data = { tokens: { access: "browser-access" } };
    else if (path.includes("/auth/me")) data = { user: { id: "usr_browser", email: "browser@example.test", full_name: "Browser Manager" } };
    else if (path.includes("/projects")) data = { results: [] };
    else if (path.includes("/organization/me")) data = { status: "active" };
    else if (path.endsWith("/providers/")) data = { results: [provider] };
    else if (path.endsWith("/providers/setup/")) { const body = request.postDataJSON(); expect(body.manifest.capabilities).toHaveProperty("risk_check"); data = { ...provider, name: body.name }; }
    else if (path.endsWith("/configurations/")) {
      if (request.method() === "GET") data = { results: configs };
      else { const body = request.postDataJSON(); submissions.push(body); const config = { id: `pec_${configs.length + 1}`, environment: body.environment, version: 1, status: "draft", configuration: body.configuration, diff: {}, test_succeeded: false, tested_at: null, approved_by: null }; configs.push(config); data = config; }
    } else if (path.includes("/configurations/pec_")) {
      const config = configs.find((item) => path.includes(item.id));
      if (config && path.endsWith("/test/")) { config.test_succeeded = true; config.tested_at = "2026-10-04T12:00:00Z"; data = config; }
      if (config && path.endsWith("/activate/")) { config.status = "active"; data = config; }
      if (path.endsWith("/assign/")) data = { route_id: "pvr_browser" };
    }
    await route.fulfill({ status: 200, headers, json: { success: true, data, request_id: "req_browser" } });
  });
  const response = await page.goto("/providers");
  expect(response?.headers()["content-security-policy"]).toContain("strict-dynamic");
  await expect(page.getByRole("heading", { name: "Providers", exact: true })).toBeVisible();
  await page.getByRole("combobox", { name: "Provider type", exact: true }).selectOption("risk");
  await page.getByLabel("Name", { exact: true }).fill("Synthetic New Provider");
  await page.getByLabel("risk check", { exact: true }).check();
  await page.getByLabel("Processing regions").fill("eu-west-1");
  await page.getByLabel("Provider retention in days").fill("0");
  await page.getByLabel("Processor name").fill("Synthetic processor");
  await page.getByLabel("Transfer safeguards").fill("No onward transfer");
  await page.getByRole("button", { name: "Add provider", exact: true }).click();
  await page.getByLabel("HTTPS endpoint").fill("https://provider.example.test/sandbox");
  await page.getByLabel("New environment credential").fill("browser-sandbox-credential");
  await page.getByRole("button", { name: "Request configuration" }).click();
  await expect(page.getByLabel("New environment credential")).toHaveValue("");
  await page.getByRole("button", { name: "Test connection" }).click();
  await expect(page.getByRole("status")).toContainText("passed");
  await page.getByRole("button", { name: "Activate sandbox" }).click();
  await page.getByRole("button", { name: "Publish assignment" }).click();
  await expect(page.getByRole("status")).toContainText("route published");
  await page.getByRole("combobox", { name: "Environment", exact: true }).selectOption("production");
  await page.getByLabel("HTTPS endpoint").fill("https://provider.example.test/production");
  await page.getByLabel("New environment credential").fill("browser-production-credential");
  await page.getByRole("button", { name: "Request configuration" }).click();
  await expect(page.getByLabel("New environment credential")).toHaveValue("");
  expect(submissions[1]).toMatchObject({ environment: "production", source_id: "pec_1", credentials: { api_key: "browser-production-credential" } });
  await expect(page.getByRole("button", { name: "Approve production" })).toBeVisible();
  await expect(page.locator("body")).not.toContainText("browser-sandbox-credential");
  await expect(page.locator("body")).not.toContainText("browser-production-credential");
  expect(await page.evaluate(() => JSON.stringify(localStorage) + JSON.stringify(sessionStorage))).not.toContain("credential");
});

test("legacy onboarding email redirect preserves async query parameters", async ({ page }) => {
  await page.route("https://api.example.test/**", (route) => route.fulfill({ status: 401, json: { success: false } }));
  await page.goto("/onboarding/verify-email?email=synthetic%40example.test&token=synthetic-token&tag=one&tag=two");
  await expect(page).toHaveURL(/\/verify-email\?email=synthetic%40example.test&token=synthetic-token&tag=one&tag=two$/);
});
