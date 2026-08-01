import { defineConfig, devices } from "@playwright/test";

// Snap-packaged editors can leak GTK libraries built against an older glibc
// into WebKit's child processes, causing navigation to fail before page load.
for (const variable of ["GIO_MODULE_DIR", "GTK_PATH"]) {
  if (process.env[variable]?.includes("/snap/")) {
    delete process.env[variable];
  }
}

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? "github" : "list",
  use: {
    baseURL: "http://127.0.0.1:3002",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
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
    {
      name: "mobile-chrome",
      use: { ...devices["Pixel 7"] },
    },
    {
      name: "mobile-safari",
      use: { ...devices["iPhone 15"] },
    },
  ],
  webServer: {
    command:
      "API_ORIGIN=https://api.example.test DEPLOYMENT_VERSION=e2e pnpm build && API_ORIGIN=https://api.example.test DEPLOYMENT_VERSION=e2e pnpm start:standalone",
    url: "http://127.0.0.1:3002",
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
});
