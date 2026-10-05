import { expect, test } from "@playwright/test";

test("independent quality disagreement preserves the applicant result", async ({
  page,
  baseURL,
}) => {
  const submissions: Record<string, unknown>[] = [];
  await page.route("https://api.example.test/**", async (route) => {
    const request = route.request(),
      url = new URL(request.url());
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
    if (url.pathname.endsWith("/auth/refresh"))
      data = { tokens: { access: "synthetic-access" } };
    else if (url.pathname.endsWith("/auth/me"))
      data = {
        user: { email: "qa@example.test", full_name: "Independent Reviewer" },
      };
    else if (url.pathname.includes("/projects")) data = { results: [] };
    else if (url.pathname.includes("/organization/me"))
      data = { status: "active" };
    else if (url.pathname.endsWith("/review-queues")) data = { queues: [] };
    else if (url.pathname.endsWith("/review-quality"))
      data = {
        results: submissions.length
          ? []
          : [
              {
                id: "rqa_test",
                verification_id: "ver_original",
                original_outcome: "verified",
                original_reason_codes: ["evidence_confirmed"],
                reviewer_id: "usr_qa",
                outcome: null,
                reason_code: null,
                completed_at: null,
                agrees: null,
                can_review: true,
                reason_rules: {
                  outcomes: {
                    verified: {
                      codes: ["evidence_confirmed"],
                      notes_required: false,
                    },
                    rejected: {
                      codes: ["evidence_mismatch"],
                      notes_required: true,
                    },
                    failed: {
                      codes: ["evidence_unavailable"],
                      notes_required: true,
                    },
                  },
                },
              },
            ],
        pagination: {},
      };
    else if (url.pathname.endsWith("/review-quality/report"))
      data = {
        completed: submissions.length,
        agreements: 0,
        disagreements: submissions.length,
        pending: submissions.length ? 0 : 1,
      };
    else if (url.pathname.endsWith("/review-quality/rqa_test")) {
      submissions.push(request.postDataJSON());
      data = { outcome: "rejected", agrees: false };
    } else if (url.pathname.endsWith("/manual-reviews"))
      data = { results: [], pagination: {} };
    await route.fulfill({
      status: 200,
      headers,
      json: { success: true, data },
    });
  });
  await page.goto("/manual-review");
  await expect(
    page.getByText("ver_original · original outcome: verified"),
  ).toBeVisible();
  await page.getByRole("button", { name: "Assess quality" }).click();
  await page.getByLabel("Quality outcome").selectOption("rejected");
  await page.getByLabel("Quality reason").selectOption("evidence_mismatch");
  await page
    .getByLabel("Quality notes")
    .fill("Independent evidence assessment");
  await page.getByRole("button", { name: "Record quality outcome" }).click();
  await expect(page.getByRole("status")).toHaveText(
    "Quality outcome recorded. The applicant's result is unchanged.",
  );
  expect(submissions).toEqual([
    {
      outcome: "rejected",
      reason_code: "evidence_mismatch",
      notes: "Independent evidence assessment",
    },
  ]);
  await expect(
    page.getByText("1 completed · 0 agreements · 1 disagreements · 0 pending"),
  ).toBeVisible();
  await expect(page.getByLabel("Quality notes")).toHaveCount(0);
});
