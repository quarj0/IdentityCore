import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  testMatch: "platform-admin-accessibility.spec.ts",
  fullyParallel: false,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? "github" : "list",
  use: {
    baseURL: "http://127.0.0.1:3004",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
    {
      name: "webkit",
      use: { ...devices["Desktop Safari"] },
    },
  ],
  webServer: {
    command:
      "pnpm --dir .. --filter platform-admin build && PORT=3004 NEXT_PUBLIC_API_ORIGIN=http://localhost:8000 pnpm --dir .. --filter platform-admin start",
    url: "http://127.0.0.1:3004",
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
});
