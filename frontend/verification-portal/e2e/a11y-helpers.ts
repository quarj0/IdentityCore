import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { expect, type Locator, type Page } from "@playwright/test";

const require = createRequire(import.meta.url);
const axeSource = readFileSync(require.resolve("axe-core/axe.min.js"), "utf8");

type AxeViolation = {
  id: string;
  impact: string | null;
  help: string;
  nodes: Array<{ target: unknown; failureSummary?: string }>;
};

export async function expectNoCriticalA11yViolations(page: Page) {
  // Read settled control colors rather than a single interpolated animation frame.
  // Recording progress and activity indicators remain running and are scanned.
  await page.evaluate(async () => {
    await Promise.all(
      document
        .getAnimations()
        .filter((animation) => {
          if (animation.constructor.name !== "CSSTransition") return false;
          const property = (animation as CSSTransition).transitionProperty;
          return property === "color" || property.endsWith("-color");
        })
        .map((animation) => animation.finished.catch(() => undefined)),
    );
  });
  // Preserve production CSP: authorize the test script with the current response
  // nonce instead of disabling CSP for the whole browser context.
  await page.evaluate((source) => {
    if ((window as unknown as { axe?: unknown }).axe) return;
    const existing = document.querySelector<HTMLScriptElement>("script[nonce]");
    if (!existing?.nonce)
      throw new Error("Production response script nonce missing");
    const script = document.createElement("script");
    script.nonce = existing.nonce;
    script.textContent = source;
    document.head.appendChild(script);
  }, axeSource);
  const violations = await page.evaluate(async () => {
    const axe = (
      window as unknown as {
        axe: {
          run: (
            context?: unknown,
            options?: unknown,
          ) => Promise<{ violations: AxeViolation[] }>;
        };
      }
    ).axe;
    const result = await axe.run(document, {
      runOnly: {
        type: "tag",
        values: ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"],
      },
    });
    return result.violations.filter(
      (violation) =>
        violation.impact === "serious" || violation.impact === "critical",
    );
  });
  expect(violations).toEqual([]);
}

export async function focusByTab(page: Page, locator: Locator) {
  await expect(locator).toBeVisible();
  await expect(locator).toBeEnabled();
  for (let attempt = 0; attempt < 100; attempt += 1) {
    if (
      await locator.evaluate((element) => element === document.activeElement)
    ) {
      await expect(locator).toBeFocused();
      return;
    }
    await page.keyboard.press("Tab");
  }
  throw new Error(
    `Control is unreachable through sequential keyboard navigation: ${(await locator.getAttribute("aria-label")) ?? (await locator.textContent())}`,
  );
}
