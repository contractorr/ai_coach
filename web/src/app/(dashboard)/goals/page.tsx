"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";
import { useToken } from "@/hooks/useToken";
import { CheckCircle2, Circle, Lightbulb, Plus, Target } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
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
  const [selectedGoal, setSelectedGoal] = useState<string | null>(null);
  const [progressMap, setProgressMap] = useState<Record<string, Progress>>({});
  const [recommendationsMap, setRecommendationsMap] = useState<Record<string, BriefingRecommendation[]>>({});
  const [unanchored, setUnanchored] = useState<BriefingRecommendation[]>([]);
  const [actionItems, setActionItems] = useState<TrackedRecommendationAction[]>([]);
  const [weeklyPlan, setWeeklyPlan] = useState<WeeklyPlanResponse | null>(null);
  const [reviewNotes, setReviewNotes] = useState<Record<string, string>>({});
  const [savingActionId, setSavingActionId] = useState<string | null>(null);
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
    apiFetch<BriefingRecommendation[]>("/api/recommendations?limit=4", {}, token)
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
    if (!token || !form.title) return;
    setCreating(true);
    try {
      await apiFetch(
        "/api/goals",
        {
          method: "POST",
          body: JSON.stringify({
            ...form,
            tags: form.tags ? form.tags.split(",").map((t) => t.trim()) : undefined,
          }),
        },
        token
      );
      setForm({ title: "", content: "", tags: "" });
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
    const notes = checkInInputs[path] || "";
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
    const title = milestoneInputs[path] || "";
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
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Goals</h1>
        <Sheet>
          <SheetTrigger asChild>
            <Button>
              <Plus className="mr-2 h-4 w-4" /> New Goal
            </Button>
          </SheetTrigger>
          <SheetContent className="sm:max-w-lg overflow-y-auto">
            <SheetHeader>
              <SheetTitle>New goal</SheetTitle>
              <SheetDescription>What are you committing to?</SheetDescription>
            </SheetHeader>
            <div className="mt-6 space-y-4 px-6 pb-6">
              <div className="space-y-1.5">
                <Label>Title</Label>
                <Input
                  value={form.title}
                  onChange={(e) => setForm({ ...form, title: e.target.value })}
                />
              </div>
              <div className="space-y-1.5">
                <Label>Description</Label>
                <Textarea
                  rows={6}
                  value={form.content}
                  onChange={(e) => setForm({ ...form, content: e.target.value })}
                />
              </div>
              <div className="space-y-1.5">
                <Label>Tags (comma-separated)</Label>
                <Input
                  value={form.tags}
                  onChange={(e) => setForm({ ...form, tags: e.target.value })}
                />
              </div>
              <Button onClick={handleCreate} disabled={creating || !form.title}>
                {creating ? "Saving..." : "Add Goal"}
              </Button>
            </div>
          </SheetContent>
        </Sheet>
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
          <h3 className="text-lg font-medium">No commitments tracked yet</h3>
          <p className="mt-1 max-w-sm text-sm text-muted-foreground">
            Set a goal and I&apos;ll track your progress, flag when it goes stale,
            and surface it in your daily brief.
          </p>
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
      {!loading && goals.length > 0 && (
        <div className="space-y-4">
          {goals.map((g) => {
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
                      Last check-in: {g.days_since_check}d ago
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
                            disabled={!milestoneInputs[g.path]}
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
                    <div className="flex gap-2">
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
                      {g.status === "paused" && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleStatusChange(g.path, "active")}
                        >
                          Resume
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
                        {recommendationsMap[g.path].map((rec) => (
                          <div
                            key={rec.id}
                            className="flex items-start gap-2 rounded-md border px-3 py-2 text-sm"
                          >
                            <div className="min-w-0 flex-1">
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
                              </div>
                              {rec.description && (
                                <p className="mt-0.5 text-muted-foreground line-clamp-1">
                                  {rec.description}
                                </p>
                              )}
                            </div>
                            <Button
                              size="sm"
                              variant={rec.action_item ? "outline" : "default"}
                              disabled={Boolean(rec.action_item) || savingActionId === rec.id}
                              onClick={() => handleCreateActionItem(rec.id, g)}
                            >
                              {rec.action_item ? "Tracked" : "Add to plan"}
                            </Button>
                          </div>
                        ))}
                      </div>
                    )}
                  </CardContent>
                )}
              </Card>
            );
          })}
        </div>
      )}

      {/* Unanchored recommendations */}
      {!loading && goals.length > 0 && unanchored.length > 0 && (
        <div className="space-y-3">
          <h2 className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
            <Lightbulb className="h-4 w-4" />
            Worth exploring
          </h2>
          <div className="grid gap-3 sm:grid-cols-2">
            {unanchored.map((rec) => (
              <div
                key={rec.id}
                className="rounded-xl border px-4 py-3 text-sm"
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
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
                    </div>
                    {rec.description && (
                      <p className="mt-1 text-muted-foreground line-clamp-1">
                        {rec.description}
                      </p>
                    )}
                  </div>
                  <Button
                    size="sm"
                    variant={rec.action_item ? "outline" : "default"}
                    disabled={Boolean(rec.action_item) || savingActionId === rec.id}
                    onClick={() => handleCreateActionItem(rec.id)}
                  >
                    {rec.action_item ? "Tracked" : "Track"}
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
