import { expect, test } from "@playwright/test";

test("an anonymous recipient accepts a fragment invitation without exposing it in the URL", async ({
  page,
}) => {
  let accepted: Record<string, unknown> | undefined;
  const token = "synthetic-one-use-invitation";
  const requests: string[] = [];
  page.on("request", (request) => requests.push(request.url()));
  await page.route("https://api.example.test/**", async (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    const headers = {
      "Access-Control-Allow-Origin": "http://127.0.0.1:3005",
      "Access-Control-Allow-Credentials": "true",
      "Access-Control-Allow-Headers":
        "Authorization, Content-Type, X-Request-Id, X-IdentityCore-Session-Scope",
      "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    };
    if (request.method() === "OPTIONS") {
      await route.fulfill({ status: 204, headers });
      return;
    }
    if (path.endsWith("/auth/team/invitations/accept")) {
      accepted = request.postDataJSON();
      await route.fulfill({
        status: 200,
        headers,
        json: {
          success: true,
          data: { accepted: true },
          request_id: "req_invitation",
        },
      });
    } else {
      await route.fulfill({
        status: 401,
        headers,
        json: {
          success: false,
          error: { code: "unauthenticated", message: "Sign in", details: {} },
          request_id: "req_invitation",
        },
      });
    }
  });
  await page.goto("/accept-invitation#token=" + token);
  await expect(page).toHaveURL("http://127.0.0.1:3005/accept-invitation");
  await page
    .getByLabel("Password", { exact: true })
    .fill("SyntheticPassword123!");
  await page
    .getByRole("button", { name: "Accept invitation", exact: true })
    .click();
  await expect(
    page.getByRole("link", { name: "Sign in to continue" }),
  ).toBeVisible();
  expect(accepted?.token).toBe(token);
  expect(requests.every((url) => !url.includes(token))).toBe(true);
  await expect(page.getByText(token, { exact: true })).toHaveCount(0);
});
