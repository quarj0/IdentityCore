import { expect, test } from "@playwright/test";

const sessionId = "ses_withdrawal";

test("BFF admits only the exact authenticated withdrawal route", async ({
  request,
}) => {
  const headers = {
    Cookie: `__Host-identitycore_verify=opaque; __Host-identitycore_verify_id=${sessionId}`,
  };
  // The test upstream is deliberately unavailable. Reaching it proves the
  // authenticated route passed the real server-side allowlist.
  const allowed = await request.post(
    `/api/verification/sessions/${sessionId}/consent/withdraw`,
    { headers },
  );
  expect(allowed.status()).toBe(502);
  for (const suffix of ["withdraw/extra", "delete"]) {
    const rejected = await request.post(
      `/api/verification/sessions/${sessionId}/consent/${suffix}`,
      { headers },
    );
    expect(rejected.status()).toBe(404);
  }
  expect(
    (
      await request.post("/api/verification/sessions/other/consent/withdraw", {
        headers,
      })
    ).status(),
  ).toBe(403);
  expect(
    (
      await request.post(
        `/api/verification/sessions/${sessionId}/consent/withdraw`,
        { headers: { ...headers, Origin: "https://attacker.example" } },
      )
    ).status(),
  ).toBe(403);
});

for (const locale of ["en", "ar"]) {
  for (const afterConsent of ["processing", "cancelled", "consent_key_unavailable"]) {
    test(`subject withdraws consent with confirmation and retry (${locale}, ${afterConsent})`, async ({
      page,
      isMobile,
    }) => {
      let step = "consent";
      let accepted = false;
      let withdrawals = 0;
      let statusRequests = 0;
      let cleared = 0;
      await page.route("**/api/verification/**", async (route) => {
        const req = route.request();
        const path = new URL(req.url()).pathname;
        const json = (data: unknown, status = 200) =>
          route.fulfill({
            status,
            contentType: "application/json",
            body: JSON.stringify({ success: true, data }),
          });
        if (path.endsWith("/session")) {
          if (req.method() === "DELETE") cleared++;
          return json({});
        }
        if (path.endsWith("/consent/withdraw")) {
          withdrawals++;
          if (withdrawals === 1)
            return route.fulfill({
              status: 503,
              contentType: "application/json",
              body: JSON.stringify({
                success: false,
                error: { message: "Please retry withdrawal." },
              }),
            });
          return json({
            consent_record_id: "con_1",
            withdrawn_at: new Date().toISOString(),
          });
        }
        if (path.endsWith("/consent")) {
          accepted = true;
          step = afterConsent === "consent_key_unavailable" ? "consent" : afterConsent;
          return json({});
        }
        if (path.endsWith("/status")) {
          statusRequests++;
          return json({
            verification_id: "ver_withdrawal",
            status: "in_progress",
            current_step: step,
            withdrawal_available: accepted,
            message: "Processing",
            evidence: {},
          });
        }
        return json({
          session_id: sessionId,
          verification_id: "ver_withdrawal",
          status: "active",
          organization: { name: "Example Bank", logo_url: "" },
          purpose: "Customer onboarding",
          redirect_url: "",
          required_steps: ["consent"],
          workflow: { steps: ["consent"], liveness_mode: "passive" },
          locale,
          supported_locales: [locale],
          direction: locale === "ar" ? "rtl" : "ltr",
          consent: {
            template_id: "ctm_1",
            version: 1,
            locale,
            content: "I consent to verification.",
            content_hash: "a".repeat(64),
          },
          document: {
            country_code: "GH",
            document_type: "passport",
            label: "Passport",
            capture_requirements: [
              { side: "front", label: "Front", required: true },
            ],
          },
          expires_at: new Date(Date.now() + 60000).toISOString(),
        });
      });
      await page.goto(`/verify/${sessionId}#token=browser-secret`);
      if (!isMobile)
        await page
          .getByRole("button", {
            name:
              locale === "ar"
                ? "المتابعة على هذا الكمبيوتر"
                : "Continue on this computer",
          })
          .click();
      const withdraw = locale === "ar" ? "سحب الموافقة" : "Withdraw consent";
      const confirm =
        locale === "ar" ? "تأكيد سحب الموافقة" : "Confirm withdrawal";
      const keep = locale === "ar" ? "الإبقاء على الموافقة" : "Keep consent";
      await expect(
        page.getByRole("button", { name: withdraw, exact: true }),
      ).toHaveCount(0);
      await page.getByRole("checkbox").check();
      await page
        .getByRole("button", {
          name: locale === "ar" ? "الموافقة والمتابعة" : "Accept and continue",
        })
        .click();
      await page.getByRole("button", { name: withdraw, exact: true }).click();
      await page.getByRole("button", { name: keep }).click();
      expect(withdrawals).toBe(0);
      await page.getByRole("button", { name: withdraw, exact: true }).click();
      await page.getByRole("button", { name: confirm }).click();
      await expect(
        page.getByRole("alert").filter({ hasText: "Please retry withdrawal." }),
      ).toContainText("Please retry withdrawal.");
      expect(cleared).toBe(0);
      await page.getByRole("button", { name: confirm }).click();
      await expect(
        page.getByRole("heading", {
          name: locale === "ar" ? "تم سحب الموافقة" : "Consent withdrawn",
        }),
      ).toBeVisible();
      await expect.poll(() => cleared).toBe(1);
      const stoppedAt = statusRequests;
      await page.waitForTimeout(4000);
      expect(statusRequests).toBe(stoppedAt);
      expect(withdrawals).toBe(2);
      await expect(page.getByRole("button", { name: confirm })).toHaveCount(0);
      expect(await page.evaluate(() => window.location.hash)).toBe("");
    });
  }
}
