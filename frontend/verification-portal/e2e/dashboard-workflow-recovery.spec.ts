import { expect, test } from "@playwright/test";

test("first workflow survives reload without creating another draft", async ({
  page,
  baseURL,
}) => {
  let creations = 0;
  const workflow = {
    id: "wfl_existing",
    project_id: "prj_sandbox",
    name: "Existing sandbox workflow",
    description: "Synthetic",
    status: "draft",
    steps: ["consent", "document", "decision"],
    settings: {},
    source_template_id: "tpl_existing",
    source_template_version: "1.0",
    created: false,
  };
  await page.route("https://api.example.test/**", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const headers = {
      "Access-Control-Allow-Origin": baseURL!,
      "Access-Control-Allow-Credentials": "true",
      "Access-Control-Allow-Headers":
        "Authorization, Content-Type, X-Request-Id, X-IdentityCore-Session-Scope",
      "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    };
    if (request.method() === "OPTIONS")
      return route.fulfill({ status: 204, headers });
    if (url.pathname === "/api/graphql")
      return route.fulfill({
        headers,
        json: { data: { organizationOnboarding: { currentStep: "active" } } },
      });
    let data: unknown = {};
    if (url.pathname.endsWith("/auth/refresh"))
      data = { tokens: { access: "synthetic-access" } };
    else if (url.pathname.endsWith("/auth/me"))
      data = { user: { email: "synthetic@example.test" } };
    else if (url.pathname === "/api/v1/projects/")
      data = {
        results: [
          {
            id: "prj_sandbox",
            name: "Sandbox",
            environment: "sandbox",
            status: "active",
            is_default: true,
          },
        ],
      };
    else if (url.pathname === "/api/v1/workflow-templates/")
      data = { results: [] };
    else if (url.pathname === "/api/v1/workflows/") {
      expect(url.searchParams.get("project_id")).toBe("prj_sandbox");
      data = { results: [workflow] };
    } else if (url.pathname.endsWith("/workflows:instantiate")) creations++;
    await route.fulfill({ headers, json: { success: true, data } });
  });
  await page.goto("/onboarding/first-workflow");
  await expect(
    page.getByRole("heading", { name: "Your first workflow is ready." }),
  ).toBeVisible();
  await expect(page.getByText(workflow.name, { exact: true })).toBeVisible();
  await page.reload();
  await expect(page.getByText(workflow.name, { exact: true })).toBeVisible();
  await expect(
    page.getByRole("link", { name: "Configure workflow in dashboard" }),
  ).toHaveAttribute("href", "/workflows/wfl_existing");
  await expect(
    page.getByRole("button", { name: "Create sandbox workflow" }),
  ).toHaveCount(0);
  expect(creations).toBe(0);
});
