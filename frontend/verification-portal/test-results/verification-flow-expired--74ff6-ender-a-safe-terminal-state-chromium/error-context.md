# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: verification-flow.spec.ts >> expired sessions render a safe terminal state
- Location: e2e/verification-flow.spec.ts:353:1

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
  377 |       session_id: sessionId,
  378 |       verification_id: verificationId,
  379 |       status: "expired",
  380 |       organization: { name: "Example Bank", logo_url: "" },
  381 |       purpose: "Customer onboarding",
  382 |       required_steps: [],
  383 |       workflow: { steps: [], liveness_mode: "passive" },
  384 |       locale: "en",
  385 |       supported_locales: ["en"],
  386 |       direction: "ltr",
  387 |       consent: {
  388 |         template_id: "ctm_test",
  389 |         version: 1,
  390 |         locale: "en",
  391 |         content: "Consent text",
  392 |         content_hash: "b".repeat(64),
  393 |       },
  394 |       document: {
  395 |         country_code: "GH",
  396 |         document_type: "national_id",
  397 |         label: "National ID",
  398 |         capture_requirements: [
  399 |           { side: "front", label: "Front", required: true },
  400 |           { side: "back", label: "Back", required: true },
  401 |         ],
  402 |       },
  403 |       expires_at: new Date(Date.now() - 60_000).toISOString(),
  404 |     });
  405 |   });
  406 | 
  407 |   await page.goto(`/verify/${sessionId}#token=expired-secret`);
  408 |   if (!isMobile) {
  409 |     await page
  410 |       .getByRole("button", { name: "Continue on this computer" })
> 411 |       .click();
      |        ^ Error: locator.click: Test timeout of 30000ms exceeded.
  412 |   }
  413 |   await expect(
  414 |     page.getByRole("heading", { name: "This session has expired" }),
  415 |   ).toBeVisible();
  416 | });
  417 | 
  418 | function json(route: Route, data: unknown, status = 200) {
  419 |   return route.fulfill({
  420 |     status,
  421 |     contentType: "application/json",
  422 |     body: JSON.stringify({ success: true, data }),
  423 |   });
  424 | }
  425 | 
  426 | function apiPath(url: URL) {
  427 |   return url.pathname.replace(/^\/api\/verification/, "/api/v1");
  428 | }
  429 | 
```