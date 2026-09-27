import { expect, test, type Route } from "@playwright/test";

const sessionId = "ses_handoff_test";
const verificationId = "ver_handoff_test";

test("desktop handoff recovers from a temporary error and displays a one-time QR", async ({
  isMobile,
  page,
}) => {
  test.skip(isMobile, "QR creation is a desktop-origin handoff journey");

  let createAttempts = 0;
  await page.route("**/api/verification/**", async (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    const method = request.method();

    if (path === "/api/verification/session" && method === "POST") {
      return json(route, {});
    }
    if (
      path === `/api/verification/sessions/${sessionId}` &&
      method === "GET"
    ) {
      return json(route, {
        session_id: sessionId,
        verification_id: verificationId,
        status: "active",
        organization: { name: "Example Bank", logo_url: "" },
        purpose: "Customer onboarding",
        required_steps: ["consent", "document_capture"],
        workflow: { steps: ["consent", "document_capture"], liveness_mode: "passive" },
        locale: "en",
        supported_locales: ["en"],
        direction: "ltr",
        consent: {
          template_id: "ctm_test",
          version: 1,
          locale: "en",
          content: "Consent text",
          content_hash: "a".repeat(64),
        },
        document: {
          country_code: "GH",
          document_type: "national_id",
          label: "National ID",
          capture_requirements: [
            { side: "front", label: "Front", required: true },
          ],
        },
        expires_at: new Date(Date.now() + 60_000).toISOString(),
      });
    }
    if (
      path === `/api/verification/sessions/${sessionId}/status` &&
      method === "GET"
    ) {
      return json(route, {
        verification_id: verificationId,
        status: "in_progress",
        current_step: "consent",
        message: "Continue your verification.",
        evidence: {
          identity_document_id: "",
          selfie_capture_id: "",
          liveness_check_id: "",
        },
      });
    }
    if (
      path === `/api/verification/sessions/${sessionId}/mobile-handoff` &&
      method === "POST"
    ) {
      createAttempts += 1;
      if (createAttempts === 1) {
        return route.fulfill({
          status: 503,
          contentType: "application/json",
          body: JSON.stringify({
            success: false,
            error: {
              code: "temporarily_unavailable",
              message: "The handoff service is temporarily unavailable.",
            },
            request_id: "req_handoff_retry",
          }),
        });
      }
      return json(route, {
        handoff_url: `https://verify.example/verify/${sessionId}#handoff=one-time-code`,
        expires_at: new Date(Date.now() + 60_000).toISOString(),
      });
    }
    return route.abort("failed");
  });

  await page.goto(`/verify/${sessionId}#token=browser-secret`);
  await expect(
    page.getByRole("heading", { name: "Continue securely on your phone" }),
  ).toBeVisible();

  await page.getByRole("button", { name: "Show secure QR code" }).click();
  await expect(page.getByRole("alert")).toContainText(
    "The handoff service is temporarily unavailable.",
  );
  await page.getByRole("button", { name: "Show secure QR code" }).click();

  await expect(page.getByText("Scan with your phone camera")).toBeVisible();
  await expect(page.getByText("The one-time code expires shortly")).toBeVisible();
  await expect(page.locator("svg")).toBeVisible();
  expect(createAttempts).toBe(2);
});

function json(route: Route, data: unknown, status = 200) {
  return route.fulfill({
    status,
    contentType: "application/json",
    body: JSON.stringify({ success: true, data }),
  });
}
