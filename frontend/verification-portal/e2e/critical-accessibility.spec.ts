import { createRequire } from "node:module";
import { expect, test, type Page, type Route } from "@playwright/test";

const require = createRequire(import.meta.url);
const sessionId = "ses_a11y_test";
const verificationId = "ver_a11y_test";
const image = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=",
  "base64",
);

async function json(route: Route, body: unknown, status = 200) {
  await route.fulfill({
    status,
    contentType: "application/json",
    body: JSON.stringify(body),
  });
}

async function assertNoSeriousViolations(page: Page) {
  if (!(await page.evaluate(() => Boolean((window as unknown as { axe?: unknown }).axe)))) {
    await page.addScriptTag({ path: require.resolve("axe-core/axe.min.js") });
  }
  const violations = await page.evaluate(async () => {
    const axe = (window as unknown as {
      axe: {
        run: (context?: unknown, options?: unknown) => Promise<{
          violations: Array<{ id: string; impact: string | null; nodes: unknown[] }>;
        }>;
      };
    }).axe;
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

async function pressFocused(page: Page, locator: ReturnType<Page["getByRole"]>) {
  await locator.focus();
  await expect(locator).toBeFocused();
  await page.keyboard.press("Enter");
}

test("critical verification journey is WCAG-clean and keyboard operable", async ({
  page,
  isMobile,
}) => {
  test.skip(isMobile, "Keyboard journey is exercised on desktop projects.");
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
      return json(route, { success: true });
    }
    if (path === `/api/verification/sessions/${sessionId}` && method === "GET") {
      return json(route, {
        session_id: sessionId,
        verification_id: verificationId,
        status: "active",
        organization: { name: "Accessible Bank", logo_url: "" },
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
          template_id: "ctm_a11y",
          version: 1,
          locale: "en",
          content: "I consent to identity verification.",
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
    if (path === `/api/verification/sessions/${sessionId}/status`) {
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
    if (path.endsWith("/consent") && method === "POST") {
      step = "document_capture";
      return json(route, { next_step: step });
    }
    if (path === "/api/verification/uploads/" && method === "POST") {
      uploadNumber += 1;
      return json(
        route,
        {
          upload_id: `upl_${uploadNumber}`,
          upload_url: "",
          upload_headers: {},
          upload_transfer_path: `/uploads/upl_${uploadNumber}/transfer`,
          upload_complete_path: `/uploads/upl_${uploadNumber}/complete`,
        },
        201,
      );
    }
    if (/\/uploads\/upl_\d+\/(transfer|complete)$/.test(path)) {
      return json(route, { upload_id: `upl_${uploadNumber}` });
    }
    if (path.endsWith("/documents") && method === "POST") {
      step = "selfie_capture";
      return json(route, {
        identity_document_id: "doc_a11y",
        status: "processing",
        next_step: "document_processing",
      });
    }
    if (path.endsWith("/selfies") && method === "POST") {
      step = "liveness_check";
      return json(route, {
        selfie_capture_id: "sel_a11y",
        status: "processing",
        next_step: "liveness_check",
      });
    }
    if (path.endsWith("/liveness/challenge") && method === "POST") {
      return json(route, {
        challenge_id: "lch_a11y",
        actions: ["turn_left", "look_up"],
        expires_at: new Date(Date.now() + 60_000).toISOString(),
      });
    }
    if (path.endsWith("/liveness") && method === "POST") {
      step = "completed";
      return json(route, {
        liveness_check_id: "liv_a11y",
        status: "processing",
        next_step: "processing",
      });
    }
    return route.abort("failed");
  });

  await page.goto(`/verify/${sessionId}#token=a11y-secret`);
  const handoff = page.getByRole("button", { name: "Continue on this computer" });
  await expect(handoff).toBeVisible();
  await assertNoSeriousViolations(page);
  await pressFocused(page, handoff);

  await expect(
    page.getByRole("heading", { name: "Review and give consent" }),
  ).toBeVisible();
  await assertNoSeriousViolations(page);
  const consent = page.getByRole("checkbox");
  await consent.focus();
  await page.keyboard.press("Space");
  await expect(consent).toBeChecked();
  await pressFocused(page, page.getByRole("button", { name: "Accept and continue" }));

  await expect(
    page.getByRole("heading", { name: "Capture your National ID" }),
  ).toBeVisible();
  await assertNoSeriousViolations(page);
  await page.getByLabel("Upload image").setInputFiles({
    name: "front.png",
    mimeType: "image/png",
    buffer: image,
  });
  await pressFocused(page, page.getByRole("button", { name: "Back Not captured" }));
  await page.getByLabel("Upload image").setInputFiles({
    name: "back.png",
    mimeType: "image/png",
    buffer: image,
  });
  await pressFocused(page, page.getByRole("button", { name: "Submit document" }));

  await expect(page.getByRole("heading", { name: "Take a live selfie" })).toBeVisible();
  await assertNoSeriousViolations(page);
  await page.getByLabel("Upload image").setInputFiles({
    name: "selfie.png",
    mimeType: "image/png",
    buffer: image,
  });
  await pressFocused(page, page.getByRole("button", { name: "Submit selfie" }));

  await expect(
    page.getByRole("heading", { name: "Complete a live camera check" }),
  ).toBeVisible();
  await assertNoSeriousViolations(page);
  for (const name of [
    "Begin live camera check",
    "Enable camera",
    "Start live challenge",
    "Finish recording",
    "Submit live check",
  ]) {
    await pressFocused(page, page.getByRole("button", { name }));
  }

  await expect(
    page.getByRole("heading", { name: "Submitted for review" }),
  ).toBeVisible();
  await assertNoSeriousViolations(page);
});
