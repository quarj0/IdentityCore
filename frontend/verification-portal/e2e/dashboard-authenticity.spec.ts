import { expect, test } from "@playwright/test";

test("review overlays stay aligned and can be toggled under strict CSP", async ({ page }) => {
  await page.route("https://api.example.test/**", async (route) => {
    const request = route.request(), path = new URL(request.url()).pathname;
    const headers = { "Access-Control-Allow-Origin": "http://127.0.0.1:3005", "Access-Control-Allow-Credentials": "true", "Access-Control-Allow-Headers": "Authorization, Content-Type, X-Request-Id, X-IdentityCore-Session-Scope", "Access-Control-Allow-Methods": "GET, POST, OPTIONS" };
    if (request.method() === "OPTIONS") { await route.fulfill({ status: 204, headers }); return; }
    let data: unknown = {};
    if (path.includes("/auth/refresh")) data = { tokens: { access: "browser-access" } };
    else if (path.includes("/auth/me")) data = { user: { id: "usr_browser", email: "browser@example.test", full_name: "Reviewer" } };
    else if (path.includes("/projects")) data = { results: [] };
    else if (path.includes("/organization/me")) data = { status: "active" };
    else if (path.endsWith("/authenticity")) data = { captures: [{ capture_id: "dcp_synthetic", verdict: "suspicious", confidence: .93, model_name: "synthetic-fixture", model_version: "1", source_size: [1000, 600], coordinate_space: "source_normalized", regions: [{ box: [.2,.25,.3,.1], reason: "copy_move", confidence: .91 }] }] };
    else if (path.endsWith("/preview")) data = { image: "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7" };
    else if (path.endsWith("/verifications/ver_synthetic")) data = { id: "ver_synthetic", status: "manual_review_required", purpose: "Synthetic", external_reference: "", verification_subject: { id: "sub_synthetic", full_name: "Synthetic" }, policy: { id: "pol_synthetic", name: "Test", version: 1 }, checks: {}, risk_assessment: null, decision: null, evidence_report: null, created_at: "2026-10-01T00:00:00Z", expires_at: "2026-10-05T00:00:00Z" };
    await route.fulfill({ status: 200, headers, json: { success: true, data, request_id: "req_synthetic" } });
  });
  const response = await page.goto("/manual-review/ver_synthetic");
  expect(response?.headers()["content-security-policy"]).toContain("style-src-attr 'none'");
  await expect(page.getByText("Duplicated region · confidence 91.0%", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "View document capture" }).click();
  const overlay = page.locator("svg[aria-label='Document capture with suspicious region annotations']");
  await expect(overlay).toBeVisible();
  await expect(overlay.locator("rect")).toHaveAttribute("x", "200");
  await expect(overlay.locator("rect")).toHaveAttribute("y", "150");
  await expect(overlay.locator("rect")).toHaveAttribute("width", "300");
  await page.getByLabel("Show suspicious regions").uncheck();
  await expect(overlay.locator("rect")).toHaveCount(0);
  await page.getByLabel("Show suspicious regions").check();
  await expect(overlay.locator("rect")).toHaveCount(1);
  await expect(page.getByRole("button", { name: "Approve", exact: true })).toBeVisible();
});
