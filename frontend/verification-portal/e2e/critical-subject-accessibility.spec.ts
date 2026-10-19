import { expect, test, type Locator, type Route } from "@playwright/test";

import { localizeText, translate } from "../src/lib/i18n";

import { expectNoCriticalA11yViolations } from "./a11y-helpers";

const sessionId = "ses_accessibility";
const verificationId = "ver_accessibility";
const image = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=",
  "base64",
);

async function activateWithKeyboard(locator: Locator, key = "Enter") {
  if (locator.page().context().browser()?.browserType().name() === "webkit") {
    await locator.click();
    return;
  }
  await locator.focus();
  await expect(locator).toBeFocused();
  await locator.press(key);
}

async function activateForBrowser(
  locator: Locator,
  isMobile: boolean,
  key = "Enter",
) {
  if (isMobile) {
    // Exercise touch input on mobile projects; synthesized mouse clicks can
    // be swallowed by WebKit while a captured image changes page geometry.
    await locator.tap();
    return;
  }
  await activateWithKeyboard(locator, key);
}

for (const locale of ["en", "ar"] as const) {
  test(`critical subject journey ${locale} is accessible and operable by keyboard or touch`, async ({
    isMobile,
    page,
  }) => {
    test.slow();
    const t = (text: string) => {
      const result =
        text === "Accept and continue"
          ? translate(locale, "accept")
          : text === "Complete a live camera check"
            ? translate(locale, "livenessTitle")
            : localizeText(locale, text);
      if (locale === "ar") expect(result).toMatch(/[\u0600-\u06ff]/);
      return result;
    };

    let step = "consent";
    let uploadNumber = 0;

    await page.addInitScript(() => {
      class MockMediaRecorder {
        static isTypeSupported() {
          return true;
        }
        state = "inactive";
        ondataavailable: ((event: { data: Blob }) => void) | null = null;
        onstop: (() => void) | null = null;
        start() {
          this.state = "recording";
        }
        stop() {
          this.state = "inactive";
          this.ondataavailable?.({
            data: new Blob(["live-video"], { type: "video/webm" }),
          });
          this.onstop?.();
        }
      }
      Object.defineProperty(window, "MediaRecorder", {
        value: MockMediaRecorder,
      });
      Object.defineProperty(navigator, "mediaDevices", {
        value: { getUserMedia: async () => new MediaStream() },
      });
    });

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
          organization: { name: "Accessibility Bank", logo_url: "" },
          purpose: "Customer onboarding",
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
            liveness_mode: "active",
          },
          locale,
          supported_locales: ["en", "ar"],
          direction: locale === "ar" ? "rtl" : "ltr",
          consent: {
            template_id: "ctm_accessibility",
            version: 1,
            locale,
            content:
              locale === "ar"
                ? "أوافق على التحقق من الهوية لاختبار إمكانية الوصول."
                : "I consent to identity verification for accessibility testing.",
            content_hash: "a".repeat(64),
          },
          document: {
            country_code: "GH",
            document_type: "national_id",
            label: "National ID",
            capture_requirements: [
              { side: "front", label: "Front", required: true },
              { side: "back", label: "Back", required: true },
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
          status:
            step === "completed" ? "manual_review_required" : "in_progress",
          current_step: step,
          message:
            step === "completed"
              ? "Your verification was submitted and requires additional review."
              : "Continue your verification.",
          evidence: {
            identity_document_id:
              step === "consent" || step === "document_capture"
                ? ""
                : "doc_a11y",
            selfie_capture_id: ["liveness_check", "completed"].includes(step)
              ? "sel_a11y"
              : "",
            liveness_check_id: step === "completed" ? "liv_a11y" : "",
          },
        });
      }
      if (
        path === `/api/verification/sessions/${sessionId}/consent` &&
        method === "POST"
      ) {
        step = "document_capture";
        return json(route, { next_step: step });
      }
      if (path === "/api/verification/uploads/" && method === "POST") {
        uploadNumber += 1;
        return json(
          route,
          {
            upload_id: `upl_a11y_${uploadNumber}`,
            upload_url: "",
            upload_headers: {},
            upload_transfer_path: `/uploads/upl_a11y_${uploadNumber}/transfer`,
            upload_complete_path: `/uploads/upl_a11y_${uploadNumber}/complete`,
          },
          201,
        );
      }
      if (/\/api\/verification\/uploads\/upl_a11y_\d+\/transfer$/.test(path)) {
        return json(route, { upload_id: `upl_a11y_${uploadNumber}` });
      }
      if (/\/api\/verification\/uploads\/upl_a11y_\d+\/complete$/.test(path)) {
        return json(route, { upload_id: `upl_a11y_${uploadNumber}` });
      }
      if (
        path === `/api/verification/sessions/${sessionId}/documents` &&
        method === "POST"
      ) {
        step = "selfie_capture";
        return json(route, {
          identity_document_id: "doc_a11y",
          status: "processing",
          next_step: "document_processing",
        });
      }
      if (
        path === `/api/verification/sessions/${sessionId}/selfies` &&
        method === "POST"
      ) {
        step = "liveness_check";
        return json(route, {
          selfie_capture_id: "sel_a11y",
          status: "processing",
          next_step: "liveness_check",
        });
      }
      if (
        path === `/api/verification/sessions/${sessionId}/liveness/challenge` &&
        method === "POST"
      ) {
        return json(route, {
          challenge_id: "lch_a11y",
          actions: [
            "turn_left",
            "look_up",
            "turn_right",
            "look_down",
            "turn_left",
            "look_up",
            "turn_right",
            "look_down",
          ],
          expires_in: 60,
          expires_at: new Date(Date.now() + 60_000).toISOString(),
        });
      }
      if (
        path === `/api/verification/sessions/${sessionId}/liveness` &&
        method === "POST"
      ) {
        step = "completed";
        return json(route, {
          liveness_check_id: "liv_a11y",
          status: "processing",
          next_step: "processing",
        });
      }
      return route.abort("failed");
    });

    await page.goto(`/verify/${sessionId}#token=accessibility-secret`);

    if (!isMobile) {
      await expectNoCriticalA11yViolations(page);
      await activateWithKeyboard(
        page.getByRole("button", { name: t("Continue on this computer") }),
      );
    }

    await expect(
      page.getByRole("heading", { name: t("Review and give consent") }),
    ).toBeVisible();
    await expect(page.locator("html")).toHaveAttribute("lang", locale);
    await expect(page.locator("html")).toHaveAttribute("dir", locale === "ar" ? "rtl" : "ltr");
    await expect(page.getByRole("link", { name: translate(locale, "skip") })).toHaveAttribute("href", "#main-content");
    await expectNoCriticalA11yViolations(page);
    const consent = page.getByRole("checkbox");
    await activateForBrowser(consent, isMobile, "Space");
    await expect(consent).toBeChecked();
    await activateForBrowser(
      page.getByRole("button", { name: t("Accept and continue") }),
      isMobile,
    );

    await expect(
      page.getByRole("heading", {
        name: `${t("Capture your")} ${t("National ID")}`,
      }),
    ).toBeVisible();
    await expectNoCriticalA11yViolations(page);
    const upload = page.getByLabel(t("Upload image"));
    if (
      !isMobile &&
      page.context().browser()?.browserType().name() !== "webkit"
    ) {
      await upload.focus();
      await expect(upload).toBeFocused();
    }
    await upload.setInputFiles({
      name: "national-id-front.png",
      mimeType: "image/png",
      buffer: image,
    });
    await activateForBrowser(
      page.getByRole("button", { name: `${t("Back")} ${t("Not captured")}` }),
      isMobile,
    );
    await upload.setInputFiles({
      name: "national-id-back.png",
      mimeType: "image/png",
      buffer: image,
    });
    await activateForBrowser(
      page.getByRole("button", { name: t("Submit document") }),
      isMobile,
    );

    await expect(
      page.getByRole("heading", { name: t("Take a live selfie") }),
    ).toBeVisible();
    await expectNoCriticalA11yViolations(page);
    await upload.setInputFiles({
      name: "selfie.png",
      mimeType: "image/png",
      buffer: image,
    });
    await activateForBrowser(
      page.getByRole("button", { name: t("Submit selfie") }),
      isMobile,
    );

    await expect(
      page.getByRole("heading", { name: t("Complete a live camera check") }),
    ).toBeVisible();
    await expectNoCriticalA11yViolations(page);
    for (const buttonName of [
      "Begin live camera check",
      "Enable camera",
      "Start live challenge",
      "Finish recording",
      "Submit live check",
    ]) {
      // Permit automatic completion on WebKit; other browsers also exercise
      // manual stop. Both paths must produce a usable capture.
      if (
        buttonName === "Finish recording" &&
        page.context().browser()?.browserType().name() === "webkit"
      ) {
        await expect(
          page.getByText(t("Live recording ready to submit.")),
        ).toBeVisible({ timeout: 25_000 });
        continue;
      }

      const button = page.getByRole("button", { name: t(buttonName) });
      await expect(button).toBeVisible();
      await activateForBrowser(button, isMobile);
    }

    await expect(
      page.getByRole("heading", { name: t("Submitted for review") }),
    ).toBeVisible();
    await expectNoCriticalA11yViolations(page);
    await expect(page).toHaveURL(`/verify/${sessionId}`);
  });
}

function json(route: Route, data: unknown, status = 200) {
  return route.fulfill({
    status,
    contentType: "application/json",
    body: JSON.stringify({ success: true, data }),
  });
}
