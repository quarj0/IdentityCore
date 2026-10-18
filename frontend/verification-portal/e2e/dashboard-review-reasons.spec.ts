import { expect, test } from "@playwright/test";

test("reviewer can resolve an automatically routed case with an outcome-specific reason", async ({
  page,
  baseURL,
}) => {
  const submissions: Record<string, unknown>[] = [];
  await page.route("https://api.example.test/**", async (route) => {
    const request = route.request(),
      path = new URL(request.url()).pathname;
    const headers = {
      "Access-Control-Allow-Origin": baseURL!,
      "Access-Control-Allow-Credentials": "true",
      "Access-Control-Allow-Headers":
        "Authorization, Content-Type, X-Request-Id, X-IdentityCore-Session-Scope, Idempotency-Key",
      "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    };
    if (request.method() === "OPTIONS") {
      await route.fulfill({ status: 204, headers });
      return;
    }
    let data: unknown = {};
    if (path.endsWith("/auth/refresh"))
      data = { tokens: { access: "synthetic-access" } };
    else if (path.endsWith("/auth/me"))
      data = {
        user: { email: "reviewer@example.test", full_name: "Reviewer" },
      };
    else if (path.includes("/projects")) data = { results: [] };
    else if (path.includes("/organization/me")) data = { status: "active" };
    else if (path.endsWith("/authenticity")) data = { captures: [] };
    else if (path.endsWith("/decision")) {
      submissions.push(request.postDataJSON());
      data = { decision: "rejected" };
    } else if (path.endsWith("/verifications/ver_reason"))
      data = {
        id: "ver_reason",
        status: "manual_review_required",
        purpose: "Synthetic",
        external_reference: "",
        verification_subject: {
          id: "sub_synthetic",
          full_name: "Synthetic Subject",
        },
        policy: {
          name: "Review policy",
          version: 1,
          review_reason_rules: {
            version: 1,
            outcomes: {
              verified: {
                codes: ["evidence_confirmed"],
                notes_required: false,
              },
              rejected: { codes: ["evidence_mismatch"], notes_required: true },
              failed: { codes: ["evidence_unavailable"], notes_required: true },
            },
            organization_facing_codes: ["evidence_mismatch"],
          },
        },
        checks: {},
        risk_assessment: null,
        decision: {
          decision: "manual_review_required",
          decision_type: "automatic",
          approval_status: "not_required",
          reason_detail: "Synthetic review route",
        },
        evidence_report: null,
        created_at: "2026-10-01T00:00:00Z",
        expires_at: "2099-01-01T00:00:00Z",
      };
    await route.fulfill({
      status: 200,
      headers,
      json: { success: true, data },
    });
  });
  await page.goto("/manual-review/ver_reason");
  await page.getByLabel("Reason code").selectOption("evidence_confirmed");
  await page.getByRole("button", { name: "Reject", exact: true }).click();
  await expect(
    page.getByText(
      "Choose a reason configured for this outcome and provide required notes.",
    ),
  ).toBeVisible();
  expect(submissions).toHaveLength(0);
  await page.getByLabel("Reason code").selectOption("evidence_mismatch");
  await page.getByRole("button", { name: "Reject", exact: true }).click();
  expect(submissions).toHaveLength(0);
  await page
    .getByLabel("Reviewer notes")
    .fill("Independent evidence assessment");
  await page.getByRole("button", { name: "Reject", exact: true }).click();
  await expect
    .poll(() => submissions)
    .toEqual([
      {
        decision: "rejected",
        reason_code: "evidence_mismatch",
        reason_detail: "Independent evidence assessment",
      },
    ]);
});
