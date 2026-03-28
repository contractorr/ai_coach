import type { Page } from "@playwright/test";

// ── Mock data (exported for assertions in specs) ──────────────────────

export const MOCK_USER = { name: "Junior Dev" };

export const MOCK_SETTINGS = {
  llm_api_key_set: true,
  using_shared_key: false,
  has_profile: true,
};

export const MOCK_GREETING = {
  text: "Welcome back. You have 3 journal entries this week.",
  return_brief: null,
  stale: false,
};

export const MOCK_GUIDE = {
  id: "python-basics",
  title: "Python Basics",
  category: "technology",
  difficulty: "introductory",
  chapter_count: 5,
  total_reading_time_minutes: 45,
  enrolled: true,
  progress_pct: 40,
  chapters_completed: 2,
};

export const MOCK_GUIDES = [
  MOCK_GUIDE,
  {
    id: "system-design",
    title: "System Design",
    category: "technology",
    difficulty: "advanced",
    chapter_count: 12,
    total_reading_time_minutes: 180,
    enrolled: false,
    progress_pct: 0,
    chapters_completed: 0,
  },
];

export const MOCK_STATS = {
  guides_enrolled: 1,
  chapters_completed: 2,
  total_chapters: 17,
  total_reading_time_seconds: 2700,
  current_streak_days: 3,
  reviews_due: 2,
};

export const MOCK_NEXT = {
  guide_id: "python-basics",
  guide_title: "Python Basics",
  chapter: { id: "python-basics/ch03", title: "Functions and Scope" },
};

export const MOCK_TREE = {
  tracks: {
    technology: {
      id: "technology",
      title: "Technology",
      description: "Technical foundations",
      color: "#2563eb",
      guide_count: 2,
      guides_completed: 0,
      average_mastery: 0,
      completion_pct: 0,
      guide_ids: ["python-basics", "system-design"],
    },
    industry: {
      id: "industry",
      title: "Industry",
      description: "Applied industry modules",
      color: "#059669",
      guide_count: 2,
      guides_completed: 0,
      average_mastery: 0,
      completion_pct: 0,
      guide_ids: ["industry-healthcare", "industry-finance"],
    },
  },
  programs: [
    {
      id: "operator-path",
      title: "Operator Path",
      audience: "Operators",
      description: "Core technical guide plus a healthcare capstone.",
      color: "#2563eb",
      outcomes: ["Build practical technical judgment"],
      guide_ids: ["python-basics"],
      applied_module_ids: ["industry-healthcare"],
    },
  ],
  nodes: [
    {
      id: "python-basics",
      title: "Python Basics",
      track: "technology",
      category: "technology",
      difficulty: "introductory",
      chapter_count: 5,
      prerequisites: [],
      is_entry_point: true,
      status: "enrolled",
      enrolled: true,
      progress_pct: 40,
      mastery_score: 25,
      chapters_completed: 2,
      chapters_total: 5,
      position: { x: 0, y: 0, depth: 0 },
    },
    {
      id: "system-design",
      title: "System Design",
      track: "technology",
      category: "technology",
      difficulty: "advanced",
      chapter_count: 12,
      prerequisites: ["python-basics"],
      is_entry_point: false,
      status: "not_started",
      enrolled: false,
      progress_pct: 0,
      mastery_score: 0,
      chapters_completed: 0,
      chapters_total: 12,
      position: { x: 0, y: 1, depth: 1 },
    },
    {
      id: "industry-healthcare",
      title: "Healthcare Industry",
      track: "industry",
      category: "industry",
      difficulty: "intermediate",
      chapter_count: 1,
      prerequisites: [],
      is_entry_point: false,
      status: "not_started",
      enrolled: false,
      progress_pct: 0,
      mastery_score: 0,
      chapters_completed: 0,
      chapters_total: 1,
      position: { x: 0, y: 0, depth: 0 },
    },
    {
      id: "industry-finance",
      title: "Finance Industry",
      track: "industry",
      category: "industry",
      difficulty: "intermediate",
      chapter_count: 1,
      prerequisites: [],
      is_entry_point: false,
      status: "not_started",
      enrolled: false,
      progress_pct: 0,
      mastery_score: 0,
      chapters_completed: 0,
      chapters_total: 1,
      position: { x: 1, y: 0, depth: 0 },
    },
  ],
  edges: [{ source: "python-basics", target: "system-design" }],
};

export const MOCK_GUIDE_DETAIL = {
  id: "python-basics",
  title: "Python Basics",
  category: "technology",
  difficulty: "introductory",
  chapter_count: 5,
  total_reading_time_minutes: 45,
  enrolled: true,
  progress_pct: 40,
  chapters_completed: 2,
  has_glossary: false,
  enrollment_completed_at: null,
  chapters: [
    { id: "python-basics/ch01", title: "Introduction", status: "completed", reading_time_minutes: 8 },
    { id: "python-basics/ch02", title: "Variables & Types", status: "completed", reading_time_minutes: 10 },
    { id: "python-basics/ch03", title: "Functions and Scope", status: "not_started", reading_time_minutes: 12 },
    { id: "python-basics/ch04", title: "Control Flow", status: "not_started", reading_time_minutes: 8 },
    { id: "python-basics/ch05", title: "Data Structures", status: "not_started", reading_time_minutes: 7 },
  ],
};

export const MOCK_SSE_ANSWER = {
  type: "answer",
  content: "Based on your journal, I'd recommend focusing on deep work blocks in the morning.",
  conversation_id: "conv-smoke-1",
  council_used: false,
};

// ── Route installer ───────────────────────────────────────────────────

export async function installApiMocks(page: Page) {
  // Settings (onboarding gate)
  await page.route("**/api/v1/settings", (route) =>
    route.fulfill({ json: MOCK_SETTINGS }),
  );

  // User identity
  await page.route("**/api/v1/user/me", (route) =>
    route.fulfill({ json: MOCK_USER }),
  );

  // Home page
  await page.route("**/api/v1/greeting", (route) =>
    route.fulfill({ json: MOCK_GREETING }),
  );
  await page.route("**/api/v1/suggestions*", (route) =>
    route.fulfill({ json: [] }),
  );

  // Home stats
  await page.route("**/api/v1/home/stats", (route) =>
    route.fulfill({ json: { journal_entries: 12, active_goals: 3, thread_count: 5 } }),
  );

  // Advisor
  await page.route("**/api/v1/advisor/conversations", (route) => {
    if (route.request().method() === "GET") {
      return route.fulfill({ json: [] });
    }
    return route.fulfill({ json: {} });
  });

  await page.route("**/api/v1/advisor/ask/stream", (route) => {
    const sseBody = `data: ${JSON.stringify(MOCK_SSE_ANSWER)}\n\n`;
    return route.fulfill({
      status: 200,
      headers: { "Content-Type": "text/event-stream" },
      body: sseBody,
    });
  });

  // Curriculum — register detail route FIRST (more specific)
  await page.route("**/api/v1/curriculum/guides/*", (route) =>
    route.fulfill({ json: MOCK_GUIDE_DETAIL }),
  );
  // Guide list (exact path — no trailing segments)
  await page.route("**/api/v1/curriculum/guides", (route) =>
    route.fulfill({ json: MOCK_GUIDES }),
  );
  await page.route("**/api/v1/curriculum/stats", (route) =>
    route.fulfill({ json: MOCK_STATS }),
  );
  await page.route("**/api/v1/curriculum/next", (route) =>
    route.fulfill({ json: MOCK_NEXT }),
  );
  await page.route("**/api/v1/curriculum/tree", (route) =>
    route.fulfill({ json: MOCK_TREE }),
  );

  // Fire-and-forget endpoints
  await page.route("**/api/v1/page-view*", (route) =>
    route.fulfill({ status: 204, body: "" }),
  );
  await page.route("**/api/v1/pageview*", (route) =>
    route.fulfill({ status: 204, body: "" }),
  );
  await page.route("**/api/v1/engagement*", (route) =>
    route.fulfill({ status: 204, body: "" }),
  );
}
