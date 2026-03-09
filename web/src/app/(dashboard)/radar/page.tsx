"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  ArrowUpRight,
  Bookmark,
  Brain,
  FolderOpen,
  Loader2,
  RefreshCw,
  Sparkles,
  Target,
} from "lucide-react";
import { toast } from "sonner";

import { WorkspacePageHeader } from "@/components/WorkspacePageHeader";
import { WhyNowChip } from "@/components/shared/WhyNowChip";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useToken } from "@/hooks/useToken";
import { apiFetch } from "@/lib/api";
import type { DossierEscalation } from "@/types/briefing";
import type { SavedFollowUp, ResearchDossier, ThreadInboxSummary, WatchlistTopic } from "@/types/radar";
import type { SuggestionItem } from "@/types/suggestions";

function formatRelativeDate(value?: string) {
  if (!value) return "No recent activity";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Updated recently";
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
  }).format(date);
}

function sourceBadge(kind: string) {
  return kind
    .replaceAll("_", " ")
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

function readSignalLink(item: SuggestionItem) {
  const payload = item.payload ?? {};
  const url = payload.url ?? payload.source_url;
  return typeof url === "string" && url.trim().length > 0 ? url : null;
}

const RADAR_KINDS = new Set([
  "company_movement",
  "hiring_signal",
  "regulatory_alert",
  "dossier_escalation",
  "assumption_alert",
]);

function readSignalTitle(item: SuggestionItem) {
  const payload = item.payload ?? {};
  const title = payload.title ?? item.title;
  return typeof title === "string" && title.trim().length > 0 ? title : item.title;
}

export default function RadarPage() {
  const token = useToken();
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [busyKey, setBusyKey] = useState<string | null>(null);
  const [researchLocked, setResearchLocked] = useState(false);
  const [suggestions, setSuggestions] = useState<SuggestionItem[]>([]);
  const [watchlist, setWatchlist] = useState<WatchlistTopic[]>([]);
  const [threads, setThreads] = useState<ThreadInboxSummary[]>([]);
  const [escalations, setEscalations] = useState<DossierEscalation[]>([]);
  const [dossiers, setDossiers] = useState<ResearchDossier[]>([]);
  const [followUps, setFollowUps] = useState<SavedFollowUp[]>([]);

  const loadRadar = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    const [suggestionsRes, watchlistRes, threadsRes, escalationsRes, dossiersRes, followUpsRes] =
      await Promise.allSettled([
        apiFetch<SuggestionItem[]>("/api/suggestions?limit=20", {}, token),
        apiFetch<WatchlistTopic[]>("/api/intel/watchlist", {}, token),
        apiFetch<ThreadInboxSummary[]>("/api/threads/inbox?limit=20", {}, token),
        apiFetch<DossierEscalation[]>("/api/dossier-escalations", {}, token),
        apiFetch<ResearchDossier[]>("/api/research/dossiers?limit=20", {}, token),
        apiFetch<SavedFollowUp[]>("/api/intel/follow-ups", {}, token),
      ]);

    if (suggestionsRes.status === "fulfilled") setSuggestions(suggestionsRes.value);
    if (watchlistRes.status === "fulfilled") setWatchlist(watchlistRes.value);
    if (threadsRes.status === "fulfilled") setThreads(threadsRes.value);
    if (escalationsRes.status === "fulfilled") setEscalations(escalationsRes.value);
    if (followUpsRes.status === "fulfilled") setFollowUps(followUpsRes.value.filter((item) => item.saved));

    if (dossiersRes.status === "fulfilled") {
      setResearchLocked(false);
      setDossiers(dossiersRes.value);
    } else {
      setResearchLocked(true);
      setDossiers([]);
    }

    setLoading(false);
  }, [token]);

  useEffect(() => {
    void loadRadar();
  }, [loadRadar]);

  const radarSuggestions = useMemo(
    () => suggestions.filter((item) => RADAR_KINDS.has(item.kind)),
    [suggestions]
  );

  const activeDossiers = useMemo(
    () => dossiers.filter((item) => (item.status || "active") !== "archived"),
    [dossiers]
  );
  const activeEscalations = useMemo(
    () => escalations.filter((item) => item.state !== "dismissed" && item.state !== "accepted"),
    [escalations]
  );

  const withBusy = async (key: string, fn: () => Promise<void>) => {
    setBusyKey(key);
    try {
      await fn();
      await loadRadar();
    } finally {
      setBusyKey(null);
    }
  };

  const handleScrape = async () => {
    if (!token) return;
    setRefreshing(true);
    try {
      await apiFetch("/api/intel/scrape", { method: "POST" }, token);
      toast.success("Radar refreshed");
      await loadRadar();
    } catch (error) {
      toast.error((error as Error).message);
    } finally {
      setRefreshing(false);
    }
  };

  const handleSuggestionAction = async (item: SuggestionItem) => {
    if (!token) return;

    if (item.kind === "dossier_escalation") {
      const escalationId = item.payload?.escalation_id;
      if (typeof escalationId === "string" && escalationId) {
        await withBusy(`suggestion-${escalationId}`, async () => {
          await apiFetch(`/api/dossier-escalations/${encodeURIComponent(escalationId)}/accept`, { method: "POST" }, token);
          toast.success("Dossier started");
        });
        return;
      }
    }

    const url = readSignalLink(item);
    if (url) {
      await withBusy(`suggestion-save-${url}`, async () => {
        await apiFetch(
          "/api/intel/follow-ups",
          {
            method: "PUT",
            body: JSON.stringify({
              url,
              title: readSignalTitle(item),
              saved: true,
              note: "",
              watchlist_ids: [],
            }),
          },
          token
        );
        toast.success("Saved to Radar follow-ups");
      });
      return;
    }

    if (item.kind === "assumption_alert") {
      router.push("/settings#watchlist");
      return;
    }

    router.push("/focus");
  };

  const handleThreadAction = async (threadId: string, action: string) => {
    if (!token) return;
    const key = `thread-${threadId}-${action}`;
    await withBusy(key, async () => {
      if (action === "dismiss") {
        await apiFetch(
          `/api/threads/${encodeURIComponent(threadId)}/state`,
          {
            method: "PATCH",
            body: JSON.stringify({ inbox_state: "dismissed", last_action: "dismissed" }),
          },
          token
        );
        toast.success("Thread dismissed");
        return;
      }

      if (action === "goal") {
        await apiFetch(`/api/threads/${encodeURIComponent(threadId)}/actions/make-goal`, { method: "POST" }, token);
        toast.success("Goal created from thread");
        return;
      }

      if (action === "research") {
        await apiFetch(`/api/threads/${encodeURIComponent(threadId)}/actions/run-research`, { method: "POST" }, token);
        toast.success("Research started");
        return;
      }

      if (action === "dossier") {
        await apiFetch(`/api/threads/${encodeURIComponent(threadId)}/actions/start-dossier`, { method: "POST" }, token);
        toast.success("Dossier started");
      }
    });
  };

  const handleEscalationAction = async (escalationId: string, action: "accept" | "dismiss" | "snooze") => {
    if (!token) return;
    await withBusy(`escalation-${escalationId}-${action}`, async () => {
      await apiFetch(
        `/api/dossier-escalations/${encodeURIComponent(escalationId)}/${action}`,
        { method: "POST" },
        token
      );
      toast.success(action === "accept" ? "Dossier started" : action === "dismiss" ? "Suggestion dismissed" : "Suggestion snoozed");
    });
  };

  const handleDossierAction = async (dossierId: string, action: "run" | "archive") => {
    if (!token) return;
    await withBusy(`dossier-${dossierId}-${action}`, async () => {
      if (action === "run") {
        await apiFetch(`/api/research/run?dossier_id=${encodeURIComponent(dossierId)}`, { method: "POST" }, token);
        toast.success("Research refresh started");
        return;
      }

      await apiFetch(`/api/research/dossiers/${encodeURIComponent(dossierId)}/archive`, { method: "POST" }, token);
      toast.success("Dossier archived");
    });
  };

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-4 md:p-6">
      <WorkspacePageHeader
        eyebrow="Monitor"
        title="Radar"
        description="Keep one eye on what changed, what resurfaced, and what needs follow-up without juggling separate monitoring tools."
        actions={
          <div className="flex flex-wrap gap-2">
            <Button variant="outline" asChild>
              <Link href="/intel">Open advanced radar</Link>
            </Button>
            <Button onClick={handleScrape} disabled={refreshing}>
              {refreshing ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <RefreshCw className="mr-2 h-4 w-4" />}
              {refreshing ? "Scanning..." : "Scan now"}
            </Button>
          </div>
        }
      />

      <div className="grid gap-3 md:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>For you</CardDescription>
            <CardTitle className="text-2xl">{radarSuggestions.length}</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            Personalized monitoring items across intel, alerts, assumptions, and dossier triggers.
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Tracked topics</CardDescription>
            <CardTitle className="text-2xl">{watchlist.length}</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            Your companies, themes, sectors, and places to watch.
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Saved follow-ups</CardDescription>
            <CardTitle className="text-2xl">{followUps.length}</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            Signals you saved for later with notes and follow-up context.
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="for-you">
        <TabsList className="flex w-full flex-wrap justify-start">
          <TabsTrigger value="for-you">For you</TabsTrigger>
          <TabsTrigger value="threads">Threads</TabsTrigger>
          <TabsTrigger value="dossiers">Dossiers</TabsTrigger>
          <TabsTrigger value="saved">Saved</TabsTrigger>
          <TabsTrigger value="tracked-topics">Tracked topics</TabsTrigger>
        </TabsList>

        <TabsContent value="for-you" className="space-y-4">
          {loading ? (
            <Card>
              <CardContent className="flex items-center gap-2 py-10 text-sm text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" /> Loading your monitoring feed...
              </CardContent>
            </Card>
          ) : radarSuggestions.length === 0 ? (
            <Card>
              <CardContent className="flex flex-col items-center py-12 text-center">
                <Sparkles className="mb-3 h-8 w-8 text-muted-foreground" />
                <CardTitle className="text-lg">Nothing urgent yet</CardTitle>
                <CardDescription className="mt-2 max-w-md">
                  Add a tracked topic or run a scan and Radar will start surfacing the strongest items for you.
                </CardDescription>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4 lg:grid-cols-2">
              {radarSuggestions.slice(0, 12).map((item, index) => {
                const signalUrl = readSignalLink(item);
                const itemKey = `${item.kind}-${item.title}-${index}`;
                return (
                  <Card key={itemKey} className="h-full">
                    <CardHeader className="space-y-3">
                      <div className="flex flex-wrap items-center gap-2">
                        <Badge variant="secondary">{sourceBadge(item.kind)}</Badge>
                        {typeof item.priority === "number" && item.priority > 0 ? (
                          <Badge variant="outline">Priority {item.priority}</Badge>
                        ) : null}
                      </div>
                      <div className="space-y-1">
                        <CardTitle className="text-lg leading-snug">{item.title}</CardTitle>
                        <CardDescription>{item.description || "Review this change and decide whether it needs follow-up."}</CardDescription>
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      {item.why_now?.length ? (
                        <div className="flex flex-wrap gap-2">
                          {item.why_now.map((chip, chipIndex) => (
                            <WhyNowChip key={`${chip.code}-${chipIndex}`} chip={chip} />
                          ))}
                        </div>
                      ) : null}
                      <div className="flex flex-wrap gap-2">
                        <Button
                          onClick={() => void handleSuggestionAction(item)}
                          disabled={busyKey === `suggestion-${String(item.payload?.escalation_id || "")}` || busyKey === `suggestion-save-${signalUrl || ""}`}
                        >
                          {item.kind === "dossier_escalation" ? "Start dossier" : signalUrl ? "Save for later" : "Open"}
                        </Button>
                        {signalUrl ? (
                          <Button variant="outline" asChild>
                            <a href={signalUrl} target="_blank" rel="noreferrer">
                              Source <ArrowUpRight className="ml-1 h-3 w-3" />
                            </a>
                          </Button>
                        ) : null}
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </TabsContent>

        <TabsContent value="threads" className="space-y-4">
          {threads.length === 0 ? (
            <Card>
              <CardContent className="flex flex-col items-center py-12 text-center">
                <Brain className="mb-3 h-8 w-8 text-muted-foreground" />
                <CardTitle className="text-lg">Threads appear as you journal</CardTitle>
                <CardDescription className="mt-2 max-w-md">
                  Write a few entries and Radar will group recurring themes here so you can turn them into goals, research, or dossiers.
                </CardDescription>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4 lg:grid-cols-2">
              {threads.map((thread) => (
                <Card key={thread.id}>
                  <CardHeader>
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <CardTitle className="text-lg">{thread.label}</CardTitle>
                        <CardDescription>
                          {thread.entry_count} entries • last active {formatRelativeDate(thread.last_date)}
                        </CardDescription>
                      </div>
                      <Badge variant="outline">{thread.inbox_state.replaceAll("_", " ")}</Badge>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {thread.recent_snippets.length > 0 ? (
                      <details className="rounded-lg border bg-muted/30 p-3 text-sm">
                        <summary className="cursor-pointer font-medium">Recent activity</summary>
                        <ul className="mt-3 space-y-2 text-muted-foreground">
                          {thread.recent_snippets.map((snippet, index) => (
                            <li key={`${thread.id}-${index}`}>{snippet}</li>
                          ))}
                        </ul>
                      </details>
                    ) : null}
                    <div className="flex flex-wrap gap-2">
                      <Button variant="outline" onClick={() => void handleThreadAction(thread.id, "goal")} disabled={busyKey === `thread-${thread.id}-goal`}>
                        Turn into goal
                      </Button>
                      <Button variant="outline" onClick={() => void handleThreadAction(thread.id, "research")} disabled={busyKey === `thread-${thread.id}-research`}>
                        Investigate
                      </Button>
                      <Button variant="outline" onClick={() => void handleThreadAction(thread.id, "dossier")} disabled={busyKey === `thread-${thread.id}-dossier`}>
                        Start dossier
                      </Button>
                      <Button variant="ghost" onClick={() => void handleThreadAction(thread.id, "dismiss")} disabled={busyKey === `thread-${thread.id}-dismiss`}>
                        Dismiss
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="dossiers" className="space-y-4">
          {activeEscalations.length > 0 ? (
            <div className="space-y-3">
              <h2 className="text-sm font-medium text-muted-foreground">Suggested dossiers</h2>
              <div className="grid gap-4 lg:grid-cols-2">
                {activeEscalations.map((item) => (
                  <Card key={item.escalation_id}>
                    <CardHeader>
                      <CardTitle className="text-lg">{item.topic_label}</CardTitle>
                      <CardDescription>
                        Score {item.score.toFixed(2)} • updated {formatRelativeDate(item.updated_at)}
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <p className="text-sm text-muted-foreground">
                        Radar thinks this topic now has enough momentum to deserve a deeper research thread.
                      </p>
                      <div className="flex flex-wrap gap-2">
                        <Button onClick={() => void handleEscalationAction(item.escalation_id, "accept")} disabled={busyKey === `escalation-${item.escalation_id}-accept`}>
                          Start dossier
                        </Button>
                        <Button variant="outline" onClick={() => void handleEscalationAction(item.escalation_id, "snooze")} disabled={busyKey === `escalation-${item.escalation_id}-snooze`}>
                          Snooze
                        </Button>
                        <Button variant="ghost" onClick={() => void handleEscalationAction(item.escalation_id, "dismiss")} disabled={busyKey === `escalation-${item.escalation_id}-dismiss`}>
                          Dismiss
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          ) : null}

          {researchLocked ? (
            <Card>
              <CardContent className="py-10">
                <CardTitle className="text-lg">Add your own research key to use dossiers</CardTitle>
                <CardDescription className="mt-2">
                  Dossiers are an advanced workflow. Add a personal research key in Settings to create and refresh them.
                </CardDescription>
              </CardContent>
            </Card>
          ) : activeDossiers.length === 0 ? (
            <Card>
              <CardContent className="py-10">
                <CardTitle className="text-lg">No active dossiers</CardTitle>
                <CardDescription className="mt-2">
                  Start a dossier from a thread or dossier suggestion when a topic deserves deeper tracking.
                </CardDescription>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-3">
              <h2 className="text-sm font-medium text-muted-foreground">Active dossiers</h2>
              <div className="grid gap-4 lg:grid-cols-2">
                {activeDossiers.map((dossier) => (
                  <Card key={dossier.dossier_id}>
                    <CardHeader>
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <CardTitle className="text-lg">{dossier.topic}</CardTitle>
                          <CardDescription>
                            {dossier.update_count || 0} updates • last refreshed {formatRelativeDate(dossier.last_updated || dossier.updated || dossier.created)}
                          </CardDescription>
                        </div>
                        <Badge variant="outline">{dossier.status || "active"}</Badge>
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <p className="text-sm text-muted-foreground">
                        {dossier.latest_change_summary || "No change summary yet. Run research to produce the first update."}
                      </p>
                      {dossier.open_questions?.length ? (
                        <div className="space-y-2">
                          <div className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Open questions</div>
                          <ul className="space-y-1 text-sm text-muted-foreground">
                            {dossier.open_questions.slice(0, 3).map((question) => (
                              <li key={question}>• {question}</li>
                            ))}
                          </ul>
                        </div>
                      ) : null}
                      <div className="flex flex-wrap gap-2">
                        <Button variant="outline" onClick={() => void handleDossierAction(dossier.dossier_id, "run")} disabled={busyKey === `dossier-${dossier.dossier_id}-run`}>
                          Refresh research
                        </Button>
                        <Button variant="ghost" onClick={() => void handleDossierAction(dossier.dossier_id, "archive")} disabled={busyKey === `dossier-${dossier.dossier_id}-archive`}>
                          Archive to Library
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          )}
        </TabsContent>

        <TabsContent value="saved" className="space-y-4">
          {followUps.length === 0 ? (
            <Card>
              <CardContent className="flex flex-col items-center py-12 text-center">
                <Bookmark className="mb-3 h-8 w-8 text-muted-foreground" />
                <CardTitle className="text-lg">No saved follow-ups</CardTitle>
                <CardDescription className="mt-2 max-w-md">
                  Save useful items from the `For you` feed and they&apos;ll stay here with your notes.
                </CardDescription>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4 lg:grid-cols-2">
              {followUps.map((item) => (
                <Card key={item.url}>
                  <CardHeader>
                    <CardTitle className="text-lg">{item.title}</CardTitle>
                    <CardDescription>
                      Saved {formatRelativeDate(item.updated_at || item.created_at)}
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <p className="text-sm text-muted-foreground">
                      {item.note || "No note yet — keep this here until you decide what to do with it."}
                    </p>
                    <Button variant="outline" asChild>
                      <a href={item.url} target="_blank" rel="noreferrer">
                        Open source <ArrowUpRight className="ml-1 h-3 w-3" />
                      </a>
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="tracked-topics" className="space-y-4">
          {watchlist.length === 0 ? (
            <Card>
              <CardContent className="flex flex-col items-center py-12 text-center">
                <Target className="mb-3 h-8 w-8 text-muted-foreground" />
                <CardTitle className="text-lg">No tracked topics yet</CardTitle>
                <CardDescription className="mt-2 max-w-md">
                  Start with plain-language topics like a company, theme, sector, or geography. You can tune advanced monitoring later.
                </CardDescription>
                <Button className="mt-4" asChild>
                  <Link href="/settings#watchlist">Add a tracked topic</Link>
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {watchlist.map((item) => (
                <Card key={item.id}>
                  <CardHeader>
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <CardTitle className="text-lg">{item.label}</CardTitle>
                        <CardDescription>
                          {sourceBadge(item.kind)} • {item.priority} priority
                        </CardDescription>
                      </div>
                      <Badge variant="outline">{formatRelativeDate(item.updated_at)}</Badge>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <p className="text-sm text-muted-foreground">
                      {item.why || "Tracked for monitoring relevance across your radar."}
                    </p>
                    <Button variant="outline" asChild>
                      <Link href="/settings#watchlist">
                        Edit topic <FolderOpen className="ml-1 h-3 w-3" />
                      </Link>
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
