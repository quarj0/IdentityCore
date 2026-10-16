import { expect, test, type Page } from "@playwright/test";

async function billingFixture(
  page: Page,
  {
    provider = "paystack",
    pending = false,
    canManage = true,
    invalidUrl = false,
    gatewayUnavailable = false,
    verified = true,
  }: {
    provider?: "paystack" | "paystack";
    pending?: boolean;
    canManage?: boolean;
    invalidUrl?: boolean;
    gatewayUnavailable?: boolean;
    verified?: boolean;
  } = {},
) {
  const calls: { checkout: unknown[]; verification: number } = {
    checkout: [],
    verification: 0,
  };
  let paid = false;
  await page.route("https://checkout.paystack.com/**", (route) =>
    route.fulfill({
      contentType: "text/html",
      body: "<h1>Synthetic Paystack checkout</h1>",
    }),
  );
  await page.route("https://api.example.test/**", async (route) => {
    const request = route.request(),
      path = new URL(request.url()).pathname;
    const headers = {
      "Access-Control-Allow-Origin": "http://127.0.0.1:3005",
      "Access-Control-Allow-Credentials": "true",
      "Access-Control-Allow-Headers":
        "Authorization, Content-Type, X-Request-Id, X-IdentityCore-Session-Scope",
      "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    };
    if (request.method() === "OPTIONS") {
      await route.fulfill({ status: 204, headers });
      return;
    }
    let data: unknown = {};
    if (path.includes("/auth/refresh"))
      data = { tokens: { access: "browser-access" } };
    else if (path.includes("/auth/me"))
      data = {
        user: {
          id: "usr_browser",
          email: "browser@example.test",
          full_name: "Finance manager",
        },
      };
    else if (path.includes("/projects")) data = { results: [] };
    else if (path.includes("/organization/me")) data = { status: "active" };
    else if (path.endsWith("/checkout")) {
      calls.checkout.push(request.postDataJSON());
      if (gatewayUnavailable) {
        await route.fulfill({
          status: 503,
          headers,
          json: {
            success: false,
            error: {
              code: "gateway_unavailable",
              message: "Payment gateway unavailable.",
              details: {},
            },
            request_id: "req_synthetic",
          },
        });
        return;
      }
      data = {
        payment_id: "bpa_Synthetic1",
        reference: "icSynthetic1",
        currency: provider === "paystack" ? "GHS" : "USD",
        amount_minor: 10750,
        provider,
        status: "pending",
        checkout_url: invalidUrl
          ? "https://evil.example.test/pay"
          : `https://checkout.${provider}.com/pay/synthetic`,
      };
    } else if (path.endsWith("/payments/bpa_Synthetic1")) {
      calls.verification++;
      paid = verified;
      data = { verified };
    } else if (path.includes("/billing/invoices")) {
      const invoice = {
        id: "bin_Synthetic1",
        plan_code: "test-plan",
        plan_version: 1,
        period_start: "2026-09-01",
        period_end: "2026-10-01",
        amount_minor: 10750,
        currency: provider === "paystack" ? "GHS" : "USD",
        status: paid ? "paid" : "issued",
        due_at: null,
        paid_at: paid ? "2026-10-15T12:00:00Z" : null,
        issued_at: "2026-10-01T00:00:00Z",
        can_manage_billing: canManage,
        payment_providers: canManage ? [provider] : [],
        payment:
          pending || paid
            ? {
                id: "bpa_Synthetic1",
                provider,
                status: paid ? "paid" : "pending",
              }
            : null,
        lines: [
          {
            description: "Monthly subscription",
            quantity: 1,
            unit_price_minor: 10000,
            amount_minor: 10000,
          },
          {
            description: "Provider usage",
            quantity: 3,
            unit_price_minor: 250,
            amount_minor: 750,
          },
        ],
      };
      data = path.endsWith("/invoices") ? { results: [invoice] } : invoice;
    }
    await route.fulfill({
      status: 200,
      headers,
      json: { success: true, data, request_id: "req_synthetic" },
    });
  });
  return calls;
}

for (const provider of ["paystack"] as const) {
  test(`opens ${provider} hosted checkout with only the provider choice`, async ({
    page,
  }) => {
    const calls = await billingFixture(page, { provider });
    await page.goto("/billing/invoices");
    await page
      .getByRole("button", {
        name: "Pay with Paystack",
      })
      .click();
    await expect(page).toHaveURL(
      new RegExp(`^https://checkout\\.${provider}\\.com/`),
    );
    expect(calls.checkout).toEqual([{ provider }]);
  });

  test(`verifies the ${provider} return before displaying paid`, async ({
    page,
  }) => {
    const calls = await billingFixture(page, { provider, pending: true });
    await page.goto("/billing/return?payment_id=bpa_Synthetic1");
    await expect(page.getByRole("status")).toContainText(
      "Payment transaction verified",
    );
    await expect(page.locator("article")).toContainText("paid · test-plan");
    expect(calls.verification).toBe(1);
  });

  test(`does not display paid for an unconfirmed ${provider} return`, async ({
    page,
  }) => {
    await billingFixture(page, { provider, pending: true, verified: false });
    await page.goto("/billing/invoices?payment_id=bpa_Synthetic1");
    await expect(page.getByRole("status")).toContainText(
      "Payment has not been confirmed yet",
    );
    await expect(page.locator("article")).toContainText("issued · test-plan");
    await expect(
      page.getByRole("button", { name: "Check payment" }),
    ).toBeVisible();
  });
}

test("refuses an unexpected checkout host and leaves the invoice retryable", async ({
  page,
}) => {
  await billingFixture(page, { invalidUrl: true });
  await page.goto("/billing/invoices");
  await page.getByRole("button", { name: "Pay with Paystack" }).click();
  await expect(page.locator("main").getByRole("alert")).toContainText(
    "Unexpected payment checkout URL",
  );
  await expect(page).toHaveURL(/\/billing\/invoices$/);
  await expect(
    page.getByRole("button", { name: "Pay with Paystack" }),
  ).toBeEnabled();
});

test("a gateway outage permits a deliberate retry", async ({ page }) => {
  const calls = await billingFixture(page, { gatewayUnavailable: true });
  await page.goto("/billing/invoices");
  await page.getByRole("button", { name: "Pay with Paystack" }).click();
  await expect(page.locator("main").getByRole("alert")).toBeVisible();
  await page.getByRole("button", { name: "Pay with Paystack" }).click();
  await expect(
    page.getByRole("button", { name: "Pay with Paystack" }),
  ).toBeEnabled();
  expect(calls.checkout).toEqual([
    { provider: "paystack" },
    { provider: "paystack" },
  ]);
});

test("users without billing management permission can inspect but cannot pay", async ({
  page,
}) => {
  await billingFixture(page, { canManage: false });
  await page.goto("/billing/invoices");
  await expect(page.locator("article")).toContainText("issued · test-plan");
  await expect(page.getByRole("button", { name: /Pay with/ })).toHaveCount(0);
  await page.getByRole("button", { name: "Details", exact: true }).click();
  await expect(
    page.getByRole("region", { name: "Invoice breakdown" }),
  ).toContainText("Monthly subscription");
});

test("a pending payment can be independently checked without another checkout", async ({
  page,
}) => {
  const calls = await billingFixture(page, { pending: true });
  await page.goto("/billing/invoices");
  await page.getByRole("button", { name: "Check payment" }).click();
  await expect(page.locator("article")).toContainText("paid · test-plan");
  expect(calls.checkout).toEqual([]);
  expect(calls.verification).toBe(1);
});
