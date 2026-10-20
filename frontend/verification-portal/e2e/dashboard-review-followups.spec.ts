import { expect, test, type Page } from "@playwright/test";

async function mockWorkspace(page: Page, canApprove = false) {
  await page.route("https://api.example.test/**", async (route) => {
    const request = route.request();
    const headers = {
      "Access-Control-Allow-Origin": "http://127.0.0.1:3005",
      "Access-Control-Allow-Credentials": "true",
      "Access-Control-Allow-Headers":
        "Authorization, Content-Type, Idempotency-Key, X-Request-Id, X-IdentityCore-Session-Scope",
      "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    };
    if (request.method() === "OPTIONS")
      return route.fulfill({ status: 204, headers });
    const path = new URL(request.url()).pathname;
    let data: unknown = {};
    if (path.includes("/auth/refresh"))
      data = { tokens: { access: "synthetic-access" } };
    else if (path.includes("/auth/me"))
      data = { user: { email: "synthetic@example.test" } };
    else if (path.includes("/organization/me")) data = { status: "active" };
    else if (path.includes("/projects")) data = { results: [] };
    else if (path.includes("/webhook-endpoints/wh_synthetic/rotate"))
      data = { secret: "synthetic-rotated-secret", signing_secret_version: 2 };
    else if (
      path.endsWith("/webhook-endpoints/") &&
      request.method() === "POST"
    ) {
      return route.fulfill({
        status: 400,
        headers,
        json: {
          success: false,
          error: {
            code: "validation_error",
            message: "Synthetic create rejected",
            details: {},
          },
        },
      });
    } else if (path.includes("/webhook-endpoints"))
      data = {
        results: [
          {
            id: "wh_synthetic",
            url: "https://example.test/hook",
            events: ["verification.failed"],
            status: "active",
          },
        ],
      };
    else if (path.endsWith("/authenticity")) data = { captures: [] };
    else if (path.replace(/\/$/, "").endsWith("/verifications/ver_synthetic"))
      data = {
        id: "ver_synthetic",
        status: "manual_review_required",
        purpose: "Synthetic review",
        verification_subject: {
          id: "sub_synthetic",
          full_name: "Synthetic subject",
        },
        policy: { name: "Synthetic policy" },
        workflow: null,
        checks: {},
        risk_assessment: null,
        evidence_report: null,
        decision: {
          decision: "verified",
          proposed_decision: "verified",
          decision_type: "manual",
          approval_status: "pending",
          can_approve: canApprove,
        },
      };
    else if (path === "/api/graphql")
      return route.fulfill({ headers, json: { data: {} } });
    return route.fulfill({ headers, json: { success: true, data } });
  });
}

for (const canApprove of [false, true]) {
  test(`pending proposal shows ${canApprove ? "checker controls" : "independent waiting state"}`, async ({
    page,
  }) => {
    await mockWorkspace(page, canApprove);
    await page.goto("/manual-review/ver_synthetic");
    if (canApprove) {
      await expect(
        page.getByText("Independent approval", { exact: true }),
      ).toBeVisible();
      await expect(
        page.getByRole("button", { name: "Approve", exact: true }),
      ).toBeVisible();
    } else {
      await expect(
        page.getByText("Awaiting independent review", { exact: true }),
      ).toBeVisible();
      await expect(
        page.getByRole("button", { name: "Approve", exact: true }),
      ).toHaveCount(0);
      await expect(page.getByLabel("Reviewer notes")).toHaveCount(0);
    }
  });
}

test("failed endpoint create preserves the displayed rotation secret", async ({
  page,
}) => {
  await mockWorkspace(page);
  page.on("dialog", (dialog) => dialog.accept());
  await page.goto("/webhooks");
  await page.getByRole("button", { name: "Rotate secret" }).click();
  const secret = page.getByLabel("New webhook signing secret");
  await expect(secret).toHaveValue("synthetic-rotated-secret");
  await page.getByLabel("Endpoint URL").fill("https://example.test/rejected");
  await page.getByRole("button", { name: "Add webhook" }).click();
  await expect(
    page.getByText(
      "We could not complete your request. Check the information and try again.",
      { exact: true },
    ),
  ).toBeVisible();
  await expect(secret).toHaveValue("synthetic-rotated-secret");
});
