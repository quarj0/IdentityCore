import { expect, test } from "@playwright/test";

test("same-count PDF replacement with blank browser MIME can be submitted", async ({
  page,
  baseURL,
}) => {
  const submissions: Record<string, unknown>[] = [];
  let uploadMime = "",
    bytes = "";
  const state = {
    currentStep: "organization_verification",
    organizationVerificationEditable: false,
    organizationName: "Synthetic",
    businessRegistrationNumber: "SYNTHETIC-1",
    registeredAddress: "Synthetic address",
    officialWebsite: "https://example.test",
    taxIdentificationNumber: "SYNTHETIC-TAX",
    supportingDocuments: [
      {
        id: "doc_old",
        filename: "old.pdf",
        storage_key: "synthetic/old.pdf",
        file_size_bytes: 10,
        status: "submitted",
      },
    ],
  };
  await page.route("https://api.example.test/**", async (route) => {
    const request = route.request(),
      path = new URL(request.url()).pathname;
    const headers = {
      "Access-Control-Allow-Origin": baseURL!,
      "Access-Control-Allow-Credentials": "true",
      "Access-Control-Allow-Headers":
        "Authorization, Content-Type, X-Request-Id, X-IdentityCore-Session-Scope",
      "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
    };
    if (request.method() === "OPTIONS")
      return route.fulfill({ status: 204, headers });
    if (path === "/api/graphql") {
      const body = request.postDataJSON();
      if (body.query.includes("SubmitOrganizationVerification")) {
        submissions.push(body.variables.input);
        return route.fulfill({
          headers,
          json: {
            data: {
              submitOrganizationOnboardingVerification: {
                onboarding: state,
                nextAction: "organization_verification",
              },
            },
          },
        });
      }
      return route.fulfill({
        headers,
        json: { data: { organizationOnboarding: state } },
      });
    }
    let data: unknown = {};
    if (path.endsWith("/auth/refresh"))
      data = { tokens: { access: "synthetic-access" } };
    else if (path.endsWith("/auth/me"))
      data = { user: { email: "synthetic@example.test" } };
    else if (path.includes("/projects")) data = { results: [] };
    else if (path.endsWith("/verification-documents/upload/")) {
      uploadMime = request.postDataJSON().mime_type;
      data = {
        document_id: "doc_new",
        filename: "replacement.pdf",
        storage_key: "synthetic/new.pdf",
        file_size_bytes: 14,
        upload_url: "/organization/me/verification-documents/doc_new/content/",
      };
    } else if (path.endsWith("/doc_new/content/"))
      bytes = request.postDataBuffer()!.toString();
    await route.fulfill({ headers, json: { success: true, data } });
  });
  await page.goto("/onboarding/organization-verification");
  await page.getByRole("button", { name: "Remove old.pdf" }).click();
  await expect(page.getByText("old.pdf", { exact: true })).toHaveCount(0);
  await page
    .getByLabel("Supporting documents", { exact: false })
    .setInputFiles({
      name: "replacement.pdf",
      mimeType: "",
      buffer: Buffer.from("%PDF-synthetic"),
    });
  await expect(
    page.getByText("replacement.pdf", { exact: true }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Submit supporting documents" })
    .click();
  await expect.poll(() => submissions.length).toBe(1);
  expect(submissions[0].supportingDocumentKeys).toEqual(["synthetic/new.pdf"]);
  expect(uploadMime).toBe("application/pdf");
  expect(bytes).toBe("%PDF-synthetic");
});

test("evidence download refreshes an expired bearer and downloads exact bytes", async ({
  page,
  baseURL,
}) => {
  let refreshes = 0,
    downloadCalls = 0;
  const bytes = Buffer.from([0, 255, 1, 254]);
  await page.route("https://api.example.test/**", async (route) => {
    const request = route.request(),
      path = new URL(request.url()).pathname;
    const headers = {
      "Access-Control-Allow-Origin": baseURL!,
      "Access-Control-Allow-Credentials": "true",
      "Access-Control-Allow-Headers":
        "Authorization, Content-Type, X-Request-Id, X-IdentityCore-Session-Scope",
      "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    };
    if (request.method() === "OPTIONS")
      return route.fulfill({ status: 204, headers });
    let data: unknown = {};
    if (path.endsWith("/auth/refresh"))
      data = { tokens: { access: `synthetic-${++refreshes}` } };
    else if (path.endsWith("/auth/me"))
      data = { user: { email: "synthetic@example.test" } };
    else if (path.includes("/projects")) data = { results: [] };
    else if (path.endsWith("/download.pdf")) {
      downloadCalls++;
      if (downloadCalls === 1)
        return route.fulfill({
          status: 401,
          headers,
          json: { success: false, error: { code: "expired" } },
        });
      expect(request.headers().authorization).toBe(
        `Bearer synthetic-${refreshes}`,
      );
      return route.fulfill({
        headers: { ...headers, "Content-Type": "application/pdf" },
        body: bytes,
      });
    } else if (path.endsWith("/verifications/ver_evidence"))
      data = {
        id: "ver_evidence",
        status: "verified",
        purpose: "Synthetic",
        policy: { name: "Synthetic" },
        checks: {},
        verification_subject: { full_name: "Synthetic" },
        evidence_report: {
          download_url: "https://untrusted.example.test/never-use",
          pdf_download_url: "https://untrusted.example.test/never-use",
        },
        created_at: "2026-10-01T00:00:00Z",
        expires_at: "2099-01-01T00:00:00Z",
      };
    await route.fulfill({ headers, json: { success: true, data } });
  });
  await page.goto("/verifications/ver_evidence");
  const pending = page.waitForEvent("download");
  await page.getByRole("button", { name: "Evidence PDF" }).click();
  const download = await pending;
  const stream = await download.createReadStream();
  const chunks: Buffer[] = [];
  for await (const chunk of stream!) chunks.push(chunk);
  expect(Buffer.concat(chunks)).toEqual(bytes);
  expect(downloadCalls).toBe(2);
});
