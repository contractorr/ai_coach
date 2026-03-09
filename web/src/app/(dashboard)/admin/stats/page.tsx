"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useToken } from "@/hooks/useToken";
import { apiFetch } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { WorkspacePageHeader } from "@/components/WorkspacePageHeader";

interface ScraperHealth {
  source: string;
  last_run: string;
  avg_items: number;
  runs: number;
}

interface PageView {
  path: string;
  count: number;
}

interface FeedbackCategory {
  positive: number;
  negative: number;
}

interface UsageStats {
  days: number;
  chat_queries: number;
  avg_latency_ms: number | null;
  active_users_7d: number;
  event_counts: Record<string, number>;
  recommendation_feedback: Record<string, FeedbackCategory>;
  scraper_health: ScraperHealth[];
  page_views: PageView[];
}

const DAY_OPTIONS = [7, 30, 90] as const;

export default function AdminStatsPage() {
  const token = useToken();
  const router = useRouter();
  const [stats, setStats] = useState<UsageStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [days, setDays] = useState<number>(30);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const loadStats = (d: number) => {
    if (!token) return;
    setLoading(true);
    apiFetch<UsageStats>(`/api/admin/stats?days=${d}`, {}, token)
      .then((data) => {
        setStats(data);
        setLastUpdated(new Date());
      })
      .catch((e) => {
        if (e.message?.includes("403")) {
          router.push("/home");
          return;
        }
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadStats(days);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token, days]);

  if (loading && !stats) {
    return (
      <div className="flex items-center justify-center py-20 text-muted-foreground">
        Loading stats...
      </div>
    );
  }

  if (!stats) return null;

  return (
    <div className="space-y-6 p-4 md:p-6">
      <WorkspacePageHeader
        eyebrow="Internal"
        title="Usage analytics"
        description="Monitor recent product activity, scraper health, and feedback signals without leaving the admin workspace."
        badge={`${days}-day window`}
        actions={
          <>
            {DAY_OPTIONS.map((d) => (
              <Button
                key={d}
                size="sm"
                variant={days === d ? "default" : "outline"}
                onClick={() => setDays(d)}
              >
                {d}d
              </Button>
            ))}
            <Button size="sm" variant="outline" onClick={() => loadStats(days)}>
              Refresh
            </Button>
          </>
        }
      />

      {lastUpdated && (
        <p className="text-xs text-muted-foreground">
          Last updated: {lastUpdated.toLocaleTimeString()}
        </p>
      )}

      {/* Top row: stat cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Chat queries</CardDescription>
            <CardTitle className="text-2xl">{stats.chat_queries}</CardTitle>
          </CardHeader>
          {stats.avg_latency_ms != null && (
            <CardContent className="text-xs text-muted-foreground">
              Avg latency: {stats.avg_latency_ms}ms
            </CardContent>
          )}
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Journal entries</CardDescription>
            <CardTitle className="text-2xl">
              {stats.event_counts.journal_entry_created ?? 0}
            </CardTitle>
          </CardHeader>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Goals created</CardDescription>
            <CardTitle className="text-2xl">
              {stats.event_counts.goal_created ?? 0}
            </CardTitle>
          </CardHeader>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Onboardings</CardDescription>
            <CardTitle className="text-2xl">
              {stats.event_counts.onboarding_complete ?? 0}
            </CardTitle>
          </CardHeader>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Active users (7d)</CardDescription>
            <CardTitle className="text-2xl">{stats.active_users_7d}</CardTitle>
          </CardHeader>
        </Card>
      </div>

      {/* Scraper health */}
      {stats.scraper_health.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Scraper Health</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-muted-foreground">
                    <th className="pb-2 pr-4">Source</th>
                    <th className="pb-2 pr-4">Runs</th>
                    <th className="pb-2 pr-4">Avg items</th>
                    <th className="pb-2">Last run</th>
                  </tr>
                </thead>
                <tbody>
                  {stats.scraper_health.map((s) => (
                    <tr key={s.source} className="border-b last:border-0">
                      <td className="py-1.5 pr-4 font-medium">{s.source}</td>
                      <td className="py-1.5 pr-4">{s.runs}</td>
                      <td className="py-1.5 pr-4">{s.avg_items}</td>
                      <td className="py-1.5 text-muted-foreground">
                        {s.last_run ? new Date(s.last_run).toLocaleDateString() : "-"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Page views */}
      {stats.page_views.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Page Views</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-muted-foreground">
                    <th className="pb-2 pr-4">Path</th>
                    <th className="pb-2">Views</th>
                  </tr>
                </thead>
                <tbody>
                  {stats.page_views.map((p) => (
                    <tr key={p.path} className="border-b last:border-0">
                      <td className="py-1.5 pr-4 font-mono">{p.path}</td>
                      <td className="py-1.5">{p.count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Recommendation feedback */}
      {Object.keys(stats.recommendation_feedback).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Recommendation Feedback</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {Object.entries(stats.recommendation_feedback).map(
                ([cat, fb]) => (
                  <div key={cat} className="rounded-lg border p-3">
                    <div className="mb-1 font-medium">{cat || "uncategorized"}</div>
                    <div className="flex gap-2">
                      <Badge variant="default">{fb.positive} useful</Badge>
                      <Badge variant="destructive">{fb.negative} irrelevant</Badge>
                    </div>
                  </div>
                )
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
