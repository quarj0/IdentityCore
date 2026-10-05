import { expect, test } from "@playwright/test";

test("queue shows overdue priority and assigns the next case", async ({
  page,
  baseURL,
}) => {
  let assigned = false;
  const queries: string[] = [];
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
        user: { email: "reviewer@example.test", full_name: "Reviewer" },
      };
    else if (url.pathname.includes("/projects")) data = { results: [] };
    else if (url.pathname.includes("/organization/me"))
      data = { status: "active" };
    else if (url.pathname.endsWith("/review-queues"))
      data = {
        queues: [
          {
            queue_id: "rvq_test",
            name: "Priority documents",
            environment: "sandbox",
            priority: 10,
            sla_minutes: 60,
            country_codes: [],
            required_skills: ["document"],
            active: true,
          },
        ],
      };
    else if (url.pathname.endsWith("/review-queues/rvq_test/cases")) {
      const entry = {
        verification_id: "ver_queue",
        queue_id: "rvq_test",
        priority: 10,
        due_at: "2026-01-01T00:00:00Z",
        overdue: true,
        country_code: "GH",
        required_skills: ["document"],
        assigned_reviewer_id: assigned ? "usr_review" : null,
      };
      if (request.method() === "POST") {
        assigned = true;
        data = { assignment: { ...entry, assigned_reviewer_id: "usr_review" } };
      } else {
        queries.push(url.search);
        data = { results: [entry], pagination: {} };
      }
    } else if (url.pathname.endsWith("/manual-reviews"))
      data = { results: [], pagination: {} };
    await route.fulfill({
      status: 200,
      headers,
      json: { success: true, data },
    });
  });
  await page.goto("/manual-review");
  await page
    .getByLabel("Review queue", { exact: true })
    .selectOption("rvq_test");
  await expect(page.getByRole("link", { name: /ver_queue/ })).toContainText(
    "Overdue",
  );
  await page.getByLabel("Queue country").fill("GH");
  await page.getByLabel("Queue skill").fill("document");
  await page.getByLabel("Overdue only").check();
  await expect
    .poll(() =>
      queries.some(
        (query) =>
          query.includes("country=GH") &&
          query.includes("skill=document") &&
          query.includes("overdue=true"),
      ),
    )
    .toBe(true);
  await page.getByRole("button", { name: "Assign next case" }).click();
  await expect(page.getByRole("status")).toHaveText(
    "Assigned ver_queue to usr_review.",
  );
  await expect(page.getByRole("link", { name: /ver_queue/ })).toContainText(
    "usr_review",
  );
});
