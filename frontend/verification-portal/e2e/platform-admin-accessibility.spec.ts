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
  organizationVerificationReviewStatus: "pending",
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
