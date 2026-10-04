import { expect, test } from "@playwright/test";

test("account owner reviews masked devices and revokes another session", async ({ page }) => {
  const sessions = [
    { id: "dss_current", device_label: "Chrome on Windows", peer_network: "192.0.2.0/24", scope: "dashboard", last_seen_at: "2026-10-04T12:00:00Z", expires_at: "2099-01-01T00:00:00Z", revoked_at: null as string | null, current: true },
    { id: "dss_other", device_label: "Safari on iOS", peer_network: "2001:db8::/48", scope: "dashboard", last_seen_at: "2026-10-03T12:00:00Z", expires_at: "2099-01-01T00:00:00Z", revoked_at: null as string | null, current: false },
  ];
  const revoked: string[] = [];
  await page.route("https://api.example.test/**", async (route) => {
    const request = route.request(), path = new URL(request.url()).pathname;
    const headers = { "Access-Control-Allow-Origin": "http://127.0.0.1:3005", "Access-Control-Allow-Credentials": "true", "Access-Control-Allow-Headers": "Authorization, Content-Type, X-Request-Id, X-IdentityCore-Session-Scope", "Access-Control-Allow-Methods": "GET, POST, OPTIONS" };
    if (request.method() === "OPTIONS") { await route.fulfill({ status: 204, headers }); return; }
    let data: unknown = {};
    if (path.endsWith("/auth/refresh")) data = { tokens: { access: "browser-access" } };
    else if (path.endsWith("/auth/me")) data = { user: { id: "usr_browser", email: "browser@example.test", full_name: "Browser Owner" } };
    else if (path.endsWith("/auth/sessions")) data = { results: sessions };
    else if (path.endsWith("/auth/sessions/dss_other/revoke")) { revoked.push("dss_other"); sessions[1].revoked_at = "2026-10-04T13:00:00Z"; data = { revoked: true }; }
    else if (path.endsWith("/auth/sessions/revoke-others")) { revoked.push("others"); data = { revoked: true }; }
    else if (path.includes("/projects")) data = { results: [] };
    else if (path.includes("/organization/me")) data = { status: "active" };
    await route.fulfill({ status: 200, headers, json: { success: true, data, request_id: "req_browser" } });
  });
  await page.goto("/settings/security");
  await expect(page.getByRole("heading", { name: "Your devices and sessions" })).toBeVisible();
  await expect(page.getByText("Chrome on Windows · This session")).toBeVisible();
  await expect(page.getByText(/2001:db8::\/48/)).toBeVisible();
  await page.getByRole("button", { name: "Sign out Safari on iOS" }).click();
  await expect(page.getByText("Revoked", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Sign out other sessions" }).click();
  await expect.poll(() => revoked).toEqual(["dss_other", "others"]);
  await expect(page.getByText("Chrome on Windows · This session")).toBeVisible();
});
