"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { toast } from "sonner";
import { ArrowRight, RefreshCcw, RotateCcw, Search } from "lucide-react";

import { WorkspacePageHeader } from "@/components/WorkspacePageHeader";
import { GuideCard } from "@/components/curriculum/GuideCard";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useToken } from "@/hooks/useToken";
import { apiFetch } from "@/lib/api";
import {
  buildLearningTaskHref,
  formatLearningMinutes,
  learningTaskLabels,
} from "@/lib/curriculum";
import type {
  Guide,
  GuideCategory,
  LearningStats,
  LearningToday,
  LearningTodayTask,
} from "@/types/curriculum";

type GuideSortMode = "recommended" | "alphabetical";

const guideCategoryOrder: GuideCategory[] = [
  "technology",
  "business",
  "science",
  "humanities",
  "social_science",
  "professional",
  "industry",
];

const guideCategoryLabels: Record<GuideCategory, string> = {
  technology: "Technology",
  business: "Business",
  science: "Science",
  humanities: "Humanities",
  social_science: "Social science",
  professional: "Professional",
  industry: "Industry",
};

function isGuideCompleted(guide: Guide): boolean {
  if (guide.enrollment_completed_at) {
    return true;
  }
  if (
    typeof guide.chapters_total === "number" &&
    typeof guide.chapters_completed === "number" &&
    guide.chapters_total > 0 &&
    guide.chapters_completed >= guide.chapters_total
  ) {
    return true;
  }
  return (guide.progress_pct ?? 0) >= 100;
}

function getUnmetPrerequisiteCount(
  guide: Guide,
  guideLookup: Map<string, Guide>,
): number {
  return (guide.prerequisites ?? []).filter((prereqId) => {
    const prereqGuide = guideLookup.get(prereqId);
    if (!prereqGuide) {
      return false;
    }
    return !isGuideCompleted(prereqGuide);
  }).length;
}

function getRecommendedGuideRank(
  guide: Guide,
  guideLookup: Map<string, Guide>,
  recommendedGuideId: string | null,
): number {
  const progress = guide.progress_pct ?? 0;
  const isCompleted = isGuideCompleted(guide);
  const isActive = Boolean(guide.enrolled) && !isCompleted && progress < 100;
  const unmetPrerequisites = getUnmetPrerequisiteCount(guide, guideLookup);
  const prerequisiteCount = (guide.prerequisites ?? []).length;

  if (guide.id === recommendedGuideId) {
    return 0;
  }
  if (isActive) {
    return 1;
  }
  if (!isCompleted && unmetPrerequisites === 0 && prerequisiteCount > 0) {
    return 2;
  }
  if (!isCompleted && unmetPrerequisites === 0) {
    return 3;
  }
  if (!isCompleted) {
    return 4;
  }
  return 5;
}

function sortGuides(
  guides: Guide[],
  allGuides: Guide[],
  sortMode: GuideSortMode,
  recommendedGuideId: string | null,
): Guide[] {
  const guideLookup = new Map(allGuides.map((guide) => [guide.id, guide]));

  return [...guides].sort((left, right) => {
    if (sortMode === "alphabetical") {
      return left.title.localeCompare(right.title);
    }

    const leftRank = getRecommendedGuideRank(left, guideLookup, recommendedGuideId);
    const rightRank = getRecommendedGuideRank(right, guideLookup, recommendedGuideId);
    if (leftRank !== rightRank) {
      return leftRank - rightRank;
    }

    const leftUnmet = getUnmetPrerequisiteCount(left, guideLookup);
    const rightUnmet = getUnmetPrerequisiteCount(right, guideLookup);
    if (leftUnmet !== rightUnmet) {
      return leftUnmet - rightUnmet;
    }

    const leftProgress = left.progress_pct ?? 0;
    const rightProgress = right.progress_pct ?? 0;
    if (leftProgress !== rightProgress) {
      return rightProgress - leftProgress;
    }

    const leftPrerequisites = (left.prerequisites ?? []).length;
    const rightPrerequisites = (right.prerequisites ?? []).length;
    if (leftPrerequisites !== rightPrerequisites) {
      return rightPrerequisites - leftPrerequisites;
    }

    return left.title.localeCompare(right.title);
  });
}

function getReviewCount(
  task: LearningTodayTask | null,
  stats: LearningStats | null,
  today: LearningToday | null,
): number {
  if (!task) {
    return stats?.reviews_due ?? today?.reviews_due ?? 0;
  }
  return task.review_count ?? task.retry_count ?? stats?.reviews_due ?? today?.reviews_due ?? 0;
}

export default function LearnPage() {
  const token = useToken();
  const [guides, setGuides] = useState<Guide[]>([]);
  const [stats, setStats] = useState<LearningStats | null>(null);
  const [today, setToday] = useState<LearningToday | null>(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [search, setSearch] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<GuideCategory | "all">("all");
  const [sortMode, setSortMode] = useState<GuideSortMode>("recommended");

  const loadData = async () => {
    if (!token) return;
    setLoading(true);
    try {
      const [guidesData, statsData, todayData] = await Promise.all([
        apiFetch<Guide[]>("/api/v1/curriculum/guides", {}, token),
        apiFetch<LearningStats>("/api/v1/curriculum/stats", {}, token),
        apiFetch<LearningToday>("/api/v1/curriculum/today", {}, token),
      ]);
      setGuides(guidesData);
      setStats(statsData);
      setToday(todayData);
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadData();
  }, [token]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleSync = async () => {
    if (!token) return;
    setSyncing(true);
    try {
      const result = await apiFetch<{
        synced_guides: number;
        message?: string;
      }>("/api/v1/curriculum/sync", { method: "POST" }, token);
      await loadData();
      toast.success(result.message || `Synced ${result.synced_guides} guides`);
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setSyncing(false);
    }
  };

  const reviewTask =
    today?.tasks.find(
      (task) => task.task_type === "due_reviews" || task.task_type === "retry_reviews",
    ) ?? null;

  const nextUpTask =
    today?.tasks.find(
      (task) => task.task_type === "continue_chapter" || task.task_type === "start_guide",
    ) ??
    reviewTask ??
    today?.tasks.find((task) => Boolean(task.guide_id || task.chapter_id)) ??
    today?.tasks[0] ??
    null;

  const reviewCount = getReviewCount(reviewTask, stats, today);
  const inProgressCount = guides.filter(
    (guide) => (guide.progress_pct ?? 0) > 0 && (guide.progress_pct ?? 0) < 100,
  ).length;
  const recommendedGuideId = nextUpTask?.guide_id ?? today?.recommended_action?.guide_id ?? null;
  const visibleCategories = useMemo(
    () =>
      guideCategoryOrder.filter((category) =>
        guides.some((guide) => guide.category === category),
      ),
    [guides],
  );
  const visibleGuides = useMemo(() => {
    const query = search.trim().toLowerCase();
    const filtered = guides.filter((guide) => {
      const matchesCategory =
        selectedCategory === "all" || guide.category === selectedCategory;
      if (!matchesCategory) {
        return false;
      }
      if (!query) {
        return true;
      }
      const categoryLabel = guideCategoryLabels[guide.category].toLowerCase();
      return (
        guide.title.toLowerCase().includes(query) ||
        categoryLabel.includes(query)
      );
    });
    return sortGuides(filtered, guides, sortMode, recommendedGuideId);
  }, [guides, recommendedGuideId, search, selectedCategory, sortMode]);

  return (
    <div className="mx-auto max-w-6xl space-y-6 p-4 md:p-6">
      <WorkspacePageHeader
        title="Learn"
        description="Use your Guide Library to start a guide, continue the next chapter, and clear reviews when they are due."
        eyebrow="Curriculum"
        actions={
          <Button
            size="sm"
            variant="outline"
            onClick={handleSync}
            disabled={syncing}
          >
            <RefreshCcw
              className={`mr-1.5 h-3.5 w-3.5 ${syncing ? "animate-spin" : ""}`}
            />
            Sync
          </Button>
        }
      />

      <section className="grid gap-4 lg:grid-cols-[minmax(0,1.5fr)_minmax(280px,0.9fr)]">
        <Card>
          <CardHeader className="space-y-2">
            <div className="space-y-1">
              <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                Next up
              </p>
              <CardTitle className="text-2xl">
                {nextUpTask?.title ?? "Choose a guide to start learning"}
              </CardTitle>
              <CardDescription>
                {nextUpTask?.detail ??
                  "Start with one guide and move through it chapter by chapter."}
              </CardDescription>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {nextUpTask ? (
              <>
                <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                  <span className="rounded-full border px-2 py-1">
                    {learningTaskLabels[nextUpTask.task_type]}
                  </span>
                  <span>{formatLearningMinutes(nextUpTask.estimate_minutes)}</span>
                  {nextUpTask.guide_title ? <span>{nextUpTask.guide_title}</span> : null}
                </div>
                <div className="flex flex-wrap gap-2">
                  <Button asChild>
                    <Link href={buildLearningTaskHref(nextUpTask)}>
                      {nextUpTask.cta_label}
                      <ArrowRight className="ml-1.5 h-3.5 w-3.5" />
                    </Link>
                  </Button>
                  <Button variant="outline" asChild>
                    <Link href="#browse-guides">Open guide library</Link>
                  </Button>
                </div>
              </>
            ) : (
              <Button asChild>
                <Link href="#browse-guides">
                  Open guide library
                  <ArrowRight className="ml-1.5 h-3.5 w-3.5" />
                </Link>
              </Button>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="space-y-2">
            <div className="flex items-center gap-2 text-muted-foreground">
              <RotateCcw className="h-4 w-4" />
              <p className="text-[11px] font-semibold uppercase tracking-[0.18em]">
                Reviews
              </p>
            </div>
            <CardTitle>
              {reviewCount > 0
                ? `${reviewCount} review${reviewCount === 1 ? "" : "s"} due`
                : "You’re caught up"}
            </CardTitle>
            <CardDescription>
              {reviewCount > 0
                ? "Use one short review session to keep what you’ve learned fresh."
                : "New reviews will show up here after you finish more chapters."}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {reviewCount > 0 ? (
              <Button asChild>
                <Link href="/learn/review">Start review</Link>
              </Button>
            ) : (
              <Button variant="outline" asChild>
                <Link href="#browse-guides">Open guide library</Link>
              </Button>
            )}
            <p className="text-sm text-muted-foreground">
              {inProgressCount > 0
                ? `${inProgressCount} guide${inProgressCount === 1 ? "" : "s"} currently in progress.`
                : "No guides in progress yet."}
            </p>
          </CardContent>
        </Card>
      </section>

      <section id="browse-guides" className="space-y-4">
        <div className="space-y-1">
          <h2 className="text-lg font-semibold">Browse guides</h2>
          <p className="text-sm text-muted-foreground">
            Filter by topic, then use recommended order to see what to start or continue next.
          </p>
        </div>

        <div className="flex flex-col gap-4 rounded-xl border bg-card p-4">
          <div className="flex flex-col gap-4 xl:flex-row xl:items-end xl:justify-between">
            <div className="space-y-2">
              <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                Topic
              </p>
              <div className="flex flex-wrap gap-2">
                <Button
                  size="sm"
                  variant={selectedCategory === "all" ? "default" : "outline"}
                  onClick={() => setSelectedCategory("all")}
                >
                  All
                </Button>
                {visibleCategories.map((category) => (
                  <Button
                    key={category}
                    size="sm"
                    variant={selectedCategory === category ? "default" : "outline"}
                    onClick={() => setSelectedCategory(category)}
                  >
                    {guideCategoryLabels[category]}
                  </Button>
                ))}
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-[minmax(0,1fr)_220px]">
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  className="pl-9"
                  placeholder="Search guides"
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                />
              </div>

              <div className="space-y-2">
                <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                  Order
                </p>
                <Select
                  value={sortMode}
                  onValueChange={(value) => setSortMode(value as GuideSortMode)}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="recommended">Recommended order</SelectItem>
                    <SelectItem value="alphabetical">A-Z</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>

          <p className="text-sm text-muted-foreground">
            {sortMode === "recommended"
              ? "Recommended order keeps your active guide first, then guides you can start now, then later guides."
              : "Alphabetical order is useful when you already know what you want to open."}
          </p>
        </div>

        {loading ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 6 }).map((_, index) => (
              <Card key={index} className="animate-pulse">
                <CardHeader className="pb-2">
                  <div className="h-5 w-3/4 rounded bg-muted" />
                </CardHeader>
                <CardContent>
                  <div className="h-3 w-1/2 rounded bg-muted" />
                </CardContent>
              </Card>
            ))}
          </div>
        ) : visibleGuides.length === 0 ? (
          <Card>
            <CardContent className="p-6 text-sm text-muted-foreground">
              No guides match that topic or search.
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {visibleGuides.map((guide) => (
              <GuideCard key={guide.id} guide={guide} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
