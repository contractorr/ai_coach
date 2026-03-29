"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  AlertCircle,
  ArrowUpRight,
  BriefcaseBusiness,
  Lightbulb,
  Loader2,
  RefreshCcw,
  Sparkles,
} from "lucide-react";
import { toast } from "sonner";
import { WorkspacePageHeader } from "@/components/WorkspacePageHeader";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useToken } from "@/hooks/useToken";
import { apiFetch } from "@/lib/api";

interface ProjectIssue {
  title: string;
  url: string;
  summary: string;
  tags: string[];
  source: string;
  match_score: number;
}

interface SettingsSummary {
  has_own_key: boolean;
  using_shared_key: boolean;
}

const DAY_OPTIONS = [7, 14, 30] as const;
const LIMIT_OPTIONS = [6, 12, 20] as const;

export default function ProjectsPage() {
  const token = useToken();
  const [issues, setIssues] = useState<ProjectIssue[]>([]);
  const [settings, setSettings] = useState<SettingsSummary | null>(null);
  const [days, setDays] = useState<number>(14);
  const [limit, setLimit] = useState<number>(12);
  const [issuesLoading, setIssuesLoading] = useState(true);
  const [issuesRefreshing, setIssuesRefreshing] = useState(false);
  const [issuesError, setIssuesError] = useState<string | null>(null);
  const [ideas, setIdeas] = useState<string>("");
  const [ideasLoading, setIdeasLoading] = useState(false);
  const [ideasError, setIdeasError] = useState<string | null>(null);

  const loadSettings = useCallback(async () => {
    if (!token) return;
    try {
      const data = await apiFetch<SettingsSummary>("/api/v1/settings", {}, token);
      setSettings(data);
    } catch {
      setSettings(null);
    }
  }, [token]);

  const loadIssues = useCallback(
    async (mode: "initial" | "refresh" = "initial") => {
      if (!token) {
        setIssuesLoading(false);
        return;
      }
      if (mode === "initial") setIssuesLoading(true);
      if (mode === "refresh") setIssuesRefreshing(true);
      setIssuesError(null);
      try {
        const data = await apiFetch<ProjectIssue[]>(
          `/api/v1/projects/issues?limit=${limit}&days=${days}`,
          {},
          token
        );
        setIssues(data);
      } catch (e) {
        setIssuesError((e as Error).message);
      } finally {
        setIssuesLoading(false);
        setIssuesRefreshing(false);
      }
    },
    [days, limit, token]
  );

  useEffect(() => {
    loadSettings();
  }, [loadSettings]);

  useEffect(() => {
    loadIssues();
  }, [loadIssues]);

  const handleGenerateIdeas = async () => {
    if (!token) return;
    setIdeasLoading(true);
    setIdeasError(null);
    try {
      const response = await apiFetch<{ ideas: string }>(
        "/api/v1/projects/ideas",
        { method: "POST" },
        token
      );
      setIdeas(response.ideas || "");
      if (!response.ideas) {
        toast.info("No ideas generated yet. Try again after adding more context.");
      }
    } catch (e) {
      const message = (e as Error).message;
      setIdeasError(message);
      toast.error(message);
    } finally {
      setIdeasLoading(false);
    }
  };

  const topIssue = useMemo(() => {
    return issues.reduce<ProjectIssue | null>((best, issue) => {
      if (!best || issue.match_score > best.match_score) return issue;
      return best;
    }, null);
  }, [issues]);

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-4 md:p-6">
      <WorkspacePageHeader
        eyebrow="Explore"
        title="Opportunities"
        description="Turn radar signals and your profile into concrete next bets. Review matched issues, then generate project ideas when you want a broader option."
        badge={`${issues.length} issue${issues.length === 1 ? "" : "s"} surfaced`}
        actions={
          <>
            <Button variant="outline" onClick={() => loadIssues("refresh")} disabled={issuesRefreshing}>
              {issuesRefreshing ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <RefreshCcw className="mr-2 h-4 w-4" />
              )}
              Refresh matches
            </Button>
            <Button onClick={handleGenerateIdeas} disabled={ideasLoading}>
              {ideasLoading ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Sparkles className="mr-2 h-4 w-4" />
              )}
              Generate project ideas
            </Button>
          </>
        }
      />

      <div className="grid gap-4 lg:grid-cols-3">
        <Card>
          <CardHeader className="pb-3">
            <CardDescription>Matched issues</CardDescription>
            <CardTitle className="text-2xl">{issues.length}</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            Ranked from the last {days} days of tracked GitHub issue signals.
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardDescription>Strongest match</CardDescription>
            <CardTitle className="text-lg">
              {topIssue ? `${topIssue.match_score}/5 score` : "Waiting for matches"}
            </CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            {topIssue ? topIssue.title : "Widen the time window or refresh after the next radar scrape."}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardDescription>Idea generation</CardDescription>
            <CardTitle className="text-lg">
              {settings?.has_own_key ? "Ready with your key" : settings?.using_shared_key ? "Ready in shared mode" : "Needs key"}
            </CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            {settings?.has_own_key || settings?.using_shared_key ? (
              "Uses your configured AI provider and your saved context."
            ) : (
              <>
                Add a key in <Link href="/settings" className="underline underline-offset-4">Settings</Link> to generate project ideas.
              </>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.15fr)_minmax(360px,0.85fr)]">
        <section className="space-y-4" aria-labelledby="issue-matches-heading">
          <Card>
            <CardHeader className="gap-4 sm:flex-row sm:items-end sm:justify-between">
              <div>
                <CardTitle id="issue-matches-heading" className="flex items-center gap-2 text-lg">
                  <BriefcaseBusiness className="h-4 w-4" />
                  Issue matches
                </CardTitle>
                <CardDescription>
                  High-signal open-source opportunities ranked against your profile and tracked intel.
                </CardDescription>
              </div>
              <div className="grid grid-cols-2 gap-2 sm:flex">
                <Select value={String(days)} onValueChange={(value) => setDays(Number(value))}>
                  <SelectTrigger className="w-full sm:w-[120px]">
                    <SelectValue placeholder="Window" />
                  </SelectTrigger>
                  <SelectContent>
                    {DAY_OPTIONS.map((option) => (
                      <SelectItem key={option} value={String(option)}>
                        Last {option} days
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Select value={String(limit)} onValueChange={(value) => setLimit(Number(value))}>
                  <SelectTrigger className="w-full sm:w-[120px]">
                    <SelectValue placeholder="Results" />
                  </SelectTrigger>
                  <SelectContent>
                    {LIMIT_OPTIONS.map((option) => (
                      <SelectItem key={option} value={String(option)}>
                        {option} results
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </CardHeader>
            <CardContent>
              {issuesLoading ? (
                <div className="space-y-3">
                  {Array.from({ length: 3 }).map((_, index) => (
                    <div key={index} className="rounded-xl border p-4">
                      <div className="h-4 w-2/3 animate-pulse rounded bg-muted" />
                      <div className="mt-3 h-3 w-full animate-pulse rounded bg-muted" />
                      <div className="mt-2 h-3 w-5/6 animate-pulse rounded bg-muted" />
                    </div>
                  ))}
                </div>
              ) : issuesError ? (
                <div className="rounded-xl border border-destructive/40 bg-destructive/5 p-4 text-sm text-destructive">
                  <div className="flex items-start gap-2">
                    <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
                    <div>
                      <p className="font-medium">Issue matching did not load.</p>
                      <p className="mt-1 text-destructive/80">{issuesError}</p>
                    </div>
                  </div>
                </div>
              ) : issues.length === 0 ? (
                <div className="rounded-xl border border-dashed p-6 text-sm text-muted-foreground">
                  <p className="font-medium text-foreground">No issue matches yet</p>
                  <p className="mt-2">
                    The radar does not have matching GitHub issues in the current window. Refresh later or widen the time range.
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {issues.map((issue) => (
                    <article key={`${issue.url}-${issue.title}`} className="rounded-xl border p-4 shadow-sm transition-shadow hover:shadow-md">
                      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                        <div className="space-y-2">
                          <div className="flex flex-wrap items-center gap-2">
                            <Badge variant="secondary">Match {issue.match_score}/5</Badge>
                            {issue.source ? <Badge variant="outline">{issue.source.replaceAll("_", " ")}</Badge> : null}
                          </div>
                          <h2 className="text-base font-semibold leading-snug">{issue.title}</h2>
                        </div>
                        <Button asChild variant="outline" size="sm" className="shrink-0">
                          <Link href={issue.url} target="_blank" rel="noreferrer">
                            Open issue
                            <ArrowUpRight className="ml-2 h-4 w-4" />
                          </Link>
                        </Button>
                      </div>
                      {issue.summary ? (
                        <p className="mt-3 text-sm leading-6 text-muted-foreground">{issue.summary}</p>
                      ) : null}
                      {issue.tags.length > 0 ? (
                        <div className="mt-3 flex flex-wrap gap-2">
                          {issue.tags.map((tag) => (
                            <Badge key={tag} variant="outline" className="text-xs">
                              {tag}
                            </Badge>
                          ))}
                        </div>
                      ) : null}
                    </article>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </section>

        <section className="space-y-4" aria-labelledby="project-ideas-heading">
          <Card>
            <CardHeader>
              <CardTitle id="project-ideas-heading" className="flex items-center gap-2 text-lg">
                <Lightbulb className="h-4 w-4" />
                Project ideas
              </CardTitle>
              <CardDescription>
                Generate side-project directions from your goals, journal, and profile context.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {ideasLoading ? (
                <div className="rounded-xl border p-4 text-sm text-muted-foreground">
                  <div className="flex items-center gap-2 font-medium text-foreground">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Generating ideas
                  </div>
                  <p className="mt-2">This usually takes a few seconds while StewardMe pulls together your context.</p>
                </div>
              ) : ideas ? (
                <div className="rounded-xl border p-4">
                  <div className="prose prose-sm dark:prose-invert max-w-none">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{ideas}</ReactMarkdown>
                  </div>
                </div>
              ) : (
                <div className="rounded-xl border border-dashed p-6 text-sm text-muted-foreground">
                  <p className="font-medium text-foreground">Generate a shortlist when you need momentum</p>
                  <p className="mt-2">
                    Use this when issue matches feel too tactical and you want a fresh project bet grounded in your current context.
                  </p>
                </div>
              )}

              {ideasError ? (
                <div className="rounded-xl border border-destructive/40 bg-destructive/5 p-4 text-sm text-destructive">
                  <div className="flex items-start gap-2">
                    <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
                    <div>
                      <p className="font-medium">Idea generation needs attention.</p>
                      <p className="mt-1 text-destructive/80">{ideasError}</p>
                    </div>
                  </div>
                </div>
              ) : null}

              <div className="rounded-xl bg-muted/40 p-4 text-sm text-muted-foreground">
                <p className="font-medium text-foreground">How to use this workspace</p>
                <ul className="mt-2 space-y-2">
                  <li>Start with issue matches when you want a narrow, executable next step.</li>
                  <li>Generate ideas when you want broader bets shaped by your goals and journal.</li>
                  <li>Move promising ideas into Goals after you choose what to pursue.</li>
                </ul>
              </div>
            </CardContent>
          </Card>
        </section>
      </div>
    </div>
  );
}
