import { expect, test } from "@playwright/test";

for (const enrollment of [true, false]) {
  test(`MFA ${enrollment ? "enrollment acknowledges recovery codes" : "challenge retries on user action"}`, async ({
    page,
    baseURL,
  }) => {
    let completed = false;
    let challenges = 0;
    const proof = "synthetic-mfa-proof";
    const secret = "JBSWY3DPEHPK3PXP";
    const recovery = "ABCDEF0123456789ABCDEF0123456789";
    await page.route("**/api/v1/**", async (route) => {
      const request = route.request();
      const path = new URL(request.url()).pathname;
      const headers = {
        "Access-Control-Allow-Origin": baseURL!,
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Headers":
          "Authorization, Content-Type, X-Request-Id, X-IdentityCore-Session-Scope",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
      };
      if (request.method() === "OPTIONS") {
        await route.fulfill({ status: 204, headers });
        return;
      }
      let status = 200;
      let data: unknown = {};
      const success = {
        tokens: { access: "synthetic-mfa-access" },
        user: {
          email: "staff@example.test",
          is_platform_admin: true,
          full_name: "Synthetic Staff",
        },
      };
      if (path.endsWith("/auth/login")) {
        status = 202;
        data = {
          mfa_required: true,
          mfa_enrollment_required: enrollment,
          mfa_token: proof,
        };
      } else if (path.includes("/auth/mfa/")) {
        expect(request.postDataJSON().mfa_token).toBe(proof);
        if (path.endsWith("/enroll")) data = { secret };
        else if (enrollment) {
          completed = true;
          data = { ...success, recovery_codes: [recovery] };
        } else {
          challenges += 1;
          if (challenges === 1) status = 401;
          else {
            completed = true;
            data = success;
          }
        }
      } else if (path.endsWith("/auth/refresh")) {
        status = completed ? 200 : 401;
        data = { tokens: success.tokens };
      } else if (path.endsWith("/auth/me")) data = { user: success.user };
      await route.fulfill({
        status,
        headers,
        json:
          status >= 400
            ? {
                success: false,
                error: {
                  code: "authentication_failed",
                  message: "Invalid code",
                },
              }
            : { success: true, data },
      });
    });
    await page.goto("/login");
    await page
      .getByLabel(/Business email|Email address/)
      .fill("staff@example.test");
    await page
      .getByLabel("Password", { exact: true })
      .fill("Synthetic-password-123");
    await page.getByRole("button", { name: /Sign in/ }).click();
    if (enrollment) {
      await page.getByRole("button", { name: "Generate setup key" }).click();
      await expect(page.getByLabel("Authenticator setup key")).toHaveText(
        secret,
      );
    }
    await page
      .getByLabel("Authentication code")
      .fill(enrollment ? "123456" : recovery);
    await page.getByRole("button", { name: "Verify", exact: true }).click();
    if (enrollment) {
      await expect(
        page.getByRole("heading", { name: "Save your recovery codes" }),
      ).toBeVisible();
      const stored = await page.evaluate(() =>
        JSON.stringify([localStorage, sessionStorage]),
      );
      for (const value of [proof, secret, recovery, "synthetic-mfa-access"])
        expect(stored).not.toContain(value);
      await page
        .getByRole("button", { name: "I saved my recovery codes" })
        .click();
    } else {
      await expect(
        page.getByRole("alert").filter({ hasText: "Verification failed" }),
      ).toContainText("Verification failed");
      expect(challenges).toBe(1);
      await page.getByRole("button", { name: "Verify", exact: true }).click();
      await expect.poll(() => challenges).toBe(2);
    }
    await page.waitForURL((url) => url.pathname === "/");
    await page.waitForLoadState("domcontentloaded");
    await expect
      .poll(() =>
        page.evaluate(() =>
          sessionStorage.getItem("identitycore.access_token"),
        ),
      )
      .toBe("synthetic-mfa-access");
    const stored = await page.evaluate(() =>
      JSON.stringify([localStorage, sessionStorage]),
    );
    for (const value of [proof, secret, recovery])
      expect(stored).not.toContain(value);
  });
}
