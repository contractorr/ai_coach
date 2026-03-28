import path from "node:path";
import { defineConfig, devices } from "@playwright/test";

/** web/ directory — the Next.js project root */
const WEB_DIR = path.resolve(__dirname, "..");

const PORT = 3099;
const BASE_URL = `http://localhost:${PORT}`;

export default defineConfig({
  testDir: "tests",
  fullyParallel: false,
  workers: 1,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? "github" : "list",
  timeout: 30_000,

  use: {
    baseURL: BASE_URL,
    trace: "retain-on-failure",
  },

  projects: [
    {
      name: "auth-setup",
      testDir: "fixtures",
      testMatch: "auth.setup.ts",
    },
    {
      name: "chromium",
      use: {
        ...devices["Desktop Chrome"],
        storageState: path.join(__dirname, ".auth/user.json"),
      },
      dependencies: ["auth-setup"],
    },
  ],

  webServer: {
    command: `npx next build && npx next start -p ${PORT}`,
    cwd: WEB_DIR,
    port: PORT,
    reuseExistingServer: !process.env.CI,
    env: {
      ENABLE_TEST_AUTH: "true",
      NEXT_PUBLIC_ENABLE_TEST_AUTH: "true",
      NEXTAUTH_SECRET: "e2e-test-secret-key-at-least-32-chars",
      NEXTAUTH_URL: BASE_URL,
      NEXT_PUBLIC_API_URL: "",
    },
    timeout: 120_000,
  },
});
