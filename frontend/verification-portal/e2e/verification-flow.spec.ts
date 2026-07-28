import { expect, test, type Route } from "@playwright/test";

const sessionId = "ses_browser_test";
const verificationId = "ver_browser_test";
const consentContent =
  "I consent to identity verification for customer onboarding.";
const image = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=",
  "base64",
);

test("verification pages send hardened browser security headers", async ({
  request,
}) => {
  const response = await request.get("/");

  expect(response.headers()["cache-control"]).toContain("no-store");
  expect(response.headers()["content-security-policy"]).toContain(
    "frame-ancestors 'none'",
  );
  expect(response.headers()["permissions-policy"]).toContain("camera=(self)");
  expect(response.headers()["referrer-policy"]).toBe("no-referrer");
  expect(response.headers()["x-content-type-options"]).toBe("nosniff");
  expect(response.headers()["x-frame-options"]).toBe("DENY");
  expect(response.headers()["x-powered-by"]).toBeUndefined();
});

test("BFF rejects cross-origin session exchange and unauthenticated proxy calls", async ({
  request,
}) => {
  const exchange = await request.post("/api/verification/session", {
    headers: { Origin: "https://attacker.example" },
    data: { sessionId, sessionToken: "stolen-token" },
  });
  expect(exchange.status()).toBe(403);

  const proxy = await request.post(
    `/api/verification/sessions/${sessionId}/consent`,
    {
      data: { accepted: true },
    },
  );
  expect(proxy.status()).toBe(401);
});

test("subject completes consent, document, selfie, liveness, and review routing", async ({
  isMobile,
  page,
}) => {
  test.slow();

  let step = "consent";
  let uploadNumber = 0;
  let uploadCreateRequests = 0;
  let failBackUploadOnce = true;
  let livenessUploadMimeType = "";
  let documentPayload: {
    captures?: Array<{ side: string; upload_id: string }>;
  } = {};

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
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ success: true }),
      });
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
          template_id: "ctm_test",
          version: 3,
          locale: "en",
          content: consentContent,
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
            step === "consent" || step === "document_capture" ? "" : "doc_1",
          selfie_capture_id: [
            "liveness_check",
            "processing",
            "completed",
          ].includes(step)
            ? "sel_1"
            : "",
          liveness_check_id: step === "completed" ? "liv_1" : "",
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
      uploadCreateRequests += 1;
      const uploadPayload = request.postDataJSON() as {
        purpose?: string;
        mime_type?: string;
      };
      if (uploadPayload.purpose === "liveness_capture") {
        livenessUploadMimeType = uploadPayload.mime_type ?? "";
      }
      if (uploadNumber === 1 && failBackUploadOnce) {
        failBackUploadOnce = false;
        return route.fulfill({
          status: 503,
          contentType: "application/json",
          body: JSON.stringify({
            success: false,
            error: {
              message: "The upload service is temporarily unavailable.",
            },
          }),
        });
      }
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

    if (/\/api\/verification\/uploads\/upl_\d+\/transfer$/.test(path)) {
      return json(route, { upload_id: `upl_${uploadNumber}` });
    }

    if (
      path === `/api/verification/sessions/${sessionId}/documents` &&
      method === "POST"
    ) {
      documentPayload = request.postDataJSON() as typeof documentPayload;
      step = "selfie_capture";
      return json(route, {
        identity_document_id: "doc_1",
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
        selfie_capture_id: "sel_1",
        status: "processing",
        next_step: "liveness_check",
      });
    }

    if (
      path === `/api/verification/sessions/${sessionId}/liveness/challenge` &&
      method === "POST"
    ) {
      return json(route, {
        challenge_id: "lch_1",
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
        liveness_check_id: "liv_1",
        status: "processing",
        next_step: "processing",
      });
    }

    return route.abort("failed");
  });

  await page.goto(`/verify/${sessionId}#token=browser-secret`);
  if (!isMobile) {
    await page
      .getByRole("button", { name: "Continue on this computer" })
      .click();
  }

  await expect(
    page.getByRole("heading", { name: "Review and give consent" }),
  ).toBeVisible();
  await expect(page.locator("html")).toHaveAttribute("lang", "en");
  await expect(page.getByText(consentContent)).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Review and give consent" }),
  ).toBeFocused();
  await page.getByRole("checkbox").check();
  await page.getByRole("button", { name: "Accept and continue" }).click();

  await expect(
    page.getByRole("heading", { name: "Capture your National ID" }),
  ).toBeVisible();
  await page.getByLabel("Upload image").setInputFiles({
    name: "ghana-card-front.png",
    mimeType: "image/png",
    buffer: image,
  });
  const backCapture = page.getByRole("button", {
    name: "Back Not captured",
  });
  await backCapture.click();
  await expect(backCapture).toHaveAttribute("aria-pressed", "true");
  await page.getByLabel("Upload image").setInputFiles({
    name: "ghana-card-back.png",
    mimeType: "image/png",
    buffer: image,
  });
  await page.getByRole("button", { name: "Submit document" }).click();
  await expect(
    page.getByRole("alert").filter({ hasText: "We could not continue" }),
  ).toContainText("The upload service is temporarily unavailable.");
  await page.getByRole("button", { name: "Submit document" }).click();

  await expect(page.getByText("Document received")).toBeVisible();
  await expect(
    page.getByText("Your document was uploaded successfully"),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Take a live selfie" }),
  ).toBeVisible();
  expect(documentPayload.captures).toEqual([
    { side: "front", upload_id: "upl_1" },
    { side: "back", upload_id: "upl_2" },
  ]);
  expect(uploadCreateRequests).toBe(3);
  await page.getByLabel("Upload image").setInputFiles({
    name: "selfie.png",
    mimeType: "image/png",
    buffer: image,
  });
  await page.getByRole("button", { name: "Submit selfie" }).click();

  await expect(page.getByText("Selfie received")).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Complete a live camera check" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Begin live camera check" }).click();
  await page.getByRole("button", { name: "Enable camera" }).click();
  await page.getByRole("button", { name: "Start live challenge" }).click();
  await page.getByRole("button", { name: "Finish recording" }).click();
  await expect(
    page.getByRole("button", { name: "Submit live check" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Submit live check" }).click();
  expect(livenessUploadMimeType).toBe("video/mp4");

  await expect(
    page.getByRole("heading", { name: "Submitted for review" }),
  ).toBeVisible();
  await expect(page.getByText("requires additional review")).toBeVisible();
  await expect(page).toHaveURL(`/verify/${sessionId}`);
});

test("expired sessions render a safe terminal state", async ({
  isMobile,
  page,
}) => {
  await page.route("**/api/verification/**", async (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    if (
      path === "/api/verification/session" &&
      request.method() === "POST"
    ) {
      return json(route, {});
    }
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
      workflow: { steps: [], liveness_mode: "passive" },
      locale: "en",
      supported_locales: ["en"],
      direction: "ltr",
      consent: {
        template_id: "ctm_test",
        version: 1,
        locale: "en",
        content: "Consent text",
        content_hash: "b".repeat(64),
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
      expires_at: new Date(Date.now() - 60_000).toISOString(),
    });
  });

  await page.goto(`/verify/${sessionId}#token=expired-secret`);
  if (!isMobile) {
    await page
      .getByRole("button", { name: "Continue on this computer" })
      .click();
  }
  await expect(
    page.getByRole("heading", { name: "This session has expired" }),
  ).toBeVisible();
});

function json(route: Route, data: unknown, status = 200) {
  return route.fulfill({
    status,
    contentType: "application/json",
    body: JSON.stringify({ success: true, data }),
  });
}
