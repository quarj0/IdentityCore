import { defineConfig, devices } from "@playwright/test";
export default defineConfig({
  testDir: "./e2e",
  testMatch: "dashboard-*.spec.ts",
  fullyParallel: false,
  retries: process.env.CI ? 1 : 0,
  use: { baseURL: "http://127.0.0.1:3005", trace: "retain-on-failure" },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: {
    env: {
      PUBLIC_ASSET_URL_BASE: "https://assets.example.test/public",
      FRONTEND_ASSET_ORIGINS: "https://cdn.example.test",
      FRONTEND_UPLOAD_ORIGINS: "https://bucket.storage.example.test",
    },
    command:
      "cd ../dashboard && NEXT_PUBLIC_API_ORIGIN=https://api.example.test NEXT_PUBLIC_DASHBOARD_URL=http://127.0.0.1:3005 node node_modules/next/dist/bin/next build --webpack && PORT=3005 NEXT_PUBLIC_API_ORIGIN=https://api.example.test NEXT_PUBLIC_DASHBOARD_URL=http://127.0.0.1:3005 node node_modules/next/dist/bin/next start",
    url: "http://127.0.0.1:3005",
    reuseExistingServer: false,
    timeout: 180_000,
  },
});
