"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { toast } from "sonner";
import {
  ArrowRight,
  BookOpen,
  Clock,
  Flame,
  GitFork,
  GraduationCap,
  LayoutGrid,
  RefreshCcw,
  Route,
  Search,
  Sparkles,
} from "lucide-react";

import { WorkspacePageHeader } from "@/components/WorkspacePageHeader";
import { GuideCard } from "@/components/curriculum/GuideCard";
import { SkillTree } from "@/components/curriculum/SkillTree";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useToken } from "@/hooks/useToken";
import { apiFetch } from "@/lib/api";
import {
  buildLearningTaskHref,
  formatLearningMinutes,
  formatLearningProgramSignals,
  formatLearningSeconds,
  learningProgramStatusLabels,
  learningTaskLabels,
  recommendationLabels,
} from "@/lib/curriculum";
import type { Guide, LearningStats, LearningToday } from "@/types/curriculum";

type CategoryFilter = string | "all";
type SortMode = "alpha" | "progress" | "difficulty" | "recommended";
type LearnView = "grid" | "tree";

const categoryLabels: Record<string, string> = {
  all: "All",
  science: "Science",
  humanities: "Humanities",
  business: "Business",
  technology: "Technology",
  industry: "Industry",
  social_science: "Social Science",
  professional: "Professional",
};

const difficultyOrder: Record<string, number> = {
  introductory: 0,
  intermediate: 1,
  advanced: 2,
};

export default function LearnPage() {
  const token = useToken();
  const searchParams = useSearchParams();
  const [guides, setGuides] = useState<Guide[]>([]);
  const [stats, setStats] = useState<LearningStats | null>(null);
  const [today, setToday] = useState<LearningToday | null>(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState<CategoryFilter>("all");
  const [sort, setSort] = useState<SortMode>("recommended");
  const [activeView, setActiveView] = useState<LearnView>(
    searchParams.get("view") === "tree" ? "tree" : "grid",
  );

  const selectedProgramId = searchParams.get("program");

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

  useEffect(() => {
    setActiveView(searchParams.get("view") === "tree" ? "tree" : "grid");
  }, [searchParams]);

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

  const categories = useMemo(() => {
    const cats = new Set(guides.map((g) => g.category));
    return ["all", ...Array.from(cats).sort()];
  }, [guides]);

  const filtered = useMemo(() => {
    let result = guides;
    if (category !== "all") {
      result = result.filter((g) => g.category === category);
    }
    if (search.trim()) {
      const q = search.toLowerCase();
      result = result.filter((g) => g.title.toLowerCase().includes(q));
    }
    return [...result].sort((a, b) => {
      switch (sort) {
        case "alpha":
          return a.title.localeCompare(b.title);
        case "progress":
          return (b.progress_pct ?? 0) - (a.progress_pct ?? 0);
        case "difficulty":
          return (
            (difficultyOrder[a.difficulty] ?? 1) -
            (difficultyOrder[b.difficulty] ?? 1)
          );
        case "recommended":
        default:
          if (a.enrolled && !b.enrolled) return -1;
          if (!a.enrolled && b.enrolled) return 1;
          if ((a.progress_pct ?? 0) !== (b.progress_pct ?? 0)) {
            return (b.progress_pct ?? 0) - (a.progress_pct ?? 0);
          }
          return a.title.localeCompare(b.title);
      }
    });
  }, [guides, category, search, sort]);

  const primaryTask = today?.tasks[0] ?? null;
  const secondaryTasks = today?.tasks.slice(1, 4) ?? [];
  const primarySignals = primaryTask?.signals?.slice(0, 3) ?? [];

  const statsCards = stats
    ? [
        {
          icon: GraduationCap,
          label: "Enrolled",
          value: `${stats.guides_enrolled}`,
        },
        {
          icon: BookOpen,
          label: "Chapters",
          value: `${stats.chapters_completed}/${stats.total_chapters}`,
        },
        {
          icon: Clock,
          label: "Reading",
          value: formatLearningSeconds(stats.total_reading_time_seconds),
        },
        {
          icon: Flame,
          label: "Streak",
          value: `${stats.current_streak_days}d`,
        },
      ]
    : [];

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-4 md:p-6">
      <WorkspacePageHeader
        title="Learn"
        description="Daily learning workflow centered on today’s queue, program paths, and applied practice."
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

      <section className="space-y-3">
        <div className="flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-primary" />
          <h2 className="text-lg font-semibold">Today in Learn</h2>
        </div>

        <div className="grid gap-4 lg:grid-cols-[minmax(0,1.6fr)_minmax(0,1fr)]">
          <Card className="border-primary/15 bg-card/80">
            <CardHeader className="space-y-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="space-y-1">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                    Daily queue
                  </p>
                  <CardTitle className="text-2xl">
                    {today?.headline ?? "Today in Learn"}
                  </CardTitle>
                  <p className="text-sm text-muted-foreground">
                    {today?.summary ??
                      "Learn now starts from the work that matters today, not from a catalog-first view."}
                  </p>
                </div>
                {stats && (
                  <Badge variant="secondary" className="text-xs">
                    {stats.reviews_due} review
                    {stats.reviews_due === 1 ? "" : "s"} due
                  </Badge>
                )}
              </div>

              {primaryTask ? (
                <div className="rounded-2xl border bg-background/80 p-5">
                  <div className="mb-3 flex flex-wrap items-center gap-2">
                    <Badge variant="outline" className="text-[10px]">
                      {learningTaskLabels[primaryTask.task_type]}
                    </Badge>
                    {primaryTask.recommendation_type ? (
                      <Badge variant="secondary" className="text-[10px]">
                        {recommendationLabels[primaryTask.recommendation_type]}
                      </Badge>
                    ) : null}
                    <Badge variant="outline" className="text-[10px]">
                      {formatLearningMinutes(primaryTask.estimate_minutes)}
                    </Badge>
                  </div>

                  <div className="space-y-3">
                    <div className="space-y-1">
                      <p className="text-xl font-semibold">
                        {primaryTask.title}
                      </p>
                      {primaryTask.guide_title ? (
                        <p className="text-xs text-muted-foreground">
                          {primaryTask.guide_title}
                        </p>
                      ) : null}
                      <p className="text-sm text-muted-foreground">
                        {primaryTask.detail}
                      </p>
                    </div>

                    {primarySignals.length > 0 ? (
                      <div className="grid gap-2 sm:grid-cols-3">
                        {primarySignals.map((signal) => (
                          <div
                            key={`${signal.kind}-${signal.label}`}
                            className="rounded-xl border bg-background/70 p-3"
                          >
                            <p className="text-sm font-medium">
                              {signal.label}
                            </p>
                            <p className="mt-1 text-xs text-muted-foreground">
                              {signal.detail}
                            </p>
                          </div>
                        ))}
                      </div>
                    ) : null}

                    {primaryTask.matched_programs?.length ? (
                      <div className="flex flex-wrap gap-1.5">
                        {primaryTask.matched_programs.map((program) => (
                          <Badge
                            key={program.id}
                            variant="outline"
                            className="text-[10px]"
                            style={{
                              borderColor: program.color,
                              color: program.color,
                            }}
                          >
                            {program.title}
                          </Badge>
                        ))}
                      </div>
                    ) : null}

                    <div className="flex flex-wrap gap-2">
                      <Button asChild>
                        <Link href={buildLearningTaskHref(primaryTask)}>
                          {primaryTask.cta_label}
                          <ArrowRight className="ml-1.5 h-3.5 w-3.5" />
                        </Link>
                      </Button>
                      <Button variant="outline" asChild>
                        <Link href="/learn/review">Open reviews</Link>
                      </Button>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="rounded-2xl border border-dashed p-6">
                  <p className="text-sm text-muted-foreground">
                    No task is queued yet. Start with a program path or open the
                    library below.
                  </p>
                </div>
              )}
            </CardHeader>
          </Card>

          <div className="space-y-4">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base">Queue</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {secondaryTasks.length > 0 ? (
                  secondaryTasks.map((task) => (
                    <div
                      key={task.id}
                      className="rounded-xl border bg-background/70 p-3"
                    >
                      <div className="mb-2 flex flex-wrap items-center gap-2">
                        <Badge variant="outline" className="text-[10px]">
                          {learningTaskLabels[task.task_type]}
                        </Badge>
                        <Badge variant="secondary" className="text-[10px]">
                          {formatLearningMinutes(task.estimate_minutes)}
                        </Badge>
                      </div>
                      <p className="text-sm font-medium">{task.title}</p>
                      <p className="mt-1 text-xs text-muted-foreground">
                        {task.detail}
                      </p>
                      <Button
                        size="sm"
                        variant="ghost"
                        className="mt-3 px-0"
                        asChild
                      >
                        <Link href={buildLearningTaskHref(task)}>
                          {task.cta_label}
                          <ArrowRight className="ml-1 h-3 w-3" />
                        </Link>
                      </Button>
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-muted-foreground">
                    Secondary tasks will appear here once you enroll, review, or
                    unlock more guides.
                  </p>
                )}
              </CardContent>
            </Card>

            {statsCards.length > 0 ? (
              <div className="grid grid-cols-2 gap-3">
                {statsCards.map(({ icon: Icon, label, value }) => (
                  <Card key={label}>
                    <CardContent className="flex items-center gap-3 p-4">
                      <Icon className="h-4 w-4 text-primary" />
                      <div>
                        <p className="text-lg font-semibold">{value}</p>
                        <p className="text-[11px] text-muted-foreground">
                          {label}
                        </p>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : null}
          </div>
        </div>
      </section>

      <section className="space-y-3">
        <div className="flex items-center gap-2">
          <Route className="h-4 w-4 text-primary" />
          <h2 className="text-lg font-semibold">Program paths</h2>
        </div>
        <p className="text-sm text-muted-foreground">
          Programs are the primary framing now: outcomes first, reusable guides
          underneath, applied modules at the edge.
        </p>

        {today?.focus_programs?.length ? (
          <div className="grid gap-4 lg:grid-cols-3">
            {today.focus_programs.map((program) => {
              const programSignals = formatLearningProgramSignals(program);

              return (
                <Card key={program.id} className="border-primary/10">
                  <CardHeader className="space-y-3 pb-3">
                    <div className="flex flex-wrap items-center gap-2">
                      <Badge
                        variant="outline"
                        className="text-[10px]"
                        style={{
                          borderColor: program.color,
                          color: program.color,
                        }}
                      >
                        {learningProgramStatusLabels[program.status]}
                      </Badge>
                      <Badge variant="secondary" className="text-[10px]">
                        {program.completed_guide_count}/
                        {program.total_guide_count} complete
                      </Badge>
                    </div>
                    <div className="space-y-1">
                      <CardTitle className="text-lg">{program.title}</CardTitle>
                      <p className="text-sm text-muted-foreground">
                        {program.description}
                      </p>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div className="rounded-xl border bg-background/70 p-3">
                        <p className="text-[11px] uppercase tracking-[0.14em] text-muted-foreground">
                          In progress
                        </p>
                        <p className="mt-1 text-lg font-semibold">
                          {program.in_progress_guide_count}
                        </p>
                      </div>
                      <div className="rounded-xl border bg-background/70 p-3">
                        <p className="text-[11px] uppercase tracking-[0.14em] text-muted-foreground">
                          Ready
                        </p>
                        <p className="mt-1 text-lg font-semibold">
                          {program.ready_guide_count}
                        </p>
                      </div>
                    </div>

                    {programSignals.length > 0 ? (
                      <div className="space-y-2">
                        <p className="text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground">
                          Watch now
                        </p>
                        <div className="flex flex-wrap gap-1.5">
                          {programSignals.map((signal) => (
                            <Badge
                              key={signal}
                              variant="outline"
                              className="text-[10px]"
                            >
                              {signal}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    ) : null}

                    <div className="space-y-2">
                      <p className="text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground">
                        Outcomes
                      </p>
                      <div className="flex flex-wrap gap-1.5">
                        {program.outcomes.slice(0, 3).map((outcome) => (
                          <Badge
                            key={outcome}
                            variant="secondary"
                            className="text-[10px]"
                          >
                            {outcome}
                          </Badge>
                        ))}
                      </div>
                    </div>

                    <Button variant="outline" asChild>
                      <Link href={`/learn?view=tree&program=${program.id}`}>
                        Open path
                        <ArrowRight className="ml-1.5 h-3.5 w-3.5" />
                      </Link>
                    </Button>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        ) : (
          <Card>
            <CardContent className="p-6 text-sm text-muted-foreground">
              Program recommendations will appear here once your curriculum
              profile and progress have more signal.
            </CardContent>
          </Card>
        )}
      </section>

      <section className="space-y-4">
        <div className="space-y-1">
          <h2 className="text-lg font-semibold">Library and map</h2>
          <p className="text-sm text-muted-foreground">
            Browse the full guide library or switch to the graph view when you
            want to inspect the underlying curriculum.
          </p>
        </div>

        <Tabs
          value={activeView}
          onValueChange={(value) => setActiveView(value as LearnView)}
        >
          <TabsList variant="line">
            <TabsTrigger value="grid">
              <LayoutGrid className="mr-1.5 h-3.5 w-3.5" />
              Grid
            </TabsTrigger>
            <TabsTrigger value="tree">
              <GitFork className="mr-1.5 h-3.5 w-3.5" />
              Tree
            </TabsTrigger>
          </TabsList>

          <TabsContent value="grid" className="space-y-4">
            <div className="flex flex-wrap items-center gap-2">
              <div className="relative min-w-[200px] max-w-sm flex-1">
                <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search guides..."
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  className="h-9 pl-9 text-sm"
                />
              </div>
              <div className="flex flex-wrap gap-1">
                {categories.map((cat) => (
                  <Badge
                    key={cat}
                    variant={category === cat ? "default" : "outline"}
                    className="cursor-pointer text-xs"
                    onClick={() => setCategory(cat)}
                  >
                    {categoryLabels[cat] ?? cat}
                  </Badge>
                ))}
              </div>
              <select
                value={sort}
                onChange={(event) => setSort(event.target.value as SortMode)}
                className="h-9 rounded-md border bg-background px-2 text-xs"
              >
                <option value="recommended">Recommended</option>
                <option value="alpha">A-Z</option>
                <option value="progress">Progress</option>
                <option value="difficulty">Difficulty</option>
              </select>
            </div>

            {loading ? (
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {Array.from({ length: 6 }).map((_, i) => (
                  <Card key={i} className="animate-pulse">
                    <CardHeader className="pb-2">
                      <div className="h-5 w-3/4 rounded bg-muted" />
                    </CardHeader>
                    <CardContent>
                      <div className="h-3 w-1/2 rounded bg-muted" />
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : filtered.length === 0 ? (
              <div className="rounded-lg border border-dashed p-8 text-center">
                <GraduationCap className="mx-auto h-10 w-10 text-muted-foreground/40" />
                <p className="mt-2 text-sm text-muted-foreground">
                  No guides found
                </p>
                <Button
                  size="sm"
                  variant="outline"
                  className="mt-3"
                  onClick={handleSync}
                >
                  Sync content
                </Button>
              </div>
            ) : (
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {filtered.map((guide) => (
                  <GuideCard key={guide.id} guide={guide} />
                ))}
              </div>
            )}
          </TabsContent>

          <TabsContent value="tree">
            <SkillTree
              key={selectedProgramId ?? "all-programs"}
              initialSelectedProgramId={selectedProgramId}
            />
          </TabsContent>
        </Tabs>
      </section>
    </div>
  );
}
