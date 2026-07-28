# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: verification-flow.spec.ts >> subject completes consent, document, selfie, liveness, and review routing
- Location: e2e/verification-flow.spec.ts:10:5

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Error: locator.click: Test timeout of 30000ms exceeded.
Call log:
  - waiting for getByRole('button', { name: 'Continue on this computer' })

```

# Page snapshot

```yaml
- generic [active] [ref=e1]:
  - link "Skip to content" [ref=e2] [cursor=pointer]:
    - /url: "#main-content"
  - generic [ref=e4]:
    - heading "Verification unavailable" [level=1] [ref=e5]
    - paragraph [ref=e6]: The verification service is temporarily unavailable. Please try again shortly.
  - alert [ref=e7]
```

# Test source

```ts
  65  |       method === "GET"
  66  |     ) {
  67  |       return json(route, {
  68  |         verification_id: verificationId,
  69  |         status:
  70  |           step === "completed" ? "manual_review_required" : "in_progress",
  71  |         current_step: step,
  72  |         message:
  73  |           step === "completed"
  74  |             ? "Your verification was submitted and requires additional review."
  75  |             : "Continue your verification.",
  76  |         evidence: {
  77  |           identity_document_id:
  78  |             step === "consent" || step === "document_capture" ? "" : "doc_1",
  79  |           selfie_capture_id:
  80  |             ["liveness_check", "processing", "completed"].includes(step)
  81  |               ? "sel_1"
  82  |               : "",
  83  |           liveness_check_id: step === "completed" ? "liv_1" : "",
  84  |         },
  85  |       });
  86  |     }
  87  | 
  88  |     if (
  89  |       path === `/api/v1/sessions/${sessionId}/consent` &&
  90  |       method === "POST"
  91  |     ) {
  92  |       step = "document_capture";
  93  |       return json(route, { next_step: step });
  94  |     }
  95  | 
  96  |     if (path === "/api/v1/uploads/" && method === "POST") {
  97  |       uploadNumber += 1;
  98  |       return json(
  99  |         route,
  100 |         {
  101 |           upload_id: `upl_${uploadNumber}`,
  102 |           upload_url: "",
  103 |           upload_headers: {},
  104 |           upload_transfer_path: `/uploads/upl_${uploadNumber}/transfer`,
  105 |         },
  106 |         201,
  107 |       );
  108 |     }
  109 | 
  110 |     if (/\/api\/v1\/uploads\/upl_\d+\/transfer$/.test(path)) {
  111 |       return json(route, { upload_id: `upl_${uploadNumber}` });
  112 |     }
  113 | 
  114 |     if (
  115 |       path === `/api/v1/sessions/${sessionId}/documents` &&
  116 |       method === "POST"
  117 |     ) {
  118 |       step = "selfie_capture";
  119 |       return json(route, {
  120 |         identity_document_id: "doc_1",
  121 |         status: "processing",
  122 |         next_step: "document_processing",
  123 |       });
  124 |     }
  125 | 
  126 |     if (
  127 |       path === `/api/v1/sessions/${sessionId}/selfies` &&
  128 |       method === "POST"
  129 |     ) {
  130 |       step = "liveness_check";
  131 |       return json(route, {
  132 |         selfie_capture_id: "sel_1",
  133 |         status: "processing",
  134 |         next_step: "liveness_check",
  135 |       });
  136 |     }
  137 | 
  138 |     if (
  139 |       path === `/api/v1/sessions/${sessionId}/liveness/challenge` &&
  140 |       method === "POST"
  141 |     ) {
  142 |       return json(route, {
  143 |         challenge_id: "lch_1",
  144 |         actions: ["turn_left", "look_up"],
  145 |         expires_at: new Date(Date.now() + 60_000).toISOString(),
  146 |       });
  147 |     }
  148 | 
  149 |     if (
  150 |       path === `/api/v1/sessions/${sessionId}/liveness` &&
  151 |       method === "POST"
  152 |     ) {
  153 |       step = "completed";
  154 |       return json(route, {
  155 |         liveness_check_id: "liv_1",
  156 |         status: "processing",
  157 |         next_step: "processing",
  158 |       });
  159 |     }
  160 | 
  161 |     return route.abort("failed");
  162 |   });
  163 | 
  164 |   await page.goto(`/verify/${sessionId}#token=browser-secret`);
> 165 |   await page.getByRole("button", { name: "Continue on this computer" }).click();
      |                                                                         ^ Error: locator.click: Test timeout of 30000ms exceeded.
  166 | 
  167 |   await expect(page.getByRole("heading", { name: "Review and give consent" })).toBeVisible();
  168 |   await page.getByRole("checkbox").check();
  169 |   await page.getByRole("button", { name: "Accept and continue" }).click();
  170 | 
  171 |   await expect(page.getByRole("heading", { name: "Capture your National ID" })).toBeVisible();
  172 |   await page.locator('input[type="file"]').setInputFiles({
  173 |     name: "ghana-card.png",
  174 |     mimeType: "image/png",
  175 |     buffer: image,
  176 |   });
  177 |   await page.getByRole("button", { name: "Submit document" }).click();
  178 | 
  179 |   await expect(page.getByText("Document received")).toBeVisible();
  180 |   await expect(
  181 |     page.getByText("Your document was uploaded successfully"),
  182 |   ).toBeVisible();
  183 |   await expect(page.getByRole("heading", { name: "Take a live selfie" })).toBeVisible();
  184 |   await page.locator('input[type="file"]').setInputFiles({
  185 |     name: "selfie.png",
  186 |     mimeType: "image/png",
  187 |     buffer: image,
  188 |   });
  189 |   await page.getByRole("button", { name: "Submit selfie" }).click();
  190 | 
  191 |   await expect(page.getByText("Selfie received")).toBeVisible();
  192 |   await expect(page.getByRole("heading", { name: "Complete a live camera check" })).toBeVisible();
  193 |   await page.getByRole("button", { name: "Begin live camera check" }).click();
  194 |   await page.getByRole("button", { name: "Enable camera" }).click();
  195 |   await page.getByRole("button", { name: "Start live challenge" }).click();
  196 |   await expect(page.getByRole("button", { name: "Submit live check" })).toBeVisible({ timeout: 10_000 });
  197 |   await page.getByRole("button", { name: "Submit live check" }).click();
  198 | 
  199 |   await expect(page.getByRole("heading", { name: "Submitted for review" })).toBeVisible();
  200 |   await expect(page.getByText("requires additional review")).toBeVisible();
  201 |   await expect(page).toHaveURL(`/verify/${sessionId}`);
  202 | });
  203 | 
  204 | test("expired sessions render a safe terminal state", async ({ page }) => {
  205 |   await page.route("http://localhost:8000/api/v1/**", async (route) => {
  206 |     const path = new URL(route.request().url()).pathname;
  207 |     if (path.endsWith("/status")) {
  208 |       return json(route, {
  209 |         verification_id: verificationId,
  210 |         status: "expired",
  211 |         current_step: "expired",
  212 |         message: "Your verification session has expired.",
  213 |         evidence: {
  214 |           identity_document_id: "",
  215 |           selfie_capture_id: "",
  216 |           liveness_check_id: "",
  217 |         },
  218 |       });
  219 |     }
  220 |     return json(route, {
  221 |       session_id: sessionId,
  222 |       verification_id: verificationId,
  223 |       status: "expired",
  224 |       organization: { name: "Example Bank", logo_url: "" },
  225 |       purpose: "Customer onboarding",
  226 |       required_steps: [],
  227 |       document: {
  228 |         country_code: "GH",
  229 |         document_type: "national_id",
  230 |         label: "National ID",
  231 |       },
  232 |       expires_at: new Date(Date.now() - 60_000).toISOString(),
  233 |     });
  234 |   });
  235 | 
  236 |   await page.goto(`/verify/${sessionId}#token=expired-secret`);
  237 |   await page.getByRole("button", { name: "Continue on this computer" }).click();
  238 |   await expect(page.getByRole("heading", { name: "This session has expired" })).toBeVisible();
  239 | });
  240 | 
  241 | function json(route: Route, data: unknown, status = 200) {
  242 |   return route.fulfill({
  243 |     status,
  244 |     contentType: "application/json",
  245 |     body: JSON.stringify({ success: true, data }),
  246 |   });
  247 | }
  248 | 
```