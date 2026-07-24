import { expect, test, type Route } from "@playwright/test";

const sessionId = "ses_browser_test";
const verificationId = "ver_browser_test";
const image = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=",
  "base64",
);

test("subject completes consent, document, selfie, liveness, and review routing", async ({
  page,
}) => {
  let step = "consent";
  let uploadNumber = 0;

  await page.addInitScript(() => {
    class MockMediaRecorder {
      static isTypeSupported() { return true; }
      state = "inactive";
      ondataavailable: ((event: { data: Blob }) => void) | null = null;
      onstop: (() => void) | null = null;
      start() { this.state = "recording"; }
      stop() {
        this.state = "inactive";
        this.ondataavailable?.({ data: new Blob(["live-video"], { type: "video/webm" }) });
        this.onstop?.();
      }
    }
    Object.defineProperty(window, "MediaRecorder", { value: MockMediaRecorder });
    Object.defineProperty(navigator, "mediaDevices", {
      value: { getUserMedia: async () => new MediaStream() },
    });
  });

  await page.route("http://localhost:8000/api/v1/**", async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const path = url.pathname;
    const method = request.method();

    if (path === `/api/v1/sessions/${sessionId}` && method === "GET") {
      return json(route, {
        session_id: sessionId,
        verification_id: verificationId,
        status: "active",
        organization: { name: "Example Bank", logo_url: "" },
        purpose: "Customer onboarding",
        required_steps: [
          "consent",
          "document_capture",
          "selfie_capture",
          "liveness_check",
        ],
        document: {
          country_code: "GH",
          document_type: "national_id",
          label: "National ID",
        },
        expires_at: new Date(Date.now() + 60_000).toISOString(),
      });
    }

    if (
      path === `/api/v1/sessions/${sessionId}/status` &&
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
            step === "consent" || step === "document_capture" ? "" : "doc_1",
          selfie_capture_id:
            ["liveness_check", "processing", "completed"].includes(step)
              ? "sel_1"
              : "",
          liveness_check_id: step === "completed" ? "liv_1" : "",
        },
      });
    }

    if (
      path === `/api/v1/sessions/${sessionId}/consent` &&
      method === "POST"
    ) {
      step = "document_capture";
      return json(route, { next_step: step });
    }

    if (path === "/api/v1/uploads/" && method === "POST") {
      uploadNumber += 1;
      return json(
        route,
        {
          upload_id: `upl_${uploadNumber}`,
          upload_url: "",
          upload_headers: {},
          upload_transfer_path: `/uploads/upl_${uploadNumber}/transfer`,
        },
        201,
      );
    }

    if (/\/api\/v1\/uploads\/upl_\d+\/transfer$/.test(path)) {
      return json(route, { upload_id: `upl_${uploadNumber}` });
    }

    if (
      path === `/api/v1/sessions/${sessionId}/documents` &&
      method === "POST"
    ) {
      step = "selfie_capture";
      return json(route, {
        identity_document_id: "doc_1",
        status: "processing",
        next_step: "document_processing",
      });
    }

    if (
      path === `/api/v1/sessions/${sessionId}/selfies` &&
      method === "POST"
    ) {
      step = "liveness_check";
      return json(route, {
        selfie_capture_id: "sel_1",
        status: "processing",
        next_step: "liveness_check",
      });
    }

    if (
      path === `/api/v1/sessions/${sessionId}/liveness/challenge` &&
      method === "POST"
    ) {
      return json(route, {
        challenge_id: "lch_1",
        actions: ["turn_left", "look_up"],
        expires_at: new Date(Date.now() + 60_000).toISOString(),
      });
    }

    if (
      path === `/api/v1/sessions/${sessionId}/liveness` &&
      method === "POST"
    ) {
      step = "completed";
      return json(route, {
        liveness_check_id: "liv_1",
        status: "processing",
        next_step: "processing",
      });
    }

    return route.abort("failed");
  });

  await page.goto(`/verify/${sessionId}#token=browser-secret`);
  await page.getByRole("button", { name: "Continue on this computer" }).click();

  await expect(page.getByRole("heading", { name: "Review and give consent" })).toBeVisible();
  await page.getByRole("checkbox").check();
  await page.getByRole("button", { name: "Accept and continue" }).click();

  await expect(page.getByRole("heading", { name: "Capture your National ID" })).toBeVisible();
  await page.locator('input[type="file"]').setInputFiles({
    name: "ghana-card.png",
    mimeType: "image/png",
    buffer: image,
  });
  await page.getByRole("button", { name: "Submit document" }).click();

  await expect(page.getByText("Document received")).toBeVisible();
  await expect(
    page.getByText("Your document was uploaded successfully"),
  ).toBeVisible();
  await expect(page.getByRole("heading", { name: "Take a live selfie" })).toBeVisible();
  await page.locator('input[type="file"]').setInputFiles({
    name: "selfie.png",
    mimeType: "image/png",
    buffer: image,
  });
  await page.getByRole("button", { name: "Submit selfie" }).click();

  await expect(page.getByText("Selfie received")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Complete a live camera check" })).toBeVisible();
  await page.getByRole("button", { name: "Begin live camera check" }).click();
  await page.getByRole("button", { name: "Enable camera" }).click();
  await page.getByRole("button", { name: "Start live challenge" }).click();
  await expect(page.getByRole("button", { name: "Submit live check" })).toBeVisible({ timeout: 10_000 });
  await page.getByRole("button", { name: "Submit live check" }).click();

  await expect(page.getByRole("heading", { name: "Submitted for review" })).toBeVisible();
  await expect(page.getByText("requires additional review")).toBeVisible();
  await expect(page).toHaveURL(`/verify/${sessionId}`);
});

test("expired sessions render a safe terminal state", async ({ page }) => {
  await page.route("http://localhost:8000/api/v1/**", async (route) => {
    const path = new URL(route.request().url()).pathname;
    if (path.endsWith("/status")) {
      return json(route, {
        verification_id: verificationId,
        status: "expired",
        current_step: "expired",
        message: "Your verification session has expired.",
        evidence: {
          identity_document_id: "",
          selfie_capture_id: "",
          liveness_check_id: "",
        },
      });
    }
    return json(route, {
      session_id: sessionId,
      verification_id: verificationId,
      status: "expired",
      organization: { name: "Example Bank", logo_url: "" },
      purpose: "Customer onboarding",
      required_steps: [],
      document: {
        country_code: "GH",
        document_type: "national_id",
        label: "National ID",
      },
      expires_at: new Date(Date.now() - 60_000).toISOString(),
    });
  });

  await page.goto(`/verify/${sessionId}#token=expired-secret`);
  await page.getByRole("button", { name: "Continue on this computer" }).click();
  await expect(page.getByRole("heading", { name: "This session has expired" })).toBeVisible();
});

function json(route: Route, data: unknown, status = 200) {
  return route.fulfill({
    status,
    contentType: "application/json",
    body: JSON.stringify({ success: true, data }),
  });
}
