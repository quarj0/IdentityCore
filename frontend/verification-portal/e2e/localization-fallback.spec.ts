import { expect, test } from "@playwright/test";

test.use({ locale: "ar-EG" });

test("Arabic root and missing pages localize server copy and theme controls", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page.locator("html")).toHaveAttribute("lang", "ar");
  await expect(page.locator("html")).toHaveAttribute("dir", "rtl");
  await expect(
    page.getByRole("heading", { name: "افتح رابط التحقق الآمن الخاص بك." }),
  ).toBeVisible();
  await expect(page.getByText("قبل البدء", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "التبديل إلى المظهر الداكن" }).click();
  await expect(
    page.getByRole("button", { name: "التبديل إلى المظهر الفاتح" }),
  ).toBeVisible();
  await page.goto("/missing-localized-page");
  await expect(
    page.getByRole("heading", { name: "لم يتم العثور على صفحة التحقق" }),
  ).toBeVisible();
  await expect(
    page.getByRole("link", { name: "العودة إلى الصفحة الرئيسية" }),
  ).toHaveAttribute("href", "/");
});

test("legacy outcome URLs cannot claim an unauthenticated result", async ({
  page,
}) => {
  for (const outcome of ["complete", "expired", "error"]) {
    await page.goto(`/verify/ses_untrusted/${outcome}`);
    await expect(
      page.getByRole("heading", { name: "التحقق غير متاح" }),
    ).toBeVisible();
    await expect(page.getByText("جلسة التحقق غير مصادق عليها.")).toBeVisible();
    await expect(
      page.getByRole("heading", { name: "Verification submitted" }),
    ).toHaveCount(0);
    await expect(
      page.getByRole("heading", {
        name: "This verification session has expired",
      }),
    ).toHaveCount(0);
  }
});
