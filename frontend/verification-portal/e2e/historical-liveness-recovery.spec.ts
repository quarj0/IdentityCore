import { expect, test } from "@playwright/test";

for (const mode of ["passive", "active"] as const) {
  test(`${mode} liveness instructions match the capture and allow challenge replacement`, async ({
    page,
    isMobile,
  }) => {
    test.setTimeout(90_000);
    const sessionId = `ses_historical_${mode}`;
    let issued = 0;
    let submitted: unknown;
    await page.route("**/api/verification/**", async (route) => {
      const path = new URL(route.request().url()).pathname;
      const reply = (data: unknown) =>
        route.fulfill({
          contentType: "application/json",
          body: JSON.stringify({ success: true, data }),
        });
      if (path === "/api/verification/session") return reply({});
      if (path.endsWith("/liveness/challenge")) {
        issued += 1;
        return reply({
          challenge_id: `lch_${issued}`,
          actions: ["turn_left", "look_up"],
          expires_at: new Date(
            Date.now() + (issued === 1 ? 8000 : 60_000),
          ).toISOString(),
        });
      }
      if (path.endsWith("/liveness")) {
        submitted = route.request().postDataJSON();
        return reply({ liveness_check_id: "liv_test", status: "processing" });
      }
      if (path.endsWith("/status"))
        return reply({
          verification_id: "ver_test",
          status: "processing",
          current_step: "liveness_check",
          message: "Continue",
          evidence: {
            identity_document_id: "doc_test",
            selfie_capture_id: "sel_test",
            liveness_check_id: "",
          },
        });
      if (path === `/api/verification/sessions/${sessionId}`)
        return reply({
          session_id: sessionId,
          verification_id: "ver_test",
          status: "active",
          organization: { name: "Example Bank", logo_url: "" },
          purpose: "Identity verification",
          required_steps: [
            "consent",
            "document_capture",
            "selfie_capture",
            "liveness_check",
          ],
          workflow: {
            steps: [
              "consent",
              "document_capture",
              "selfie_capture",
              "liveness_check",
            ],
            liveness_mode: mode,
          },
          locale: "en",
          supported_locales: ["en"],
          direction: "ltr",
          consent: {
            template_id: "ctm_test",
            version: 1,
            locale: "en",
            content: "Notice",
            content_hash: "a".repeat(64),
          },
          document: {
            country_code: "GH",
            document_type: "passport",
            label: "Passport",
            capture_requirements: [
              { side: "single", label: "Photo page", required: true },
            ],
          },
          expires_at: "2099-01-01T00:00:00Z",
        });
      return route.abort("failed");
    });
    await page.goto(`/verify/${sessionId}#token=synthetic-token`);
    if (!isMobile)
      await page
        .getByRole("button", { name: "Continue on this computer" })
        .click();
    const activePromise = page.getByText(
      "Your challenge is single-use, randomized, and recorded directly from this device in one short video.",
    );
    if (mode === "passive") {
      await expect(activePromise).toHaveCount(0);
      await expect(
        page.getByRole("button", { name: "Begin live camera check" }),
      ).toHaveCount(0);
      await page.getByRole("button", { name: "Submit presence check" }).click();
      await expect
        .poll(() => submitted)
        .toEqual({ selfie_capture_id: "sel_test", liveness_type: "passive" });
      expect(issued).toBe(0);
    } else {
      await expect(activePromise).toBeVisible();
      await page
        .getByRole("button", { name: "Begin live camera check" })
        .click();
      await expect(
        page.getByRole("button", { name: "Start a new live challenge" }),
      ).toBeVisible();
      await expect(
        page.getByText(
          "Your live challenge expired. Begin a new live camera check.",
        ),
      ).toBeVisible({ timeout: 15_000 });
      await page
        .getByRole("button", { name: "Begin live camera check" })
        .click();
      await page
        .getByRole("button", { name: "Start a new live challenge" })
        .click();
      await page
        .getByRole("button", { name: "Begin live camera check" })
        .click();
      await expect(
        page.getByRole("button", { name: "Enable camera" }),
      ).toBeVisible();
      expect(issued).toBe(3);
    }
  });
}
