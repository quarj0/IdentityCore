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
  await page.route("http://localhost:8000/**", async (route: Route) => {
    const request = route.request();
    if (new URL(request.url()).pathname.endsWith("/api/graphql")) {
      const payload = request.postDataJSON() as { query?: string };
      const query = payload.query ?? "";
      if (query.includes("mutation ReviewOrganization")) {
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            data: {
              reviewOrganizationOnboarding: {
                nextAction: "approved",
                onboarding: {
                  ...reviewItem,
                  organizationVerificationReviewStatus: "approved",
                },
              },
            },
          }),
        });
      }
      if (query.includes("OrganizationReviewQueue")) {
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            data: { organizationReviewQueue: [reviewItem] },
          }),
        });
      }
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ data: { organizationReview: reviewItem } }),
      });
    }

    return route.fulfill({
      status: 200,
      contentType: "application/json",
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
  });
}

test("review queue and decision flow are WCAG-clean and keyboard operable", async ({
  page,
}) => {
  await mockAdminBackend(page);
  await page.goto("/review");
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
});
