import { expect, test, type Route } from "@playwright/test";

import {
  direction,
  formatDate,
  formatNumber,
  resolveLocale,
  translate,
} from "../src/lib/i18n";

const sessionId = "ses_localized_test";
const verificationId = "ver_localized_test";

test("locale negotiation, formatting, RTL, and fallback are deterministic", async () => {
  expect(resolveLocale("ar-EG;q=0.9,en;q=0.8")).toBe("ar");
  expect(resolveLocale("fr-CA, ar;q=0.7")).toBe("ar");
  expect(resolveLocale("fr-CA")).toBe("en");
  expect(direction(resolveLocale("ar"))).toBe("rtl");
  expect(formatNumber("ar", 1234.5)).not.toBe(
    formatNumber("en", 1234.5),
  );
  expect(formatDate("ar", "2026-09-27")).not.toBe(
    formatDate("en", "2026-09-27"),
  );
  expect(translate("fr", "consentTitle")).toBe(
    translate("en", "consentTitle"),
  );
});

test("applicant language selection fetches matching consent and records its locale", async ({
  isMobile,
  page,
}) => {
  let consentPayload: Record<string, unknown> | null = null;

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
      const locale = request.headers()["accept-language"]?.toLowerCase().startsWith("ar")
        ? "ar"
        : "en";
      const isArabic = locale === "ar";
      return json(route, {
        session_id: sessionId,
        verification_id: verificationId,
        status: "active",
        organization: { name: "Example Bank", logo_url: "" },
        purpose: "Customer onboarding",
        required_steps: ["consent"],
        workflow: { steps: ["consent"], liveness_mode: "passive" },
        locale,
        supported_locales: ["en", "ar"],
        direction: isArabic ? "rtl" : "ltr",
        consent: {
          template_id: "ctm_localized",
          version: 4,
          locale,
          content: isArabic
            ? "أوافق على معالجة بيانات التحقق."
            : "I consent to identity verification processing.",
          content_hash: (isArabic ? "b" : "a").repeat(64),
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
      path === `/api/verification/sessions/${sessionId}/consent` &&
      method === "POST"
    ) {
      consentPayload = request.postDataJSON() as Record<string, unknown>;
      return json(route, { next_step: "completed" });
    }
    return route.abort("failed");
  });

  await page.goto(`/verify/${sessionId}#token=browser-secret`);
  if (!isMobile) {
    await page
      .getByRole("button", { name: "Continue on this computer" })
      .click();
  }

  await page.locator("#applicant-language").selectOption("ar");
  await expect(page.locator("html")).toHaveAttribute("lang", "ar");
  await expect(page.locator("html")).toHaveAttribute("dir", "rtl");
  await expect(
    page.getByRole("heading", { name: "راجع الموافقة وقدّمها" }),
  ).toBeVisible();
  await expect(page.getByText("أوافق على معالجة بيانات التحقق.")).toBeVisible();

  await page.getByRole("checkbox").check();
  await page.getByRole("button", { name: "الموافقة والمتابعة" }).click();
  await expect.poll(() => consentPayload).not.toBeNull();
  const submittedConsent = consentPayload as unknown as Record<string, unknown>;
  expect(submittedConsent.locale).toBe("ar");
  expect(submittedConsent.version).toBe(4);
});

function json(route: Route, data: unknown, status = 200) {
  return route.fulfill({
    status,
    contentType: "application/json",
    body: JSON.stringify({ success: true, data }),
  });
}
