# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: verification-flow.spec.ts >> subject completes consent, document, selfie, liveness, and review routing
- Location: e2e/verification-flow.spec.ts:44:1

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
  - main [ref=e3]:
    - generic [ref=e5]:
      - heading "Opening your secure session" [level=1] [ref=e8]
      - paragraph [ref=e9]: Validating your one-time session credential…
```

# Test source

```ts
  176 |       method === "POST"
  177 |     ) {
  178 |       step = "document_capture";
  179 |       return json(route, { next_step: step });
  180 |     }
  181 | 
  182 |     if (path === "/api/v1/uploads/" && method === "POST") {
  183 |       uploadCreateRequests += 1;
  184 |       const uploadPayload = request.postDataJSON() as {
  185 |         purpose?: string;
  186 |         mime_type?: string;
  187 |       };
  188 |       if (uploadPayload.purpose === "liveness_capture") {
  189 |         livenessUploadMimeType = uploadPayload.mime_type ?? "";
  190 |       }
  191 |       if (uploadNumber === 1 && failBackUploadOnce) {
  192 |         failBackUploadOnce = false;
  193 |         return route.fulfill({
  194 |           status: 503,
  195 |           contentType: "application/json",
  196 |           body: JSON.stringify({
  197 |             success: false,
  198 |             error: {
  199 |               message: "The upload service is temporarily unavailable.",
  200 |             },
  201 |           }),
  202 |         });
  203 |       }
  204 |       uploadNumber += 1;
  205 |       return json(
  206 |         route,
  207 |         {
  208 |           upload_id: `upl_${uploadNumber}`,
  209 |           upload_url: "",
  210 |           upload_headers: {},
  211 |           upload_transfer_path: `/uploads/upl_${uploadNumber}/transfer`,
  212 |         },
  213 |         201,
  214 |       );
  215 |     }
  216 | 
  217 |     if (/\/api\/v1\/uploads\/upl_\d+\/transfer$/.test(path)) {
  218 |       return json(route, { upload_id: `upl_${uploadNumber}` });
  219 |     }
  220 | 
  221 |     if (
  222 |       path === `/api/v1/sessions/${sessionId}/documents` &&
  223 |       method === "POST"
  224 |     ) {
  225 |       documentPayload = request.postDataJSON() as typeof documentPayload;
  226 |       step = "selfie_capture";
  227 |       return json(route, {
  228 |         identity_document_id: "doc_1",
  229 |         status: "processing",
  230 |         next_step: "document_processing",
  231 |       });
  232 |     }
  233 | 
  234 |     if (
  235 |       path === `/api/v1/sessions/${sessionId}/selfies` &&
  236 |       method === "POST"
  237 |     ) {
  238 |       step = "liveness_check";
  239 |       return json(route, {
  240 |         selfie_capture_id: "sel_1",
  241 |         status: "processing",
  242 |         next_step: "liveness_check",
  243 |       });
  244 |     }
  245 | 
  246 |     if (
  247 |       path === `/api/v1/sessions/${sessionId}/liveness/challenge` &&
  248 |       method === "POST"
  249 |     ) {
  250 |       return json(route, {
  251 |         challenge_id: "lch_1",
  252 |         actions: ["turn_left", "look_up"],
  253 |         expires_at: new Date(Date.now() + 60_000).toISOString(),
  254 |       });
  255 |     }
  256 | 
  257 |     if (
  258 |       path === `/api/v1/sessions/${sessionId}/liveness` &&
  259 |       method === "POST"
  260 |     ) {
  261 |       step = "completed";
  262 |       return json(route, {
  263 |         liveness_check_id: "liv_1",
  264 |         status: "processing",
  265 |         next_step: "processing",
  266 |       });
  267 |     }
  268 | 
  269 |     return route.abort("failed");
  270 |   });
  271 | 
  272 |   await page.goto(`/verify/${sessionId}#token=browser-secret`);
  273 |   if (!isMobile) {
  274 |     await page
  275 |       .getByRole("button", { name: "Continue on this computer" })
> 276 |       .click();
      |        ^ Error: locator.click: Test timeout of 30000ms exceeded.
  277 |   }
  278 | 
  279 |   await expect(
  280 |     page.getByRole("heading", { name: "Review and give consent" }),
  281 |   ).toBeVisible();
  282 |   await expect(page.locator("html")).toHaveAttribute("lang", "en");
  283 |   await expect(
  284 |     page.getByText(
  285 |       "I consent to Example Bank processing my identity evidence.",
  286 |     ),
  287 |   ).toBeVisible();
  288 |   await expect(
  289 |     page.getByRole("heading", { name: "Review and give consent" }),
  290 |   ).toBeFocused();
  291 |   await page.getByRole("checkbox").check();
  292 |   await page.getByRole("button", { name: "Accept and continue" }).click();
  293 | 
  294 |   await expect(
  295 |     page.getByRole("heading", { name: "Capture your National ID" }),
  296 |   ).toBeVisible();
  297 |   await page.locator('input[type="file"]').setInputFiles({
  298 |     name: "ghana-card-front.png",
  299 |     mimeType: "image/png",
  300 |     buffer: image,
  301 |   });
  302 |   await page.getByRole("button", { name: "Capture back" }).click();
  303 |   await page.locator('input[type="file"]').setInputFiles({
  304 |     name: "ghana-card-back.png",
  305 |     mimeType: "image/png",
  306 |     buffer: image,
  307 |   });
  308 |   await page.getByRole("button", { name: "Submit document" }).click();
  309 |   await expect(
  310 |     page.getByRole("alert").filter({ hasText: "We could not continue" }),
  311 |   ).toContainText("The upload service is temporarily unavailable.");
  312 |   await page.getByRole("button", { name: "Submit document" }).click();
  313 | 
  314 |   await expect(page.getByText("Document received")).toBeVisible();
  315 |   await expect(
  316 |     page.getByText("Your document was uploaded successfully"),
  317 |   ).toBeVisible();
  318 |   await expect(
  319 |     page.getByRole("heading", { name: "Take a live selfie" }),
  320 |   ).toBeVisible();
  321 |   expect(documentPayload.captures).toEqual([
  322 |     { side: "front", upload_id: "upl_1" },
  323 |     { side: "back", upload_id: "upl_2" },
  324 |   ]);
  325 |   expect(uploadCreateRequests).toBe(3);
  326 |   await page.locator('input[type="file"]').setInputFiles({
  327 |     name: "selfie.png",
  328 |     mimeType: "image/png",
  329 |     buffer: image,
  330 |   });
  331 |   await page.getByRole("button", { name: "Submit selfie" }).click();
  332 | 
  333 |   await expect(page.getByText("Selfie received")).toBeVisible();
  334 |   await expect(
  335 |     page.getByRole("heading", { name: "Complete a live camera check" }),
  336 |   ).toBeVisible();
  337 |   await page.getByRole("button", { name: "Begin live camera check" }).click();
  338 |   await page.getByRole("button", { name: "Enable camera" }).click();
  339 |   await page.getByRole("button", { name: "Start live challenge" }).click();
  340 |   await expect(
  341 |     page.getByRole("button", { name: "Submit live check" }),
  342 |   ).toBeVisible({ timeout: 10_000 });
  343 |   await page.getByRole("button", { name: "Submit live check" }).click();
  344 |   expect(livenessUploadMimeType).toBe("video/mp4");
  345 | 
  346 |   await expect(
  347 |     page.getByRole("heading", { name: "Submitted for review" }),
  348 |   ).toBeVisible();
  349 |   await expect(page.getByText("requires additional review")).toBeVisible();
  350 |   await expect(page).toHaveURL(`/verify/${sessionId}`);
  351 | });
  352 | 
  353 | test("expired sessions render a safe terminal state", async ({
  354 |   isMobile,
  355 |   page,
  356 | }) => {
  357 |   await page.route("**/api/verification/**", async (route) => {
  358 |     const request = route.request();
  359 |     const path = apiPath(new URL(request.url()));
  360 |     if (path === "/api/v1/session" && request.method() === "POST") {
  361 |       return json(route, {});
  362 |     }
  363 |     if (path.endsWith("/status")) {
  364 |       return json(route, {
  365 |         verification_id: verificationId,
  366 |         status: "expired",
  367 |         current_step: "expired",
  368 |         message: "Your verification session has expired.",
  369 |         evidence: {
  370 |           identity_document_id: "",
  371 |           selfie_capture_id: "",
  372 |           liveness_check_id: "",
  373 |         },
  374 |       });
  375 |     }
  376 |     return json(route, {
```