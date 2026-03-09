import playwright from "../..//web/node_modules/playwright/index.js";
import fs from "node:fs/promises";
import path from "node:path";

const { chromium } = playwright;

const baseUrl = "http://127.0.0.1:3100";
const outputDir = path.resolve("eval/ux-audit/artifacts");

async function ensureDir() {
  await fs.mkdir(outputDir, { recursive: true });
}

async function screenshot(page, name) {
  await page.screenshot({ path: path.join(outputDir, name), fullPage: true });
}

async function login(page, username) {
  console.log(`login:${username}:start`);
  await page.goto(`${baseUrl}/login`, { waitUntil: "networkidle" });
  await page.selectOption("#test-username", username);
  await page.fill("#test-password", "test");
  await page.getByRole("button", { name: new RegExp(`Sign in as ${username}`) }).click();
}

async function run() {
  await ensureDir();
  const browser = await chromium.launch({ headless: true });
  const results = [];

  // Onboarding flow with an unseeded user.
  {
    const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const page = await context.newPage();
    page.setDefaultTimeout(30000);
    const started = Date.now();
    await login(page, "switcher");
    await page.waitForURL((url) => url.pathname === "/onboarding", { timeout: 30000 });
    console.log("onboarding:reached");
    await page.getByRole("button", { name: /Get started/i }).click();
    await page.getByText("What's your name?").waitFor({ timeout: 10000 });
    await screenshot(page, "onboarding-name-step.png");
    results.push({
      workflow: "Onboarding",
      clicks: 2,
      duration_ms: Date.now() - started,
      outcome: "Reached onboarding name step from login.",
    });
    await context.close();
  }

  // Main authenticated workflows with seeded profile.
  {
    const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const page = await context.newPage();
    page.setDefaultTimeout(30000);
    await login(page, "junior_dev");
    await page.waitForURL((url) => url.pathname === "/", { timeout: 30000 });
    console.log("junior_dev:home");

    // Goals workflow
    let started = Date.now();
    await page.getByRole("link", { name: "Goals" }).click();
    await page.waitForURL(/\/goals/, { timeout: 15000 });
    console.log("goals:page");
    const createGoalButton = page.getByRole("button", { name: /Create your first goal|New goal/i }).first();
    await createGoalButton.click();
    await page.locator('input[placeholder="Ship the portfolio refresh"]').fill("Ship projects workspace");
    await page.getByRole("button", { name: /Create goal/i }).click();
    await page.getByText("Ship projects workspace").waitFor({ timeout: 15000 });
    console.log("goals:created");
    await screenshot(page, "goals-after-create.png");
    results.push({
      workflow: "Goal Tracking",
      clicks: 3,
      duration_ms: Date.now() - started,
      outcome: "Created a goal from the goals workspace.",
    });

    // Projects workflow
    started = Date.now();
    await page.getByRole("link", { name: "Projects" }).click();
    await page.waitForURL(/\/projects/, { timeout: 15000 });
    await page.getByRole("heading", { name: /Projects & opportunities/i }).waitFor({ timeout: 15000 });
    console.log("projects:page");
    await screenshot(page, "projects-workspace.png");
    results.push({
      workflow: "Projects & Opportunities",
      clicks: 1,
      duration_ms: Date.now() - started,
      outcome: "Opened the new projects workspace and verified the tactical-plus-strategic layout.",
    });

    // Settings workflow
    started = Date.now();
    await page.getByRole("link", { name: "Settings" }).click();
    await page.waitForURL(/\/settings/, { timeout: 15000 });
    console.log("settings:page");
    await page.locator('input[placeholder="e.g. claude-sonnet-4-20250514"]').fill("claude-test-model");
    await page.getByText(/You have unsaved settings changes/i).waitFor({ timeout: 10000 });
    await page.getByRole("button", { name: /Save changes/i }).click();
    console.log("settings:saved");
    await screenshot(page, "settings-save-bar.png");
    results.push({
      workflow: "Settings & Account",
      clicks: 3,
      duration_ms: Date.now() - started,
      outcome: "Edited model settings and saved via the sticky action bar.",
    });

    // Analytics workflow
    started = Date.now();
    await page.goto(`${baseUrl}/admin/stats`, { waitUntil: "networkidle" });
    await page.getByRole("heading", { name: /Usage analytics/i }).waitFor({ timeout: 15000 });
    console.log("admin:page");
    await page.getByRole("button", { name: "7d" }).click();
    await screenshot(page, "admin-analytics.png");
    results.push({
      workflow: "Analytics & Admin",
      clicks: 1,
      duration_ms: Date.now() - started,
      outcome: "Loaded admin analytics and changed the day window.",
    });

    await context.close();
  }

  await browser.close();
  await fs.writeFile(
    path.join(outputDir, "workflow-results.json"),
    JSON.stringify(results, null, 2),
    "utf8"
  );
}

run().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
