import { expect, test, type Locator } from "@playwright/test";

import { localizeText, translate } from "../src/lib/i18n";

import { expectNoCriticalA11yViolations, focusByTab } from "./a11y-helpers";

import {
  image,
  sessionId,
  mockSubjectJourney,
} from "./subject-journey-fixture";

async function activateWithKeyboard(locator: Locator, key = "Enter") {
  await focusByTab(locator.page(), locator);
  await locator.page().keyboard.press(key);
}

async function activateForBrowser(
  locator: Locator,
  isMobile: boolean,
  key = "Enter",
) {
  if (isMobile) {
    // Exercise touch input on mobile projects; synthesized mouse clicks can
    // be swallowed by WebKit while a captured image changes page geometry.
    await locator.tap();
    return;
  }
  await activateWithKeyboard(locator, key);
}

for (const locale of ["en", "ar"] as const) {
  test(`critical subject journey ${locale} is accessible and operable by keyboard or touch`, async ({
    isMobile,
    page,
  }) => {
    test.slow();
    const t = (text: string) => {
      const result =
        text === "Accept and continue"
          ? translate(locale, "accept")
          : text === "Complete a live camera check"
            ? translate(locale, "livenessTitle")
            : localizeText(locale, text);
      if (locale === "ar") expect(result).toMatch(/[\u0600-\u06ff]/);
      return result;
    };

    await mockSubjectJourney(page, locale);

    await page.goto(`/verify/${sessionId}#token=accessibility-secret`);

    if (!isMobile) {
      const continueOnComputer = page.getByRole("button", {
        name: t("Continue on this computer"),
      });
      await expect(continueOnComputer).toBeVisible();
      await expectNoCriticalA11yViolations(page);
      await activateWithKeyboard(continueOnComputer);
    }

    await expect(
      page.getByRole("heading", { name: t("Review and give consent") }),
    ).toBeVisible();
    await expect(page.locator("html")).toHaveAttribute("lang", locale);
    await expect(page.locator("html")).toHaveAttribute(
      "dir",
      locale === "ar" ? "rtl" : "ltr",
    );
    await expect(
      page.getByRole("link", { name: translate(locale, "skip") }),
    ).toHaveAttribute("href", "#main-content");
    await expectNoCriticalA11yViolations(page);
    const consent = page.getByRole("checkbox");
    await activateForBrowser(consent, isMobile, "Space");
    await expect(consent).toBeChecked();
    await activateForBrowser(
      page.getByRole("button", { name: t("Accept and continue") }),
      isMobile,
    );

    await expect(
      page.getByRole("heading", {
        name: `${t("Capture your")} ${t("National ID")}`,
      }),
    ).toBeVisible();
    await expectNoCriticalA11yViolations(page);
    const upload = page.getByLabel(t("Upload image"));
    async function capture(name: string) {
      const chooser = page.waitForEvent("filechooser");
      if (isMobile) {
        await page.getByText(t("Upload image"), { exact: true }).tap();
      } else {
        await activateWithKeyboard(upload, "Enter");
      }
      await (
        await chooser
      ).setFiles({ name, mimeType: "image/png", buffer: image });
      await expect(
        page.getByRole("button", { name: t("Retake"), exact: true }),
      ).toBeVisible();
      await expectNoCriticalA11yViolations(page);
    }
    await capture("national-id-front.png");
    await activateForBrowser(
      page.getByRole("button", { name: `${t("Back")} ${t("Not captured")}` }),
      isMobile,
    );
    await capture("national-id-back.png");
    await activateForBrowser(
      page.getByRole("button", { name: t("Submit document") }),
      isMobile,
    );

    await expect(
      page.getByRole("heading", { name: t("Take a live selfie") }),
    ).toBeVisible();
    await expectNoCriticalA11yViolations(page);
    await capture("selfie.png");
    await activateForBrowser(
      page.getByRole("button", { name: t("Submit selfie") }),
      isMobile,
    );

    await expect(
      page.getByRole("heading", { name: t("Complete a live camera check") }),
    ).toBeVisible();
    await expectNoCriticalA11yViolations(page);
    for (const buttonName of [
      "Begin live camera check",
      "Enable camera",
      "Start live challenge",
      "Finish recording",
      "Submit live check",
    ]) {
      // Permit automatic completion on WebKit; other browsers also exercise
      // manual stop. Both paths must produce a usable capture.
      if (
        buttonName === "Finish recording" &&
        page.context().browser()?.browserType().name() === "webkit"
      ) {
        await expect(
          page.getByText(t("Live recording ready to submit.")),
        ).toBeVisible({ timeout: 25_000 });
        await expectNoCriticalA11yViolations(page);
        continue;
      }

      const button = page.getByRole("button", { name: t(buttonName) });
      await expect(button).toBeVisible();
      await activateForBrowser(button, isMobile);
      const nextControl: Record<string, string> = {
        "Begin live camera check": "Enable camera",
        "Enable camera": "Start live challenge",
        "Start live challenge": "Finish recording",
        "Finish recording": "Submit live check",
      };
      if (nextControl[buttonName]) {
        await expect(
          page.getByRole("button", {
            name: t(nextControl[buttonName]),
            exact: true,
          }),
        ).toBeVisible();
      } else {
        await expect(
          page.getByRole("heading", { name: t("Submitted for review") }),
        ).toBeVisible();
      }
      // Scan each mounted state, including enabled camera, recording and review.
      await expectNoCriticalA11yViolations(page);
    }

    await expect(
      page.getByRole("heading", { name: t("Submitted for review") }),
    ).toBeVisible();
    await expectNoCriticalA11yViolations(page);
    await expect(page).toHaveURL(`/verify/${sessionId}`);
  });
}
