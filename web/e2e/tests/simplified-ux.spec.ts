import { expect, test } from "@playwright/test";
import type { Page } from "@playwright/test";
import { installApiMocks } from "../fixtures/api-mocks";

const HOME_SUGGESTIONS = [
  {
    kind: "goal_at_risk",
    title: "Review stewardship launch plan",
    description: "A quick check-in will keep the launch work moving.",
    action: "Open goals",
    priority: 82,
    why_now: [],
    payload: {},
  },
];

const GOALS = [
  {
    path: "goals/stewardship-launch",
    title: "Stewardship launch",
    status: "active",
    created: "2026-03-20T09:00:00Z",
    last_checked: "2026-03-27T09:00:00Z",
    check_in_days: 7,
    days_since_check: 2,
    is_stale: false,
    milestones: [
      {
        title: "Ship simplified dashboard",
        completed: false,
      },
    ],
  },
];

const GOAL_PROGRESS = {
  percent: 25,
  completed: 1,
  total: 4,
  milestones: [
    {
      title: "Ship simplified dashboard",
      completed: false,
    },
  ],
};

const WATCHLIST = [
  {
    id: "watch-1",
    label: "Vertical AI agents",
    kind: "theme",
    aliases: [],
    why: "Track the category for product positioning changes.",
    priority: "high",
    tags: [],
    goal: "",
    time_horizon: "",
    source_preferences: [],
    domain: "",
    github_org: "",
    ticker: "",
    topics: [],
    geographies: [],
    linked_dossier_ids: [],
    created_at: "2026-03-20T09:00:00Z",
    updated_at: "2026-03-29T09:00:00Z",
  },
];

const REPORT_LIST = [
  {
    id: "report-fintech",
    title: "Fintech landscape overview",
    report_type: "overview",
    status: "ready",
    collection: "Industries",
    preview: "A concise overview of major fintech segments and current shifts.",
    source_kind: "generated",
  },
];

const REPORT_DETAIL = {
  id: "report-fintech",
  title: "Fintech landscape overview",
  report_type: "overview",
  status: "ready",
  collection: "Industries",
  prompt: "Summarize the current fintech landscape.",
  content: "# Fintech landscape overview\n\nPayments, infrastructure, and lending remain the main clusters.",
  updated: "2026-03-29T09:00:00Z",
  last_generated_at: "2026-03-29T08:30:00Z",
  source_kind: "generated",
  has_attachment: false,
  file_name: null,
  file_size: null,
  mime_type: null,
};

const SETTINGS = {
  llm_provider: "openai",
  llm_model: "gpt-5.2",
  llm_council_enabled: false,
  llm_council_ready: false,
  llm_provider_keys: [
    {
      provider: "openai",
      configured: true,
      hint: "sk-...1234",
      council_eligible: true,
    },
  ],
  llm_custom_providers: [],
  llm_api_key_set: true,
  llm_api_key_hint: "sk-...1234",
  using_shared_key: false,
  has_own_key: true,
  has_profile: true,
  tavily_api_key_set: false,
  tavily_api_key_hint: null,
  github_token_set: false,
  github_token_hint: null,
  eventbrite_token_set: false,
  feature_extended_thinking: false,
  feature_memory_enabled: true,
  feature_threads_enabled: true,
  feature_recommendations_enabled: true,
  feature_research_enabled: true,
  feature_entity_extraction_enabled: true,
  feature_trending_radar_enabled: true,
  feature_heartbeat_enabled: false,
  feature_company_movement_enabled: true,
  feature_hiring_signals_enabled: true,
  feature_regulatory_signals_enabled: true,
};

const PROFILE = {
  current_role: "Product lead",
  career_stage: "senior",
  skills: [],
  interests: ["product strategy"],
  aspirations: "Build a calmer personal intelligence product.",
  location: "London",
  languages_frameworks: [],
  learning_style: "concise",
  weekly_hours_available: 5,
  goals_short_term: "Ship the simplified product pass.",
  goals_long_term: "Build a trusted personal intelligence brand.",
  industries_watching: ["AI"],
  technologies_watching: ["agents"],
  constraints: {},
  fears_risks: [],
  active_projects: ["StewardMe simplification"],
  updated_at: "2026-03-29T09:00:00Z",
  summary: "Product lead focused on simplifying StewardMe.",
  is_stale: false,
};

const USAGE = {
  days: 30,
  total_queries: 0,
  total_estimated_cost_usd: 0,
  by_model: [],
};

const MEMORY_STATS = {
  total_active: 0,
  total_superseded: 0,
  by_category: {},
};

async function installDashboardMocks(page: Page) {
  await installApiMocks(page);

  await page.route("**/api/v1/user/me", (route) =>
    route.fulfill({ json: { name: "Junior Dev", email: "junior@example.com" } }),
  );
  await page.route("**/api/v1/suggestions?limit=3", (route) =>
    route.fulfill({ json: HOME_SUGGESTIONS }),
  );
  await page.route("**/api/v1/suggestions?limit=20", (route) =>
    route.fulfill({ json: [] }),
  );
  await page.route("**/api/v1/goals?include_inactive=true", (route) =>
    route.fulfill({ json: GOALS }),
  );
  await page.route("**/api/v1/goals/*/progress", (route) =>
    route.fulfill({ json: GOAL_PROGRESS }),
  );
  await page.route("**/api/v1/recommendations?search=*&limit=3", (route) =>
    route.fulfill({ json: [] }),
  );
  await page.route("**/api/v1/recommendations?limit=3", (route) =>
    route.fulfill({ json: [] }),
  );
  await page.route("**/api/v1/recommendations/actions?limit=30", (route) =>
    route.fulfill({ json: [] }),
  );
  await page.route("**/api/v1/recommendations/weekly-plan", (route) =>
    route.fulfill({
      json: {
        items: [],
        used_points: 0,
        capacity_points: 0,
        remaining_points: 0,
      },
    }),
  );
  await page.route("**/api/v1/intel/watchlist", (route) =>
    route.fulfill({ json: WATCHLIST }),
  );
  await page.route("**/api/v1/threads/inbox?limit=20", (route) =>
    route.fulfill({ json: [] }),
  );
  await page.route("**/api/v1/dossier-escalations", (route) =>
    route.fulfill({ json: [] }),
  );
  await page.route("**/api/v1/research/dossiers?limit=20", (route) =>
    route.fulfill({ json: [] }),
  );
  await page.route("**/api/v1/research/dossiers?include_archived=true&limit=50", (route) =>
    route.fulfill({ json: [] }),
  );
  await page.route("**/api/v1/intel/follow-ups", (route) =>
    route.fulfill({ json: [] }),
  );
  await page.route("**/api/v1/library/reports?*", (route) =>
    route.fulfill({ json: REPORT_LIST }),
  );
  await page.route("**/api/v1/library/reports", (route) =>
    route.fulfill({ json: REPORT_LIST }),
  );
  await page.route("**/api/v1/library/reports/report-fintech", (route) =>
    route.fulfill({ json: REPORT_DETAIL }),
  );
  await page.route("**/api/v1/settings", (route) =>
    route.fulfill({ json: SETTINGS }),
  );
  await page.route("**/api/v1/profile", (route) =>
    route.fulfill({ json: PROFILE }),
  );
  await page.route("**/api/v1/intel/rss-feeds", (route) =>
    route.fulfill({ json: [] }),
  );
  await page.route("**/api/v1/settings/usage", (route) =>
    route.fulfill({ json: USAGE }),
  );
  await page.route("**/api/v1/memory/facts?limit=50", (route) =>
    route.fulfill({ json: [] }),
  );
  await page.route("**/api/v1/memory/stats", (route) =>
    route.fulfill({ json: MEMORY_STATS }),
  );
}

test.describe("Simplified dashboard UX", () => {
  test.beforeEach(async ({ page }) => {
    await installDashboardMocks(page);
  });

  test("home, goals, radar, research, and settings render the simplified surfaces", async ({ page }) => {
    await page.goto("/home");
    await expect(page).toHaveURL(/\/home$/);
    await expect(page.getByText("Capture or ask", { exact: true })).toBeVisible();
    await expect(page.getByText("Next up", { exact: true })).toBeVisible();
    await expect(page.getByRole("link", { name: "Open Guide Library" })).toBeVisible();
    await expect(page.getByText("Journal entries", { exact: true })).toHaveCount(0);

    await page.goto("/goals");
    await expect(page.getByRole("heading", { name: "Goals" })).toBeVisible({ timeout: 10_000 });
    await expect(page.getByRole("button", { name: "New goal" })).toBeVisible();
    await expect(page.getByText("Stewardship launch", { exact: true })).toBeVisible();

    await page.goto("/radar");
    await expect(page.getByRole("heading", { name: "Radar" })).toBeVisible({ timeout: 10_000 });
    await expect(page.getByRole("tab", { name: "For you" })).toBeVisible();
    await expect(page.getByRole("tab", { name: "Tracked topics" })).toBeVisible();
    await page.getByRole("tab", { name: "Tracked topics" }).click();
    await expect(page.getByText("Vertical AI agents", { exact: true })).toBeVisible();

    await page.goto("/research");
    await expect(page.getByRole("heading", { name: "Research" }).first()).toBeVisible({
      timeout: 10_000,
    });
    await expect(page.getByText("Browse research", { exact: true })).toBeVisible();
    await expect(page.getByText("Fintech landscape overview", { exact: true })).toBeVisible();
    await expect(page.getByRole("button", { name: "New report" })).toBeVisible();

    await page.goto("/settings");
    await expect(page.getByRole("heading", { name: "Settings" })).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText("Advanced controls", { exact: true })).toBeVisible();
    await expect(page.getByText("Usage", { exact: true })).not.toBeVisible();
    await page.locator("summary").filter({ hasText: "Advanced controls" }).click();
    await expect(page.getByText("Usage", { exact: true })).toBeVisible();
  });

  test("legacy aliases redirect to canonical goals and research routes", async ({ page }) => {
    await page.goto("/focus");
    await page.waitForURL("**/goals");
    await expect(page).toHaveURL(/\/goals$/);

    await page.goto("/library");
    await page.waitForURL("**/research");
    await expect(page).toHaveURL(/\/research$/);
    await expect(page.getByText("Browse research", { exact: true })).toBeVisible({ timeout: 10_000 });
  });
});
