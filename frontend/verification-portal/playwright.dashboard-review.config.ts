import { defineConfig, devices } from "@playwright/test";
import dashboard from "./playwright.dashboard.config";

export default defineConfig({
  ...dashboard,
  testMatch: "dashboard-review-followups.spec.ts",
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
    { name: "webkit", use: { ...devices["Desktop Safari"] } },
  ],
});
