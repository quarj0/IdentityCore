import { expect, test, type Locator, type Route } from "@playwright/test";

import { expectNoCriticalA11yViolations } from "./a11y-helpers";

const sessionId = "ses_accessibility";
const verificationId = "ver_accessibility";
const image = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=",
  "base64",
);

async function activateWithKeyboard(locator: Locator, key = "Enter") {
  await locator.focus();
  await expect(locator).toBeFocused();
  await locator.press(key);
}

test("critical subject verification journey is WCAG-clean and keyboard operable", async ({
  isMobile,
  page,
}) => {
  test.slow();

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
    Object.defineProperty(window, "MediaRecorder", { value: MockMediaRecorder });
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
        locale: "en",
        supported_locales: ["en"],
        direction: "ltr",
        consent: {
          template_id: "ctm_accessibility",
          version: 1,
          locale: "en",
          content: "I consent to identity verification for accessibility testing.",
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
        status: step === "completed" ? "manual_review_required" : "in_progress",
        current_step: step,
        message:
          step === "completed"
            ? "Your verification was submitted and requires additional review."
            : "Continue your verification.",
        evidence: {
          identity_document_id:
            step === "consent" || step === "document_capture" ? "" : "doc_a11y",
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
        actions: ["turn_left", "look_up"],
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
      page.getByRole("button", { name: "Continue on this computer" }),
    );
  }

  await expect(
    page.getByRole("heading", { name: "Review and give consent" }),
  ).toBeVisible();
  await expectNoCriticalA11yViolations(page);
  const consent = page.getByRole("checkbox");
  await activateWithKeyboard(consent, "Space");
  await expect(consent).toBeChecked();
  await activateWithKeyboard(
    page.getByRole("button", { name: "Accept and continue" }),
  );

  await expect(
    page.getByRole("heading", { name: "Capture your National ID" }),
  ).toBeVisible();
  await expectNoCriticalA11yViolations(page);
  const upload = page.getByLabel("Upload image");
  await upload.focus();
  await expect(upload).toBeFocused();
  await upload.setInputFiles({
    name: "national-id-front.png",
    mimeType: "image/png",
    buffer: image,
  });
  await activateWithKeyboard(page.getByRole("button", { name: "Back Not captured" }));
  await upload.setInputFiles({
    name: "national-id-back.png",
    mimeType: "image/png",
    buffer: image,
  });
  await activateWithKeyboard(page.getByRole("button", { name: "Submit document" }));

  await expect(
    page.getByRole("heading", { name: "Take a live selfie" }),
  ).toBeVisible();
  await expectNoCriticalA11yViolations(page);
  await upload.setInputFiles({
    name: "selfie.png",
    mimeType: "image/png",
    buffer: image,
  });
  await activateWithKeyboard(page.getByRole("button", { name: "Submit selfie" }));

  await expect(
    page.getByRole("heading", { name: "Complete a live camera check" }),
  ).toBeVisible();
  await expectNoCriticalA11yViolations(page);
  for (const buttonName of [
    "Begin live camera check",
    "Enable camera",
    "Start live challenge",
    "Finish recording",
    "Submit live check",
  ]) {
    const button = page.getByRole("button", { name: buttonName });
    await expect(button).toBeVisible();
    await activateWithKeyboard(button);
  }

  await expect(
    page.getByRole("heading", { name: "Submitted for review" }),
  ).toBeVisible();
  await expectNoCriticalA11yViolations(page);
  await expect(page).toHaveURL(`/verify/${sessionId}`);
});

function json(route: Route, data: unknown, status = 200) {
  return route.fulfill({
    status,
    contentType: "application/json",
    body: JSON.stringify({ success: true, data }),
  });
}
