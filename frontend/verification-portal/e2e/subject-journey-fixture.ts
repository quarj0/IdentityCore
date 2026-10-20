import type { Page, Route } from "@playwright/test";

export const sessionId = "ses_accessibility";
export const verificationId = "ver_accessibility";
export const image = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=",
  "base64",
);

export async function mockSubjectJourney(
  page: Page,
  locale: "en" | "ar",
  terminal?: "verified" | "failed",
) {
  let step =
    terminal === "failed" ? "failed" : terminal ? "completed" : "consent";
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

    if (
      path === "/api/verification/session" &&
      ["POST", "DELETE"].includes(method)
    ) {
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
        expires_at: new Date(Date.now() + 600_000).toISOString(),
      });
    }
    if (
      path === `/api/verification/sessions/${sessionId}/status` &&
      method === "GET"
    ) {
      return json(route, {
        verification_id: verificationId,
        status:
          step === "failed"
            ? "failed"
            : step === "completed"
              ? (terminal ?? "manual_review_required")
              : "in_progress",
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
      path === `/api/verification/sessions/${sessionId}/mobile-handoff` &&
      method === "POST"
    ) {
      return json(route, {
        handoff_url: `https://verify.example.test/verify/${sessionId}#handoff=synthetic-one-time-claim`,
        expires_at: new Date(Date.now() + 600_000).toISOString(),
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
}

function json(route: Route, data: unknown, status = 200) {
  return route.fulfill({
    status,
    contentType: "application/json",
    body: JSON.stringify({ success: true, data }),
  });
}
