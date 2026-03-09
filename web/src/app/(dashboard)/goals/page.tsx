"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import { useToken } from "@/hooks/useToken";
import {
  Archive,
  CheckCircle2,
  Circle,
  Clock3,
  Lightbulb,
  Plus,
  Search,
  Target,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { WhyNowChip } from "@/components/shared/WhyNowChip";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { apiFetch } from "@/lib/api";
import type {
  BriefingRecommendation,
  TrackedRecommendationAction,
  WeeklyPlanResponse,
} from "@/types/briefing";

interface Milestone {
  title: string;
  completed: boolean;
  completed_at?: string;
}

interface Goal {
  path: string;
  title: string;
  status: string;
  created: string;
  last_checked: string;
  check_in_days: number;
  days_since_check: number;
  is_stale: boolean;
  milestones?: Milestone[];
}

interface Progress {
  percent: number;
  completed: number;
  total: number;
  milestones: Milestone[];
}

type GoalFilter = "focus" | "stale" | "archived" | "all";

const goalSortOrder: Record<string, number> = {
  active: 0,
  paused: 1,
  completed: 2,
  abandoned: 3,
};

function formatCheckInAge(days: number) {
  if (days <= 0) return "Checked in today";
  if (days === 1) return "Last check-in: yesterday";
  return `Last check-in: ${days}d ago`;
}

function GoalSkeleton() {
  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div className="h-4 w-48 animate-pulse rounded bg-muted" />
          <div className="h-5 w-16 animate-pulse rounded bg-muted" />
        </div>
        <div className="h-3 w-32 animate-pulse rounded bg-muted" />
      </CardHeader>
    </Card>
  );
}

export default function GoalsPage() {
  const token = useToken();
  const [goals, setGoals] = useState<Goal[]>([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState({ title: "", content: "", tags: "" });
  const [creating, setCreating] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);
  const [selectedGoal, setSelectedGoal] = useState<string | null>(null);
  const [goalFilter, setGoalFilter] = useState<GoalFilter>("focus");
  const [searchQuery, setSearchQuery] = useState("");
  const [progressMap, setProgressMap] = useState<Record<string, Progress>>({});
  const [recommendationsMap, setRecommendationsMap] = useState<Record<string, BriefingRecommendation[]>>({});
  const [unanchored, setUnanchored] = useState<BriefingRecommendation[]>([]);
  const [actionItems, setActionItems] = useState<TrackedRecommendationAction[]>([]);
  const [weeklyPlan, setWeeklyPlan] = useState<WeeklyPlanResponse | null>(null);
  const [reviewNotes, setReviewNotes] = useState<Record<string, string>>({});
  const [feedbackDrafts, setFeedbackDrafts] = useState<Record<string, string>>({});
  const [feedbackRatings, setFeedbackRatings] = useState<Record<string, number>>({});
  const [savingActionId, setSavingActionId] = useState<string | null>(null);
  const [savingFeedbackId, setSavingFeedbackId] = useState<string | null>(null);
  // Per-goal input state
  const [milestoneInputs, setMilestoneInputs] = useState<Record<string, string>>({});
  const [checkInInputs, setCheckInInputs] = useState<Record<string, string>>({});

  const loadGoals = () => {
    if (!token) {
      setLoading(false);
      return;
    }
    apiFetch<Goal[]>("/api/goals?include_inactive=true", {}, token)
      .then(setGoals)
      .catch((e) => toast.error(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(loadGoals, [token]);

  // Load progress for all goals on mount
  useEffect(() => {
    if (!token || goals.length === 0) return;
    goals.forEach((g) => loadProgress(g.path));
  }, [token, goals.length]); // eslint-disable-line react-hooks/exhaustive-deps

  const loadRecommendations = async (path: string, title: string) => {
    if (!token) return;
    try {
      const recs = await apiFetch<BriefingRecommendation[]>(
        `/api/recommendations?search=${encodeURIComponent(title)}&limit=3`,
        {},
        token
      );
      setRecommendationsMap((prev) => ({ ...prev, [path]: recs }));
    } catch {
      /* no recs */
    }
  };

  const loadUnanchored = () => {
    if (!token) return;
    apiFetch<BriefingRecommendation[]>("/api/recommendations?limit=3", {}, token)
      .then(setUnanchored)
      .catch(() => {});
  };

  const loadActionItems = () => {
    if (!token) return;
    apiFetch<TrackedRecommendationAction[]>("/api/recommendations/actions?limit=30", {}, token)
      .then(setActionItems)
      .catch(() => {});
  };

  const loadWeeklyPlan = () => {
    if (!token) return;
    apiFetch<WeeklyPlanResponse>("/api/recommendations/weekly-plan", {}, token)
      .then(setWeeklyPlan)
      .catch(() => {});
  };

  useEffect(loadUnanchored, [token]);
  useEffect(loadActionItems, [token]);
  useEffect(loadWeeklyPlan, [token]);

  const refreshExecutionViews = () => {
    loadActionItems();
    loadWeeklyPlan();
    loadUnanchored();
    goals.forEach((goal) => loadRecommendations(goal.path, goal.title));
  };

  const updateRecommendationEverywhere = (updated: BriefingRecommendation) => {
    setRecommendationsMap((prev) => {
      const next: Record<string, BriefingRecommendation[]> = {};
      for (const [path, recs] of Object.entries(prev)) {
        next[path] = recs.map((rec) => (rec.id === updated.id ? updated : rec));
      }
      return next;
    });
    setUnanchored((prev) => prev.map((rec) => (rec.id === updated.id ? updated : rec)));
  };

  const loadProgress = async (path: string) => {
    if (!token) return;
    try {
      const p = await apiFetch<Progress>(
        `/api/goals/${encodeURIComponent(path)}/progress`,
        {},
        token
      );
      setProgressMap((prev) => ({ ...prev, [path]: p }));
    } catch {
      /* no progress yet */
    }
  };

  const handleCreate = async () => {
    const title = form.title.trim();
    if (!token || !title) return;
    setCreating(true);
    try {
      await apiFetch(
        "/api/goals",
        {
          method: "POST",
          body: JSON.stringify({
            title,
            content: form.content.trim(),
            tags: form.tags
              ? form.tags.split(",").map((tag) => tag.trim()).filter(Boolean)
              : undefined,
          }),
        },
        token
      );
      setForm({ title: "", content: "", tags: "" });
      setCreateOpen(false);
      toast.success("Goal created");
      loadGoals();
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setCreating(false);
    }
  };

  const handleCheckIn = async (path: string) => {
    if (!token) return;
    const notes = (checkInInputs[path] || "").trim();
    try {
      await apiFetch(
        `/api/goals/${encodeURIComponent(path)}/check-in`,
        { method: "POST", body: JSON.stringify({ notes: notes || null }) },
        token
      );
      setCheckInInputs((prev) => ({ ...prev, [path]: "" }));
      toast.success("Checked in");
      loadGoals();
      loadProgress(path);
    } catch (e) {
      toast.error((e as Error).message);
    }
  };

  const handleStatusChange = async (path: string, status: string) => {
    if (!token) return;
    try {
      await apiFetch(
        `/api/goals/${encodeURIComponent(path)}/status`,
        { method: "PUT", body: JSON.stringify({ status }) },
        token
      );
      toast.success(`Status: ${status}`);
      loadGoals();
    } catch (e) {
      toast.error((e as Error).message);
    }
  };

  const handleAddMilestone = async (path: string) => {
    const title = (milestoneInputs[path] || "").trim();
    if (!token || !title) return;
    try {
      await apiFetch(
        `/api/goals/${encodeURIComponent(path)}/milestones`,
        { method: "POST", body: JSON.stringify({ title }) },
        token
      );
      setMilestoneInputs((prev) => ({ ...prev, [path]: "" }));
      toast.success("Milestone added");
      loadProgress(path);
    } catch (e) {
      toast.error((e as Error).message);
    }
  };

  const handleCompleteMilestone = async (path: string, index: number) => {
    if (!token) return;
    try {
      await apiFetch(
        `/api/goals/${encodeURIComponent(path)}/milestones/complete`,
        { method: "POST", body: JSON.stringify({ milestone_index: index }) },
        token
      );
      toast.success("Milestone completed");
      loadProgress(path);
      loadGoals();
    } catch (e) {
      toast.error((e as Error).message);
    }
  };

  const handleCreateActionItem = async (recId: string, goal?: Goal) => {
    if (!token) return;
    setSavingActionId(recId);
    try {
      await apiFetch(
        `/api/recommendations/${encodeURIComponent(recId)}/action-item`,
        {
          method: "POST",
          body: JSON.stringify({ goal_path: goal?.path ?? null }),
        },
        token
      );
      toast.success(goal ? `Added to ${goal.title}` : "Added to weekly actions");
      refreshExecutionViews();
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setSavingActionId(null);
    }
  };

  const handleActionUpdate = async (
    recId: string,
    payload: Partial<{
      status: "accepted" | "deferred" | "blocked" | "completed" | "abandoned";
      effort: "small" | "medium" | "large";
      due_window: "today" | "this_week" | "later";
      review_notes: string;
    }>
  ) => {
    if (!token) return;
    setSavingActionId(recId);
    try {
      await apiFetch(
        `/api/recommendations/${encodeURIComponent(recId)}/action-item`,
        {
          method: "PUT",
          body: JSON.stringify(payload),
        },
        token
      );
      toast.success("Action updated");
      refreshExecutionViews();
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setSavingActionId(null);
    }
  };

  const handleSaveFeedback = async (rec: BriefingRecommendation) => {
    const rating = feedbackRatings[rec.id] ?? rec.user_rating;
    if (!token) return;
    if (!rating) {
      toast.error("Choose a rating first");
      return;
    }

    const comment = (feedbackDrafts[rec.id] ?? rec.feedback_comment ?? "").trim();
    setSavingFeedbackId(rec.id);
    try {
      const updated = await apiFetch<BriefingRecommendation>(
        `/api/recommendations/${encodeURIComponent(rec.id)}/feedback`,
        {
          method: "POST",
          body: JSON.stringify({ rating, comment: comment || null }),
        },
        token
      );
      updateRecommendationEverywhere(updated);
      setFeedbackRatings((prev) => ({ ...prev, [rec.id]: updated.user_rating ?? rating }));
      setFeedbackDrafts((prev) => ({ ...prev, [rec.id]: updated.feedback_comment ?? "" }));
      toast.success("Feedback saved");
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setSavingFeedbackId(null);
    }
  };

  const statusColor: Record<string, string> = {
    active: "default",
    paused: "secondary",
    completed: "outline",
    abandoned: "destructive",
  };

  const staleUrgency = (days: number) => {
    if (days >= 14) return "text-destructive";
    if (days >= 7) return "text-warning";
    return "";
  };

  const actionStatusColor: Record<string, "default" | "secondary" | "outline" | "destructive"> = {
    accepted: "default",
    deferred: "secondary",
    blocked: "destructive",
    completed: "outline",
    abandoned: "destructive",
  };

  const linkedActionItems = (goalPath: string) =>
    actionItems.filter((item) => item.action_item.goal_path === goalPath);

  const goalCounts = useMemo(
    () => ({
      focus: goals.filter((goal) => goal.status === "active" || goal.status === "paused").length,
      stale: goals.filter((goal) => goal.is_stale).length,
      archived: goals.filter((goal) => goal.status === "completed" || goal.status === "abandoned").length,
      all: goals.length,
    }),
    [goals]
  );

  const filteredGoals = useMemo(() => {
    const query = searchQuery.trim().toLowerCase();

    return [...goals]
      .sort((left, right) => {
        if (left.is_stale !== right.is_stale) {
          return Number(right.is_stale) - Number(left.is_stale);
        }

        const statusDiff =
          (goalSortOrder[left.status] ?? Number.MAX_SAFE_INTEGER)
          - (goalSortOrder[right.status] ?? Number.MAX_SAFE_INTEGER);
        if (statusDiff !== 0) return statusDiff;

        if (left.days_since_check !== right.days_since_check) {
          return right.days_since_check - left.days_since_check;
        }

        return right.created.localeCompare(left.created);
      })
      .filter((goal) => {
        if (goalFilter === "focus") {
          return goal.status === "active" || goal.status === "paused";
        }
        if (goalFilter === "stale") {
          return goal.is_stale;
        }
        if (goalFilter === "archived") {
          return goal.status === "completed" || goal.status === "abandoned";
        }
        return true;
      })
      .filter((goal) => {
        if (!query) return true;
        return goal.title.toLowerCase().includes(query);
      });
  }, [goalFilter, goals, searchQuery]);

  const filterOptions: Array<{
    value: GoalFilter;
    label: string;
    count: number;
  }> = [
    { value: "focus", label: "Focus", count: goalCounts.focus },
    { value: "stale", label: "Needs check-in", count: goalCounts.stale },
    { value: "archived", label: "Archived", count: goalCounts.archived },
    { value: "all", label: "All", count: goalCounts.all },
  ];

  const hasActiveFilters = goalFilter !== "focus" || searchQuery.trim().length > 0;

  const filteredEmptyState = (() => {
    if (searchQuery.trim()) {
      return {
        title: "No goals match that search",
        description: "Try a shorter keyword or reset the filters to see your full goal list.",
      };
    }

    if (goalFilter === "stale") {
      return {
        title: "Nothing needs a check-in right now",
        description: "Your stale-goal queue is clear. Keep momentum by checking in as work progresses.",
      };
    }

    if (goalFilter === "archived") {
      return {
        title: "No archived goals yet",
        description: "Completed and abandoned goals will stay here so your focus list stays clean.",
      };
    }

    return {
      title: "No focus goals yet",
      description: "Create a goal or reactivate an archived one to bring it back into your working list.",
    };
  })();

  const renderRecommendationCard = (
    rec: BriefingRecommendation,
    options?: { goal?: Goal; ctaLabel?: string; compact?: boolean }
  ) => {
    const selectedRating = feedbackRatings[rec.id] ?? rec.user_rating ?? 0;
    const comment = feedbackDrafts[rec.id] ?? rec.feedback_comment ?? "";
    const pendingFeedback = savingFeedbackId === rec.id;
    const pendingAction = savingActionId === rec.id;

    return (
      <div
        key={rec.id}
        className={`space-y-3 rounded-xl border px-4 py-3 text-sm ${
          options?.compact ? "" : "bg-card"
        }`}
      >
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0 flex-1 space-y-1">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-medium">{rec.title}</span>
              <Badge variant="secondary" className="text-xs">
                {rec.category}
              </Badge>
              {rec.action_item && (
                <Badge
                  variant={actionStatusColor[rec.action_item.status] ?? "secondary"}
                  className="text-xs"
                >
                  {rec.action_item.status}
                </Badge>
              )}
              {rec.user_rating && (
                <Badge variant="outline" className="text-xs">
                  Rated {rec.user_rating}/5
                </Badge>
              )}
            </div>
            {rec.description && (
              <p className="text-muted-foreground line-clamp-2">{rec.description}</p>
            )}
            {rec.why_now?.length ? (
              <div className="flex flex-wrap items-center gap-2 pt-1">
                {rec.why_now.map((chip, index) => (
                  <WhyNowChip key={`${rec.id}-${chip.code}-${index}`} chip={chip} />
                ))}
              </div>
            ) : null}
            <p className="text-xs text-muted-foreground">
              Rate this suggestion to tune future recommendations.
            </p>
          </div>
          <Button
            size="sm"
            variant={rec.action_item ? "outline" : "default"}
            disabled={Boolean(rec.action_item) || pendingAction}
            onClick={() => handleCreateActionItem(rec.id, options?.goal)}
          >
            {rec.action_item ? "Tracked" : options?.ctaLabel ?? "Track"}
          </Button>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {[1, 2, 3, 4, 5].map((rating) => (
            <Button
              key={rating}
              size="sm"
              variant={selectedRating === rating ? "default" : "outline"}
              className="h-7 w-8 px-0 text-xs"
              disabled={pendingFeedback}
              onClick={() =>
                setFeedbackRatings((prev) => ({
                  ...prev,
                  [rec.id]: rating,
                }))
              }
            >
              {rating}
            </Button>
          ))}
          <span className="text-xs text-muted-foreground">1 = skip, 5 = strong fit</span>
        </div>

        <div className="space-y-2">
          <Textarea
            rows={2}
            placeholder="Optional note - why this did or did not fit right now"
            value={comment}
            onChange={(e) =>
              setFeedbackDrafts((prev) => ({
                ...prev,
                [rec.id]: e.target.value,
              }))
            }
          />
          <div className="flex flex-wrap gap-2">
            <Button size="sm" disabled={pendingFeedback || selectedRating === 0} onClick={() => handleSaveFeedback(rec)}>
              {pendingFeedback ? "Saving..." : rec.user_rating ? "Update feedback" : "Save feedback"}
            </Button>
            {rec.feedback_at && (
              <p className="self-center text-xs text-muted-foreground">Saved feedback stays with this suggestion.</p>
            )}
          </div>
        </div>
      </div>
    );
  };

  const renderActionCard = (item: TrackedRecommendationAction) => {
    const note = reviewNotes[item.recommendation_id] ?? item.action_item.review_notes ?? "";
    const pending = savingActionId === item.recommendation_id;

    return (
      <div key={item.recommendation_id} className="space-y-3 rounded-lg border p-3 text-sm">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-medium">{item.recommendation_title}</span>
              <Badge variant="secondary" className="text-xs">{item.category}</Badge>
              <Badge variant={actionStatusColor[item.action_item.status] ?? "secondary"} className="text-xs">
                {item.action_item.status}
              </Badge>
            </div>
            <p className="mt-1 text-muted-foreground">{item.action_item.next_step}</p>
            {item.action_item.goal_title && (
              <p className="mt-1 text-xs text-muted-foreground">Linked to: {item.action_item.goal_title}</p>
            )}
          </div>
          <div className="flex flex-wrap gap-1">
            {(["small", "medium", "large"] as const).map((effort) => (
              <Button
                key={effort}
                size="sm"
                variant={item.action_item.effort === effort ? "default" : "outline"}
                className="h-7 px-2 text-xs"
                disabled={pending}
                onClick={() => handleActionUpdate(item.recommendation_id, { effort })}
              >
                {effort}
              </Button>
            ))}
          </div>
        </div>

        <div className="flex flex-wrap gap-1">
          {([
            ["today", "Today"],
            ["this_week", "This week"],
            ["later", "Later"],
          ] as const).map(([dueWindow, label]) => (
            <Button
              key={dueWindow}
              size="sm"
              variant={item.action_item.due_window === dueWindow ? "default" : "outline"}
              className="h-7 px-2 text-xs"
              disabled={pending}
              onClick={() => handleActionUpdate(item.recommendation_id, { due_window: dueWindow })}
            >
              {label}
            </Button>
          ))}
        </div>

        {item.action_item.success_criteria && (
          <p className="text-xs text-muted-foreground">
            Success: {item.action_item.success_criteria}
          </p>
        )}

        <div className="flex flex-wrap gap-1">
          {([
            ["accepted", "Accept"],
            ["deferred", "Defer"],
            ["blocked", "Block"],
            ["completed", "Complete"],
            ["abandoned", "Abandon"],
          ] as const).map(([statusValue, label]) => (
            <Button
              key={statusValue}
              size="sm"
              variant={item.action_item.status === statusValue ? "default" : "outline"}
              className="h-7 px-2 text-xs"
              disabled={pending}
              onClick={() =>
                handleActionUpdate(item.recommendation_id, {
                  status: statusValue,
                  review_notes: note,
                })
              }
            >
              {label}
            </Button>
          ))}
        </div>

        <div className="space-y-2">
          <Textarea
            rows={2}
            placeholder="Review notes — what happened, what changed, what you learned?"
            value={note}
            onChange={(e) =>
              setReviewNotes((prev) => ({ ...prev, [item.recommendation_id]: e.target.value }))
            }
          />
          <Button
            size="sm"
            variant="outline"
            disabled={pending}
            onClick={() => handleActionUpdate(item.recommendation_id, { review_notes: note })}
          >
            Save Notes
          </Button>
        </div>
      </div>
    );
  };

  return (
    <div className="mx-auto max-w-3xl space-y-6 p-4 md:p-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="space-y-1">
          <h1 className="text-2xl font-semibold">Focus</h1>
          <p className="text-sm text-muted-foreground">
            See your best next moves, keep active goals moving, and turn opportunities into progress.
          </p>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <Button variant="outline" size="sm" asChild>
            <Link href="/projects">More opportunities</Link>
          </Button>
          <Sheet open={createOpen} onOpenChange={setCreateOpen}>
            <SheetTrigger asChild>
              <Button size="sm">
                <Plus className="mr-2 h-4 w-4" /> New Goal
              </Button>
            </SheetTrigger>
            <SheetContent className="sm:max-w-lg overflow-y-auto">
              <SheetHeader>
                <SheetTitle>New goal</SheetTitle>
                <SheetDescription>
                  What are you committing to next? New web goals start as general goals and can be broken into milestones after creation.
                </SheetDescription>
              </SheetHeader>
              <div className="mt-6 space-y-4 px-6 pb-6">
                <div className="space-y-1.5">
                  <Label>Title</Label>
                  <Input
                    value={form.title}
                    onChange={(e) => setForm({ ...form, title: e.target.value })}
                    placeholder="Ship the portfolio refresh"
                  />
                </div>
                <div className="space-y-1.5">
                  <Label>Description</Label>
                  <Textarea
                    rows={6}
                    value={form.content}
                    onChange={(e) => setForm({ ...form, content: e.target.value })}
                    placeholder="Why this matters, what done looks like, and any constraints to keep in mind."
                  />
                </div>
                <div className="space-y-1.5">
                  <Label>Tags (comma-separated)</Label>
                  <Input
                    value={form.tags}
                    onChange={(e) => setForm({ ...form, tags: e.target.value })}
                    placeholder="career, portfolio"
                  />
                </div>
                <Button onClick={handleCreate} disabled={creating || !form.title.trim()}>
                  {creating ? "Saving..." : "Add Goal"}
                </Button>
              </div>
            </SheetContent>
          </Sheet>
        </div>
      </div>

      {/* Loading */}
      {loading && (
        <div className="space-y-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <GoalSkeleton key={i} />
          ))}
        </div>
      )}

      {/* Empty state */}
      {!loading && goals.length === 0 && (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-muted">
            <Target className="h-7 w-7 text-muted-foreground" />
          </div>
          <h3 className="text-lg font-medium">Nothing in focus yet</h3>
          <p className="mt-1 max-w-sm text-sm text-muted-foreground">
            Start by setting a goal or exploring opportunities. I&apos;ll keep the strongest next steps at the top.
          </p>
          <Button className="mt-4" variant="outline" onClick={() => setCreateOpen(true)}>
            <Plus className="h-4 w-4" /> Create your first goal
          </Button>
        </div>
      )}

      {!loading && goals.length > 0 && (
        <>
          <div className="grid gap-3 sm:grid-cols-3">
            <Card className="gap-3 py-4">
              <CardHeader className="px-4 pb-0">
                <CardDescription className="flex items-center gap-2 text-xs uppercase tracking-wide">
                  <Target className="h-3.5 w-3.5" /> In focus
                </CardDescription>
                <CardTitle className="text-2xl">{goalCounts.focus}</CardTitle>
              </CardHeader>
              <CardContent className="px-4 text-xs text-muted-foreground">
                Active and paused goals stay in the default working list.
              </CardContent>
            </Card>

            <Card className="gap-3 py-4">
              <CardHeader className="px-4 pb-0">
                <CardDescription className="flex items-center gap-2 text-xs uppercase tracking-wide">
                  <Clock3 className="h-3.5 w-3.5" /> Needs check-in
                </CardDescription>
                <CardTitle className="text-2xl">{goalCounts.stale}</CardTitle>
              </CardHeader>
              <CardContent className="px-4 text-xs text-muted-foreground">
                Stale goals surface separately so they do not get buried in the list.
              </CardContent>
            </Card>

            <Card className="gap-3 py-4">
              <CardHeader className="px-4 pb-0">
                <CardDescription className="flex items-center gap-2 text-xs uppercase tracking-wide">
                  <Archive className="h-3.5 w-3.5" /> Archived
                </CardDescription>
                <CardTitle className="text-2xl">{goalCounts.archived}</CardTitle>
              </CardHeader>
              <CardContent className="px-4 text-xs text-muted-foreground">
                Completed and abandoned goals remain available without crowding current work.
              </CardContent>
            </Card>
          </div>

          <Card className="gap-3 py-4">
            <CardContent className="flex flex-col gap-3 px-4 sm:flex-row sm:items-center sm:justify-between">
              <div className="flex flex-wrap gap-2">
                {filterOptions.map((option) => (
                  <Button
                    key={option.value}
                    size="sm"
                    variant={goalFilter === option.value ? "default" : "outline"}
                    onClick={() => setGoalFilter(option.value)}
                  >
                    {option.label}
                    <Badge
                      variant={goalFilter === option.value ? "secondary" : "outline"}
                      className="ml-1"
                    >
                      {option.count}
                    </Badge>
                  </Button>
                ))}
              </div>

              <div className="flex flex-col gap-2 sm:w-auto sm:min-w-72">
                <div className="relative">
                  <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search goals"
                    className="pl-9"
                  />
                </div>
                {hasActiveFilters && (
                  <div className="flex justify-end">
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => {
                        setGoalFilter("focus");
                        setSearchQuery("");
                      }}
                    >
                      Reset filters
                    </Button>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          <p className="text-sm text-muted-foreground">
            {filteredGoals.length === goals.length
              ? `${goals.length} goals total`
              : `Showing ${filteredGoals.length} of ${goals.length} goals`}
          </p>
        </>
      )}

      {!loading && unanchored.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
            <Lightbulb className="h-4 w-4" />
            Best next moves
          </div>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {unanchored.map((rec) =>
              renderRecommendationCard(rec, {
                ctaLabel: "Track",
              })
            )}
          </div>
        </div>
      )}

      {weeklyPlan && weeklyPlan.items.length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between gap-3">
              <div>
                <CardTitle className="text-base">This week</CardTitle>
                <CardDescription>
                  {weeklyPlan.used_points}/{weeklyPlan.capacity_points} effort points planned
                </CardDescription>
              </div>
              <Badge variant="secondary">{weeklyPlan.remaining_points} points free</Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            {weeklyPlan.items.map(renderActionCard)}
          </CardContent>
        </Card>
      )}

      {/* Goals list */}
      {!loading && goals.length > 0 && filteredGoals.length === 0 && (
        <Card className="border-dashed py-10 text-center">
          <CardContent className="space-y-3 px-6">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-muted">
              <Target className="h-5 w-5 text-muted-foreground" />
            </div>
            <div className="space-y-1">
              <CardTitle className="text-lg">{filteredEmptyState.title}</CardTitle>
              <CardDescription>{filteredEmptyState.description}</CardDescription>
            </div>
            {hasActiveFilters && (
              <div className="flex justify-center">
                <Button
                  variant="outline"
                  onClick={() => {
                    setGoalFilter("focus");
                    setSearchQuery("");
                  }}
                >
                  Reset filters
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {!loading && filteredGoals.length > 0 && (
        <div className="space-y-4">
          {filteredGoals.map((g) => {
            const progress = progressMap[g.path];
            const goalActions = linkedActionItems(g.path);
            return (
              <Card key={g.path}>
                <CardHeader
                  className="cursor-pointer pb-2"
                  onClick={() => {
                    const next = selectedGoal === g.path ? null : g.path;
                    setSelectedGoal(next);
                    if (next) {
                      loadProgress(g.path);
                      loadRecommendations(g.path, g.title);
                    }
                  }}
                >
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-base">{g.title}</CardTitle>
                    <div className="flex gap-2">
                      {g.is_stale && (
                        <Badge variant="destructive">Needs check-in</Badge>
                      )}
                      <Badge variant={statusColor[g.status] as "default" | "secondary" | "outline" | "destructive"}>
                        {g.status}
                      </Badge>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <CardDescription className={staleUrgency(g.days_since_check)}>
                      {formatCheckInAge(g.days_since_check)}
                    </CardDescription>
                    {progress && progress.total > 0 ? (
                      <span className="text-xs text-muted-foreground">{progress.completed}/{progress.total} milestones</span>
                    ) : (
                      <span className="flex items-center gap-1 text-xs text-muted-foreground">
                        <Plus className="h-3 w-3" /> Add milestones to track progress
                      </span>
                    )}
                  </div>
                  {progress && progress.total > 0 && (
                    <div className="mt-1.5 h-1.5 w-full rounded-full bg-muted">
                      <div
                        className="h-full rounded-full bg-primary transition-all"
                        style={{ width: `${progress.percent}%` }}
                      />
                    </div>
                  )}
                  {progress?.milestones && (() => {
                    const next = progress.milestones.find((m) => !m.completed);
                    return next ? (
                      <p className="text-xs text-muted-foreground mt-1">
                        Next: {next.title}
                      </p>
                    ) : null;
                  })()}
                </CardHeader>

                {selectedGoal === g.path && (
                  <CardContent className="space-y-4">
                    {/* Progress */}
                    {progress && progress.total > 0 ? (
                      <div>
                        <div className="mb-2 text-sm font-medium">
                          Progress: {progress.percent}% ({progress.completed}/{progress.total})
                        </div>
                        <div className="h-2 w-full rounded-full bg-muted">
                          <div
                            className="h-full rounded-full bg-primary transition-all"
                            style={{ width: `${progress.percent}%` }}
                          />
                        </div>
                      </div>
                    ) : (
                      <p className="text-sm text-muted-foreground">
                        No milestones — add one below to start tracking
                      </p>
                    )}

                    {/* Milestones */}
                    <div className="space-y-2">
                      <h4 className="text-sm font-medium">Milestones</h4>
                      {progress?.milestones?.map((m, i) => (
                          <div
                            key={i}
                            className="flex items-center gap-2 text-sm"
                          >
                            {m.completed ? (
                              <CheckCircle2 className="h-4 w-4 text-success" />
                            ) : (
                              <button onClick={() => handleCompleteMilestone(g.path, i)}>
                                <Circle className="h-4 w-4 text-muted-foreground hover:text-primary" />
                              </button>
                            )}
                            <span className={m.completed ? "line-through text-muted-foreground" : ""}>
                              {m.title}
                            </span>
                          </div>
                        ))}
                        <div className="flex gap-2">
                          <Input
                            placeholder="New milestone"
                            value={milestoneInputs[g.path] || ""}
                            onChange={(e) =>
                              setMilestoneInputs((prev) => ({ ...prev, [g.path]: e.target.value }))
                            }
                            className="text-sm"
                          />
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleAddMilestone(g.path)}
                            disabled={!(milestoneInputs[g.path] || "").trim()}
                          >
                            Add
                          </Button>
                        </div>
                    </div>

                    {/* Check-in */}
                    <div className="space-y-2">
                      <h4 className="text-sm font-medium">Check in</h4>
                      <Textarea
                        rows={2}
                        placeholder="What's changed since your last check-in?"
                        value={checkInInputs[g.path] || ""}
                        onChange={(e) =>
                          setCheckInInputs((prev) => ({ ...prev, [g.path]: e.target.value }))
                        }
                      />
                      <Button
                        size="sm"
                        onClick={() => handleCheckIn(g.path)}
                      >
                        Check In
                      </Button>
                    </div>

                    {/* Status actions */}
                    <div className="flex flex-wrap gap-2">
                      {g.status !== "completed" && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleStatusChange(g.path, "completed")}
                        >
                          Complete
                        </Button>
                      )}

                      {g.status === "active" && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleStatusChange(g.path, "paused")}
                        >
                          Pause
                        </Button>
                      )}

                      {(g.status === "paused" || g.status === "abandoned") && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleStatusChange(g.path, "active")}
                        >
                          {g.status === "abandoned" ? "Reactivate" : "Resume"}
                        </Button>
                      )}

                      {(g.status === "active" || g.status === "paused") && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleStatusChange(g.path, "abandoned")}
                        >
                          Abandon
                        </Button>
                      )}
                    </div>

                    {goalActions.length > 0 && (
                      <div className="space-y-2">
                        <h4 className="text-sm font-medium">Tracked action plans</h4>
                        {goalActions.map(renderActionCard)}
                      </div>
                    )}

                    {/* Goal-contextual recommendations */}
                    {recommendationsMap[g.path]?.length > 0 && (
                      <div className="space-y-2">
                        <h4 className="flex items-center gap-1.5 text-sm font-medium">
                          <Lightbulb className="h-4 w-4 text-warning" />
                          Suggested next moves
                        </h4>
                        {recommendationsMap[g.path].map((rec) =>
                          renderRecommendationCard(rec, {
                            goal: g,
                            ctaLabel: "Add to plan",
                            compact: true,
                          })
                        )}
                      </div>
                    )}
                  </CardContent>
                )}
              </Card>
            );
          })}
        </div>
      )}

    </div>
  );
}
