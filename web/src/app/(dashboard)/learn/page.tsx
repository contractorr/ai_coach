"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { toast } from "sonner";
import {
  BookOpen,
  Clock,
  GraduationCap,
  RefreshCcw,
  Search,
  Flame,
  ArrowRight,
  LayoutGrid,
  GitFork,
} from "lucide-react";
import { WorkspacePageHeader } from "@/components/WorkspacePageHeader";
import { useToken } from "@/hooks/useToken";
import { apiFetch } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { GuideCard } from "@/components/curriculum/GuideCard";
import { SkillTree } from "@/components/curriculum/SkillTree";
import type { Guide, LearningStats, NextRecommendation } from "@/types/curriculum";

type CategoryFilter = string | "all";
type SortMode = "alpha" | "progress" | "difficulty" | "recommended";

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
  const [guides, setGuides] = useState<Guide[]>([]);
  const [stats, setStats] = useState<LearningStats | null>(null);
  const [next, setNext] = useState<NextRecommendation | null>(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState<CategoryFilter>("all");
  const [sort, setSort] = useState<SortMode>("recommended");

  const loadData = async () => {
    if (!token) return;
    setLoading(true);
    try {
      const [guidesData, statsData, nextData] = await Promise.all([
        apiFetch<Guide[]>("/api/v1/curriculum/guides", {}, token),
        apiFetch<LearningStats>("/api/v1/curriculum/stats", {}, token),
        apiFetch<NextRecommendation>("/api/v1/curriculum/next", {}, token),
      ]);
      setGuides(guidesData);
      setStats(statsData);
      setNext(nextData);
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [token]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleSync = async () => {
    if (!token) return;
    setSyncing(true);
    try {
      const result = await apiFetch<{ synced_guides: number; message?: string }>(
        "/api/v1/curriculum/sync",
        { method: "POST" },
        token
      );
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
    // Sort
    result = [...result].sort((a, b) => {
      switch (sort) {
        case "alpha":
          return a.title.localeCompare(b.title);
        case "progress":
          return (b.progress_pct ?? 0) - (a.progress_pct ?? 0);
        case "difficulty":
          return (difficultyOrder[a.difficulty] ?? 1) - (difficultyOrder[b.difficulty] ?? 1);
        case "recommended":
        default:
          // Enrolled first, then by progress, then alphabetical
          if (a.enrolled && !b.enrolled) return -1;
          if (!a.enrolled && b.enrolled) return 1;
          if ((a.progress_pct ?? 0) !== (b.progress_pct ?? 0))
            return (b.progress_pct ?? 0) - (a.progress_pct ?? 0);
          return a.title.localeCompare(b.title);
      }
    });
    return result;
  }, [guides, category, search, sort]);

  const formatTime = (seconds: number) => {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    return h > 0 ? `${h}h ${m}m` : `${m}m`;
  };

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-4 md:p-6">
      <WorkspacePageHeader
        title="Learn"
        description="Structured guides with spaced repetition and active recall testing."
        eyebrow="Curriculum"
        actions={
          <Button size="sm" variant="outline" onClick={handleSync} disabled={syncing}>
            <RefreshCcw className={`mr-1.5 h-3.5 w-3.5 ${syncing ? "animate-spin" : ""}`} />
            Sync
          </Button>
        }
      />

      {/* Stats row */}
      {stats && (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <Card>
            <CardContent className="flex items-center gap-3 p-4">
              <GraduationCap className="h-5 w-5 text-primary" />
              <div>
                <p className="text-lg font-semibold">{stats.guides_enrolled}</p>
                <p className="text-[11px] text-muted-foreground">Enrolled</p>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="flex items-center gap-3 p-4">
              <BookOpen className="h-5 w-5 text-primary" />
              <div>
                <p className="text-lg font-semibold">
                  {stats.chapters_completed}/{stats.total_chapters}
                </p>
                <p className="text-[11px] text-muted-foreground">Chapters</p>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="flex items-center gap-3 p-4">
              <Clock className="h-5 w-5 text-primary" />
              <div>
                <p className="text-lg font-semibold">
                  {formatTime(stats.total_reading_time_seconds)}
                </p>
                <p className="text-[11px] text-muted-foreground">Reading</p>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="flex items-center gap-3 p-4">
              <Flame className="h-5 w-5 text-orange-500" />
              <div>
                <p className="text-lg font-semibold">{stats.current_streak_days}d</p>
                <p className="text-[11px] text-muted-foreground">Streak</p>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Continue reading + Reviews due */}
      <div className="grid gap-3 sm:grid-cols-2">
        {next?.chapter && (
          <Link href={`/learn/${next.guide_id}/${next.chapter.id.split("/").pop()}`}>
            <Card className="transition-colors hover:border-primary/40">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Continue reading
                </CardTitle>
              </CardHeader>
              <CardContent className="flex items-center justify-between">
                <div>
                  <p className="font-medium">{next.chapter.title}</p>
                  <p className="text-xs text-muted-foreground">{next.guide_title}</p>
                </div>
                <ArrowRight className="h-4 w-4 text-muted-foreground" />
              </CardContent>
            </Card>
          </Link>
        )}
        {stats && stats.reviews_due > 0 && (
          <Link href="/learn/review">
            <Card className="transition-colors hover:border-primary/40">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Reviews due
                </CardTitle>
              </CardHeader>
              <CardContent className="flex items-center justify-between">
                <div>
                  <p className="font-medium">{stats.reviews_due} items</p>
                  <p className="text-xs text-muted-foreground">
                    Spaced repetition session ready
                  </p>
                </div>
                <ArrowRight className="h-4 w-4 text-muted-foreground" />
              </CardContent>
            </Card>
          </Link>
        )}
      </div>

      <Tabs defaultValue="grid">
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
          {/* Filters */}
          <div className="flex flex-wrap items-center gap-2">
            <div className="relative flex-1 min-w-[200px] max-w-sm">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search guides..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9 h-9 text-sm"
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
              onChange={(e) => setSort(e.target.value as SortMode)}
              className="h-9 rounded-md border bg-background px-2 text-xs"
            >
              <option value="recommended">Recommended</option>
              <option value="alpha">A-Z</option>
              <option value="progress">Progress</option>
              <option value="difficulty">Difficulty</option>
            </select>
          </div>

          {/* Guide grid */}
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
              <p className="mt-2 text-sm text-muted-foreground">No guides found</p>
              <Button size="sm" variant="outline" className="mt-3" onClick={handleSync}>
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
          <SkillTree />
        </TabsContent>
      </Tabs>
    </div>
  );
}
