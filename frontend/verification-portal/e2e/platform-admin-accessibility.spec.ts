import { csvCell } from "../../platform-admin/src/lib/export-csv";
import { createRequire } from "node:module";
import { expect, test, type Page, type Route } from "@playwright/test";

const require = createRequire(import.meta.url);
const organizationId = "org_a11y_review";

const reviewItem = {
  organizationId,
  organizationName: "Accessible Organization",
  organizationSlug: "accessible-org",
  organizationType: "company",
  organizationCountry: "GH",
  organizationCountryName: "Ghana",
  organizationStatus: "pending_review",
  tenantStatus: "active",
  administratorFullName: "Ada Reviewer",
  administratorEmail: "ada@example.test",
  supportEmail: "support@example.test",
  website: "https://example.test",
  onboardingStatus: "review",
  currentStep: "organization_verification",
  organizationVerificationSubmittedAt: "2026-08-22T12:00:00Z",
  organizationVerificationEditable: false,
  organizationVerificationReviewStatus: "submitted",
  organizationVerificationChangedAfterApproval: false,
  organizationVerificationReviewedAt: null,
  organizationVerificationReviewNote: "",
  platformReviewStatus: "pending",
  platformReviewNote: "",
  platformReviewedAt: null,
  businessRegistrationNumber: "REG-123",
  taxIdentificationNumber: "TIN-456",
  registeredAddress: "1 Accessible Street, Accra",
  officialWebsite: "https://example.test",
  reviewPriority: "high",
  reviewSummary: "Manual review required for submitted organization evidence.",
  supportingDocuments: [],
};

async function assertNoSeriousViolations(page: Page) {
  await page.addScriptTag({ path: require.resolve("axe-core/axe.min.js") });
  const violations = await page.evaluate(async () => {
    const axe = (
      window as unknown as {
        axe: {
          run: (
            context?: unknown,
            options?: unknown,
          ) => Promise<{
            violations: Array<{
              id: string;
              impact: string | null;
              nodes: unknown[];
            }>;
          }>;
        };
      }
    ).axe;
    const result = await axe.run(document, {
      runOnly: {
        type: "tag",
        values: ["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"],
      },
    });
    return result.violations.filter(
      (violation) =>
        violation.impact === "serious" || violation.impact === "critical",
    );
  });
  expect(violations).toEqual([]);
}

async function mockAdminBackend(page: Page) {
  let currentReviewItem = { ...reviewItem };

  const handler = async (route: Route) => {
    const request = route.request();
    const corsHeaders = {
      "Access-Control-Allow-Credentials": "true",
      "Access-Control-Allow-Headers":
        "Authorization, Content-Type, X-IdentityCore-Session-Scope",
      "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
      "Access-Control-Allow-Origin": "http://127.0.0.1:3004",
    };

    if (request.method() === "OPTIONS") {
      await route.fulfill({ status: 204, headers: corsHeaders });
      return;
    }

    if (new URL(request.url()).pathname.endsWith("/api/graphql")) {
      const payload = request.postDataJSON() as {
        query?: string;
        variables?: { decision?: string; note?: string };
      };
      const query = payload.query ?? "";
      if (query.includes("mutation ReviewOrganization")) {
        const decision = payload.variables?.decision ?? "approved";
        currentReviewItem = {
          ...currentReviewItem,
          organizationVerificationReviewStatus: decision,
          organizationVerificationReviewNote:
            payload.variables?.note ??
            currentReviewItem.organizationVerificationReviewNote,
        };
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          headers: corsHeaders,
          body: JSON.stringify({
            data: {
              reviewOrganizationOnboarding: {
                nextAction: decision,
                onboarding: currentReviewItem,
              },
            },
          }),
        });
        return;
      }
      if (query.includes("OrganizationReviewQueue")) {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          headers: corsHeaders,
          body: JSON.stringify({
            data: { organizationReviewQueue: [currentReviewItem] },
          }),
        });
        return;
      }
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        headers: corsHeaders,
        body: JSON.stringify({
          data: { organizationReview: currentReviewItem },
        }),
      });
      return;
    }

    await route.fulfill({
      status: 200,
      contentType: "application/json",
      headers: corsHeaders,
      body: JSON.stringify({
        success: true,
        data: {
          user: {
            email: "reviewer@example.test",
            first_name: "Review",
            last_name: "Admin",
            is_platform_admin: true,
          },
        },
        request_id: "req_accessibility",
      }),
    });
  };

  await page.route("**/api/v1/**", handler);
  await page.route("**/api/graphql", handler);
}

test("review queue and decision flow are WCAG-clean and keyboard operable", async ({
  page,
}) => {
  await mockAdminBackend(page);
  const currentUserResponse = page.waitForResponse((response) =>
    response.url().includes("/api/v1/auth/me"),
  );
  await page.goto("/review");
  await expect((await currentUserResponse).status()).toBe(200);
  await expect(page).toHaveURL(/\/review$/);
  await expect(
    page.getByRole("heading", { name: /organization review/i }),
  ).toBeVisible();
  await assertNoSeriousViolations(page);

  const reviewLink = page
    .getByRole("link", { name: /accessible organization/i })
    .first();
  await reviewLink.focus();
  await expect(reviewLink).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page).toHaveURL(new RegExp(`/review/${organizationId}$`));

  await expect(
    page.getByRole("heading", { name: "Accessible Organization" }),
  ).toBeVisible();
  await assertNoSeriousViolations(page);

  const note = page.getByRole("textbox", { name: "Review note" });
  await note.focus();
  await expect(note).toBeFocused();
  await page.keyboard.type("Evidence checked with keyboard-only navigation.");

  const approve = page.getByRole("button", { name: "Approve" });
  await approve.focus();
  await expect(approve).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page.getByText(/approved/i).first()).toBeVisible();
  await expect(approve).toBeDisabled();
  await expect(
    page.getByRole("button", { name: "Reject", exact: true }),
  ).toBeDisabled();
  await assertNoSeriousViolations(page);
});

const lifecycleTemplate = {
  id: "tpl_lifecycle",
  name: "Customer KYC",
  description: "Synthetic template",
  category: "banking_kyc",
  status: "published",
  version: "1.0",
  countries: ["GH"],
  requiredChecks: ["document"],
  usageCount: 0,
  clonedByOrganizations: 0,
  ownerTeam: "Platform",
  riskLevel: "standard",
  createdById: "usr_admin",
  createdByEmail: "admin@example.test",
  createdAt: "2026-10-15T00:00:00Z",
  updatedAt: "2026-10-15T00:00:00Z",
};

async function mockTemplateLifecycle(page: Page, status: string) {
  await mockAdminBackend(page);
  let created = false;
  await page.route("**/api/graphql", async (route) => {
    const payload = route.request().postDataJSON();
    const headers = {
      "Access-Control-Allow-Origin": "http://127.0.0.1:3004",
      "Access-Control-Allow-Credentials": "true",
    };
    if (payload.query.includes("mutation CreateTemplateVersion")) {
      expect(payload.variables).toEqual({
        templateId: "tpl_lifecycle",
        version: "1.1",
      });
      created = true;
      await route.fulfill({
        json: {
          data: {
            template: {
              ...lifecycleTemplate,
              id: "tpl_lifecycle_v11",
              version: "1.1",
              status: "draft",
            },
          },
        },
        headers,
      });
    } else {
      const template = created
        ? {
            ...lifecycleTemplate,
            id: "tpl_lifecycle_v11",
            version: "1.1",
            status: "draft",
          }
        : { ...lifecycleTemplate, status };
      await route.fulfill({
        json: {
          data: { platformTemplate: template, platformTemplates: [template] },
        },
        headers,
      });
    }
  });
}

test("workflow author can create steps, edit their order and publish the draft", async ({
  page,
}) => {
  await mockAdminBackend(page);
  let workflow = {
    ...lifecycleTemplate,
    id: "wfl_authored",
    name: "Authored workflow",
    status: "draft",
    projectName: "Synthetic project",
    currentVersion: 0,
    steps: ["consent", "document", "decision"],
    settings: {},
  };
  let created = false;
  let published = false;
  await page.route("**/api/graphql", async (route) => {
    const payload = route.request().postDataJSON();
    const headers = {
      "Access-Control-Allow-Origin": "http://127.0.0.1:3004",
      "Access-Control-Allow-Credentials": "true",
    };
    if (payload.query.includes("mutation CreateWorkflow")) {
      expect(payload.query).toContain("steps: $steps");
      expect(payload.variables.steps).toEqual([
        "consent",
        "document",
        "selfie",
        "liveness",
        "decision",
      ]);
      expect(payload.variables.tenantId).toBe("ten_synthetic");
      expect(payload.variables.projectId).toBe("prj_synthetic");
      workflow = { ...workflow, ...payload.variables };
      created = true;
      await route.fulfill({ headers, json: { data: { workflow } } });
    } else if (payload.query.includes("mutation UpdateWorkflow")) {
      expect(payload.query).toContain("steps: $steps");
      expect(payload.variables.steps).toEqual([
        "consent",
        "selfie",
        "document",
        "liveness",
        "decision",
      ]);
      workflow = { ...workflow, ...payload.variables };
      await route.fulfill({ headers, json: { data: { workflow } } });
    } else if (payload.query.includes("mutation PublishWorkflow")) {
      expect(payload.variables.workflowId).toBe(workflow.id);
      published = true;
      workflow = { ...workflow, status: "published", currentVersion: 1 };
      await route.fulfill({
        headers,
        json: {
          data: { publishPlatformWorkflow: { id: "wfv_authored", version: 1 } },
        },
      });
    } else {
      await route.fulfill({
        headers,
        json: {
          data: {
            platformWorkflows: created ? [workflow] : [],
            platformWorkflow: workflow,
            platformWorkflowVersions: [],
          },
        },
      });
    }
  });
  await page.goto("/workflows");
  await page
    .getByRole("button", { name: "Create workflow", exact: true })
    .click();
  await page.getByLabel("Tenant ID", { exact: true }).fill("ten_synthetic");
  await page.getByLabel("Project ID", { exact: true }).fill("prj_synthetic");
  await page
    .getByLabel("Workflow name", { exact: true })
    .fill("Authored workflow");
  await page.getByRole("button", { name: "Add Selfie", exact: true }).click();
  await page.getByRole("button", { name: "Add Liveness", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "Remove Consent", exact: true }),
  ).toBeDisabled();
  await page.getByRole("button", { name: "Create draft", exact: true }).click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await page
    .getByRole("link", { name: "Authored workflow", exact: true })
    .click();
  await page.getByRole("button", { name: "Edit draft", exact: true }).click();
  await page
    .getByRole("button", { name: "Move Selfie up", exact: true })
    .click();
  await assertNoSeriousViolations(page);
  await page.getByRole("button", { name: "Save draft", exact: true }).click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
  await page.getByRole("button", { name: "Publish", exact: true }).click();
  await page
    .getByLabel("Release notes", { exact: true })
    .fill("Reviewed ordered verification steps.");
  await page
    .getByRole("button", { name: "Publish workflow", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Archive", exact: true }),
  ).toBeVisible();
  expect(created).toBe(true);
  expect(published).toBe(true);
});

for (const status of ["draft", "published", "archived"]) {
  test(`template ${status} exposes only valid lifecycle actions`, async ({
    page,
  }) => {
    await mockTemplateLifecycle(page, status);
    await page.goto("/templates/tpl_lifecycle");
    await expect(
      page.getByRole("heading", { name: "Customer KYC" }),
    ).toBeVisible();
    await expect(
      page.getByRole("button", { name: "Edit draft", exact: true }),
    ).toHaveCount(status === "draft" ? 1 : 0);
    await expect(
      page.getByRole("button", { name: "New version", exact: true }),
    ).toHaveCount(status === "published" ? 1 : 0);
    await expect(
      page.getByRole("button", { name: "Publish", exact: true }),
    ).toHaveCount(status === "draft" ? 1 : 0);
  });
}

test("published template creates and opens an editable later version", async ({
  page,
}) => {
  await mockTemplateLifecycle(page, "published");
  await page.goto("/templates/tpl_lifecycle");
  await page.getByRole("button", { name: "New version", exact: true }).click();
  await page.getByLabel("New version", { exact: true }).fill("1.1");
  await page
    .getByRole("button", { name: "Create version", exact: true })
    .click();
  await expect(page).toHaveURL(/\/templates\/tpl_lifecycle_v11$/);
  await expect(
    page.getByRole("button", { name: "Edit draft", exact: true }),
  ).toBeVisible();
});

test("template creation submits publishable checks and closes after success", async ({
  page,
}) => {
  await mockAdminBackend(page);
  let creation: Record<string, unknown> | undefined;
  await page.route("**/api/graphql", async (route) => {
    const payload = route.request().postDataJSON();
    const headers = {
      "Access-Control-Allow-Origin": "http://127.0.0.1:3004",
      "Access-Control-Allow-Credentials": "true",
    };
    if (payload.query.includes("mutation CreatePlatformTemplate")) {
      creation = payload.variables;
      await route.fulfill({
        json: {
          data: {
            createPlatformTemplate: { ...lifecycleTemplate, status: "draft" },
          },
        },
        headers,
      });
    } else
      await route.fulfill({
        json: {
          data: {
            platformTemplates: [{ ...lifecycleTemplate, status: "draft" }],
          },
        },
        headers,
      });
  });
  await page.goto("/templates");
  await page
    .getByRole("button", { name: "Create template", exact: true })
    .click();
  await page
    .getByLabel("Template name", { exact: true })
    .fill("Publishable draft");
  await page.getByRole("combobox").click();
  await page.getByRole("option", { name: "Banking KYC", exact: true }).click();
  await page
    .getByLabel("Description", { exact: true })
    .fill("Synthetic creation");
  await page.getByRole("button", { name: "Create draft", exact: true }).click();
  await expect.poll(() => creation).toBeTruthy();
  expect.soft(creation?.requiredChecks).toEqual(["document"]);
  expect.soft(creation?.steps).toEqual(["consent", "document", "decision"]);
  await expect(page.getByRole("dialog")).toHaveCount(0);
});

test("template description edits survive the refreshed detail response", async ({
  page,
}) => {
  await mockAdminBackend(page);
  let template = { ...lifecycleTemplate, status: "draft" };
  let submittedDescription: string | undefined;
  await page.route("**/api/graphql", async (route) => {
    const payload = route.request().postDataJSON();
    const headers = {
      "Access-Control-Allow-Origin": "http://127.0.0.1:3004",
      "Access-Control-Allow-Credentials": "true",
    };
    if (payload.query.includes("mutation UpdateTemplate")) {
      submittedDescription = payload.variables.description;
      template = {
        ...template,
        description: payload.variables.description ?? template.description,
      };
      await route.fulfill({ json: { data: { template } }, headers });
    } else
      await route.fulfill({
        json: { data: { platformTemplate: template } },
        headers,
      });
  });
  await page.goto("/templates/tpl_lifecycle");
  await page.getByRole("button", { name: "Edit draft", exact: true }).click();
  await page
    .getByLabel("Description", { exact: true })
    .fill("Updated description evidence");
  await page.getByRole("button", { name: "Save draft", exact: true }).click();
  await expect
    .poll(() => submittedDescription)
    .toBe("Updated description evidence");
  await expect(
    page.locator("p").filter({ hasText: /^Updated description evidence$/ }),
  ).toBeVisible();
});

for (const entity of ["template", "workflow"]) {
  for (const action of ["publish", "archive"]) {
    test(`${entity} ${action} submits operator rationale and closes`, async ({
      page,
    }) => {
      await mockAdminBackend(page);
      let rationale: string | undefined;
      let status = action === "publish" ? "draft" : "published";
      await page.route("**/api/graphql", async (route) => {
        const payload = route.request().postDataJSON();
        const headers = {
          "Access-Control-Allow-Origin": "http://127.0.0.1:3004",
          "Access-Control-Allow-Credentials": "true",
        };
        const template = { ...lifecycleTemplate, status };
        const workflow = {
          ...lifecycleTemplate,
          id: "wfl_notes",
          status,
          projectName: "Synthetic project",
          currentVersion: 1,
          version: 1,
          stepCount: 2,
          steps: ["consent", "decision"],
          settings: {},
        };
        if (
          payload.query.includes(
            "mutation " +
              (action === "publish" ? "Publish" : "Archive") +
              (entity === "template" ? "Template" : "Workflow"),
          )
        ) {
          rationale =
            payload.variables[action === "publish" ? "notes" : "reason"];
          status = action === "publish" ? "published" : "archived";
          await route.fulfill({
            json: {
              data:
                entity === "template"
                  ? { template: { ...template, status } }
                  : action === "publish"
                    ? {
                        publishPlatformWorkflow: {
                          id: "wfv_notes",
                          version: 1,
                        },
                      }
                    : { workflow: { ...workflow, status } },
            },
            headers,
          });
        } else
          await route.fulfill({
            json: {
              data: {
                platformTemplate: template,
                platformWorkflow: workflow,
                platformWorkflowVersions: [],
              },
            },
            headers,
          });
      });
      await page.goto(
        entity === "template"
          ? "/templates/tpl_lifecycle"
          : "/workflows/wfl_notes",
      );
      await page
        .getByRole("button", {
          name: action === "publish" ? "Publish" : "Archive",
          exact: true,
        })
        .click();
      await page
        .getByLabel(action === "publish" ? "Release notes" : "Archive reason", {
          exact: true,
        })
        .fill("Recorded operator rationale");
      await page
        .getByRole("button", {
          name: `${action === "publish" ? "Publish" : "Archive"} ${entity}`,
          exact: true,
        })
        .click();
      await expect.poll(() => rationale).toBe("Recorded operator rationale");
      await expect(page.getByRole("dialog")).toHaveCount(0);
    });
  }
}

test("platform invitation acceptance clears the fragment and continues through sign-in", async ({
  page,
}) => {
  const submissions: Record<string, unknown>[] = [];
  await page.route("**/api/graphql", async (route) => {
    const request = route.request();
    const headers = {
      "Access-Control-Allow-Origin": "http://127.0.0.1:3004",
      "Access-Control-Allow-Credentials": "true",
      "Access-Control-Allow-Headers":
        "Content-Type, X-IdentityCore-Session-Scope",
    };
    if (request.method() === "OPTIONS")
      return route.fulfill({ status: 204, headers });
    expect(request.headers().authorization).toBeUndefined();
    expect(request.headers()["x-identitycore-session-scope"]).toBe(
      "platform_admin",
    );
    submissions.push(request.postDataJSON().variables);
    return route.fulfill({
      headers,
      json: {
        data: {
          acceptPlatformAdminInvitation: {
            user: { email: "synthetic@example.test" },
            mfaRequired: true,
          },
        },
      },
    });
  });
  await page.goto("/accept-invitation#token=synthetic-invitation-token");
  await expect(page).toHaveURL(/\/accept-invitation$/);
  await page.getByLabel("New password").fill("StrongSyntheticPassword123!");
  await page
    .getByRole("button", { name: "Accept invitation", exact: true })
    .click();
  await expect(page.getByRole("status")).toContainText(
    "Your account was created",
  );
  expect(submissions).toEqual([
    {
      token: "synthetic-invitation-token",
      password: "StrongSyntheticPassword123!",
    },
  ]);
  expect(
    await page.evaluate(() =>
      JSON.stringify({ ...sessionStorage, ...localStorage }),
    ),
  ).not.toContain("synthetic-invitation-token");
  await expect(
    page.getByRole("link", { name: "Continue to sign in" }),
  ).toHaveAttribute("href", "/login");
  await assertNoSeriousViolations(page);
});

test("platform invitation UI states full privilege and queues a validated address", async ({
  page,
}) => {
  await mockAdminBackend(page);
  const submissions: Record<string, unknown>[] = [];
  await page.route("**/api/graphql", async (route) => {
    const request = route.request();
    const headers = {
      "Access-Control-Allow-Origin": "http://127.0.0.1:3004",
      "Access-Control-Allow-Credentials": "true",
      "Access-Control-Allow-Headers":
        "Content-Type, Authorization, X-IdentityCore-Session-Scope",
    };
    if (request.method() === "OPTIONS")
      return route.fulfill({ status: 204, headers });
    const body = request.postDataJSON();
    if (body.query.includes("InvitePlatformAdmin")) {
      submissions.push(body.variables);
      return route.fulfill({
        headers,
        json: {
          data: {
            invitePlatformAdmin: {
              invitation: { id: "pinv_synthetic", status: "pending" },
            },
          },
        },
      });
    }
    return route.fulfill({ headers, json: { data: { platformAdmins: [] } } });
  });
  await page.goto("/users");
  await page.getByRole("button", { name: "Invite admin", exact: true }).click();
  await expect(
    page.getByText("This invitation grants full platform administration.", {
      exact: false,
    }),
  ).toBeVisible();
  await page.getByLabel("Email address").fill("not-an-address");
  await expect(
    page.getByRole("button", { name: "Send invite" }),
  ).toBeDisabled();
  await page.getByLabel("Email address").fill("synthetic@example.test");
  await page.getByRole("button", { name: "Send invite" }).click();
  await expect(page.getByRole("status")).toContainText("Invitation queued");
  expect(submissions).toEqual([
    { email: "synthetic@example.test", roleName: "Platform Admin" },
  ]);
  await page.getByRole("button", { name: "Cancel", exact: true }).click();
  await expect(page.getByRole("dialog")).toHaveCount(0);
});

test("CSV exports neutralize formula and control prefixes", () => {
  for (const value of [
    '=HYPERLINK("https://example.test")',
    "+1+1",
    "-1+1",
    "@SUM(1)",
    "  =1+1",
    "\t=1+1",
    "\rvalue",
    "\nvalue",
  ]) {
    expect(csvCell(value).startsWith("\"'")).toBe(true);
  }
  expect(csvCell('ordinary "text"')).toBe('"ordinary ""text"""');
  expect(csvCell(null)).toBe('""');
});

test("generic admin lists retain a functional safe export of loaded results", async ({
  page,
}) => {
  await mockAdminBackend(page);
  await page.route("**/api/graphql", async (route) => {
    const headers = {
      "Access-Control-Allow-Origin": "http://127.0.0.1:3004",
      "Access-Control-Allow-Credentials": "true",
      "Access-Control-Allow-Headers":
        "Content-Type, Authorization, X-IdentityCore-Session-Scope",
    };
    if (route.request().method() === "OPTIONS")
      return route.fulfill({ status: 204, headers });
    return route.fulfill({
      headers,
      json: {
        data: {
          platformProviders: [
            {
              id: "prv_synthetic",
              name: "=SUM(1)",
              code: "synthetic",
              providerType: "document",
              status: "active",
              configuration: { configured: true },
              updatedAt: "2026-10-18T00:00:00Z",
            },
          ],
        },
      },
    });
  });
  await page.goto("/providers");
  const pending = page.waitForEvent("download");
  await page
    .getByRole("button", { name: "Export loaded results", exact: true })
    .click();
  const stream = await (await pending).createReadStream();
  const chunks: Buffer[] = [];
  for await (const chunk of stream!) chunks.push(chunk);
  expect(Buffer.concat(chunks).toString()).toContain('"\'=SUM(1)"');
});
