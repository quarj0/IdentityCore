# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: verification-flow.spec.ts >> expired sessions render a safe terminal state
- Location: e2e/verification-flow.spec.ts:204:5

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
  165 |   await page.getByRole("button", { name: "Continue on this computer" }).click();
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
> 237 |   await page.getByRole("button", { name: "Continue on this computer" }).click();
      |                                                                         ^ Error: locator.click: Test timeout of 30000ms exceeded.
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