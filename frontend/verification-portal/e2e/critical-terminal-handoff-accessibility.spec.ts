import { expect, test } from "@playwright/test";
import { expectNoCriticalA11yViolations, focusByTab } from "./a11y-helpers";
import { mockSubjectJourney, sessionId } from "./subject-journey-fixture";

for (const state of ["verified", "failed"] as const) {
  test(`terminal ${state} state is scanned and finish is keyboard/touch operable`, async ({
    page,
    isMobile,
    baseURL,
  }) => {
    await mockSubjectJourney(page, "en", state);
    await page.goto(`/verify/${sessionId}#token=synthetic-terminal-token`);
    if (!isMobile) {
      const local = page.getByRole("button", {
        name: "Continue on this computer",
      });
      await focusByTab(page, local);
      await page.keyboard.press("Enter");
    }
    await expect(
      page.getByRole("heading", {
        name:
          state === "verified"
            ? "Verification complete"
            : "Verification needs attention",
        exact: true,
      }),
    ).toBeVisible();
    await expectNoCriticalA11yViolations(page);
    const finish = page.getByRole("button", {
      name: "Finish and return",
      exact: true,
    });
    if (isMobile) await finish.tap();
    else {
      await focusByTab(page, finish);
      await page.keyboard.press("Enter");
    }
    await expect(page).toHaveURL(`${baseURL}/`);
  });
}

test("desktop secure QR handoff is scanned, copyable and keyboard operable while waiting", async ({
  page,
  isMobile,
}) => {
  test.skip(
    isMobile,
    "The initiating QR chooser is a desktop flow; mobile capture is scanned separately.",
  );
  await mockSubjectJourney(page, "en");
  await page.addInitScript(() => {
    Object.defineProperty(navigator, "clipboard", {
      value: {
        writeText: async (text: string) => {
          (window as unknown as { copiedLink: string }).copiedLink = text;
        },
      },
    });
  });
  await page.goto(`/verify/${sessionId}#token=synthetic-handoff-token`);
  const show = page.getByRole("button", { name: "Show secure QR code" });
  await expect(show).toBeVisible();
  await expectNoCriticalA11yViolations(page);
  await focusByTab(page, show);
  await page.keyboard.press("Enter");
  await expect(
    page.getByRole("img", { name: "Mobile handoff QR code" }).locator("svg"),
  ).toBeVisible();
  await expect(
    page.getByText("Waiting for completion on your phone", { exact: true }),
  ).toBeVisible();
  await expectNoCriticalA11yViolations(page);
  const copy = page.getByRole("button", { name: "Copy mobile link" });
  await focusByTab(page, copy);
  await page.keyboard.press("Enter");
  await expect
    .poll(() =>
      page.evaluate(
        () => (window as unknown as { copiedLink?: string }).copiedLink,
      ),
    )
    .toBe(
      `https://verify.example.test/verify/${sessionId}#handoff=synthetic-one-time-claim`,
    );
});
