import { createRequire } from "node:module";
import { expect, type Page } from "@playwright/test";

const require = createRequire(import.meta.url);

type AxeViolation = {
  id: string;
  impact: string | null;
  help: string;
  nodes: Array<{ target: unknown; failureSummary?: string }>;
};

export async function expectNoCriticalA11yViolations(page: Page) {
  await page.addScriptTag({ path: require.resolve("axe-core/axe.min.js") });
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
        values: ["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"],
      },
    });
    return result.violations.filter(
      (violation) =>
        violation.impact === "serious" || violation.impact === "critical",
    );
  });

  expect(violations).toEqual([]);
}

export async function focusByTab(page: Page, accessibleName: string) {
  for (let attempt = 0; attempt < 40; attempt += 1) {
    await page.keyboard.press("Tab");
    const name = await page.evaluate(() => {
      const element = document.activeElement;
      if (!(element instanceof HTMLElement)) return "";
      return (
        element.getAttribute("aria-label") ||
        element.getAttribute("title") ||
        element.textContent ||
        ""
      ).trim();
    });
    if (name.includes(accessibleName)) return;
  }
  throw new Error(`Could not reach ${accessibleName} with the keyboard.`);
}
