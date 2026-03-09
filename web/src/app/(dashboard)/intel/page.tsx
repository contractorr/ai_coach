"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import { useToken } from "@/hooks/useToken";
import {
  Bookmark,
  Briefcase,
  Building2,
  ChevronDown,
  ChevronRight,
  ExternalLink,
  Heart,
  Newspaper,
  RefreshCw,
  Search,
  ShieldAlert,
  TrendingUp,
  X,
} from "lucide-react";
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
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { apiFetch } from "@/lib/api";
import type { CompanyMovement, HiringSignal, RegulatoryAlert } from "@/types/briefing";

interface IntelItem {
  source: string;
  title: string;
  url: string;
  summary: string;
  published?: string;
  tags?: string[];
  relevance_score?: number;
  match_reasons?: string[];
  watchlist_score?: number;
  why_this_matters?: string;
  watchlist_matches?: {
    watchlist_id: string;
    label: string;
    priority: "high" | "medium" | "low";
    matched_terms: string[];
    why: string;
    score: number;
  }[];
  follow_up?: {
    url: string;
    title: string;
    saved: boolean;
    note: string;
    watchlist_ids: string[];
    created_at?: string;
    updated_at?: string;
  };
}

interface TrendingTopic {
  topic: string;
  summary?: string;
  score?: number;
  item_count: number;
  source_count: number;
  sources: string[];
  velocity?: number;
  relevance_score?: number;
  relevance_matches?: string[];
  items: { id: number; title: string; url: string; source: string; summary: string }[];
}

interface TrendingSnapshot {
  computed_at: string;
  days: number;
  total_items_scanned: number;
  method?: string;
  personalized?: boolean;
  topics: TrendingTopic[];
}

interface ScraperHealth {
  source: string;
  last_run_at: string | null;
  last_success_at: string | null;
  consecutive_errors: number;
  total_runs: number;
  total_errors: number;
  last_error: string | null;
  backoff_until: string | null;
}

type FeedFilter = "all" | "for_you" | "watchlist" | "saved";

function timeAgo(dateStr: string | null): string {
  if (!dateStr) return "never";
  const diff = Date.now() - new Date(dateStr).getTime();
  const hours = Math.floor(diff / 3600000);
  if (hours < 1) return "< 1h ago";
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

function healthColor(h: ScraperHealth): "green" | "yellow" | "red" {
  if (h.consecutive_errors >= 3) return "red";
  if (h.last_success_at) {
    const hoursSinceSuccess =
      (Date.now() - new Date(h.last_success_at).getTime()) / 3600000;
    if (hoursSinceSuccess > 72) return "red";
  } else if (h.total_runs > 0) {
    return "red";
  }
  if (h.consecutive_errors > 0) return "yellow";
  return "green";
}

const dotColors = {
  green: "bg-success",
  yellow: "bg-warning",
  red: "bg-destructive",
};

function HealthDashboard({ token }: { token: string }) {
  const [health, setHealth] = useState<ScraperHealth[]>([]);
  const [expanded, setExpanded] = useState(false);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    let cancelled = false;

    apiFetch<{ scrapers: ScraperHealth[] }>("/api/intel/health", {}, token)
      .then((data) => {
        if (!cancelled) setHealth(data.scrapers);
      })
      .catch(() => {})
      .finally(() => {
        if (!cancelled) setLoaded(true);
      });

    return () => {
      cancelled = true;
    };
  }, [token]);

  if (!loaded || health.length === 0) return null;

  const healthyCount = health.filter((h) => healthColor(h) === "green").length;

  return (
    <Card>
      <CardHeader
        className="cursor-pointer pb-3"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Heart className="h-4 w-4 text-muted-foreground" />
            <CardTitle className="text-base">Source health</CardTitle>
            <Badge variant={healthyCount === health.length ? "secondary" : "destructive"}>
              {healthyCount}/{health.length} healthy
            </Badge>
          </div>
          {expanded ? (
            <ChevronDown className="h-4 w-4 text-muted-foreground" />
          ) : (
            <ChevronRight className="h-4 w-4 text-muted-foreground" />
          )}
        </div>
      </CardHeader>
      {expanded && (
        <CardContent>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {health.map((h) => {
              const color = healthColor(h);
              return (
                <div
                  key={h.source}
                  className="rounded-xl border p-3 text-sm transition-shadow hover:shadow-md"
                >
                  <div className="flex items-center gap-2">
                    <span className={`h-2.5 w-2.5 rounded-full ${dotColors[color]}`} />
                    <span className="font-medium">{h.source}</span>
                  </div>
                  <div className="mt-2 space-y-0.5 text-xs text-muted-foreground">
                    <p>Last scan: {timeAgo(h.last_success_at)}</p>
                    <p>
                      Runs: {h.total_runs} | Errors: {h.total_errors}
                    </p>
                    {h.last_error && (
                      <p className="truncate text-destructive" title={h.last_error}>
                        {h.last_error.slice(0, 80)}
                      </p>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      )}
    </Card>
  );
}

function TrendingTab({ token }: { token: string }) {
  const [snapshot, setSnapshot] = useState<TrendingSnapshot | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    apiFetch<TrendingSnapshot>("/api/intel/trending", {}, token)
      .then((data) => {
        if (!cancelled) setSnapshot(data);
      })
      .catch((e) => toast.error(e.message))
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [token]);

  if (loading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="h-24 animate-pulse rounded-lg bg-muted" />
        ))}
      </div>
    );
  }

  if (!snapshot || snapshot.topics.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-muted">
          <TrendingUp className="h-7 w-7 text-muted-foreground" />
        </div>
        <h3 className="text-lg font-medium">No trending topics yet</h3>
        <p className="mt-1 max-w-sm text-sm text-muted-foreground">
          Topics appear here when the same term shows up across multiple sources.
          Run a scan first to populate the feed.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <p className="text-xs text-muted-foreground">
        {snapshot.total_items_scanned} items scanned &middot; {snapshot.days}d window
      </p>
      {snapshot.topics.map((t, idx) => (
        <Card key={t.topic + idx}>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">{t.topic}</CardTitle>
            {t.summary && (
              <p className="text-sm text-muted-foreground">{t.summary}</p>
            )}
            {!t.summary && t.score != null && (
              <div className="flex items-center gap-2">
                <div className="h-1.5 flex-1 rounded-full bg-muted">
                  <div
                    className="h-full rounded-full bg-foreground/70"
                    style={{ width: `${Math.round(t.score * 100)}%` }}
                  />
                </div>
                <span className="text-sm font-medium tabular-nums">
                  {(t.score * 100).toFixed(0)}
                </span>
              </div>
            )}
            <CardDescription className="flex flex-wrap gap-1">
              {t.relevance_score != null && t.relevance_score > 0.1 && (
                <Badge variant="default" className="text-xs bg-primary/80">For you</Badge>
              )}
              {t.sources.map((s) => (
                <Badge key={s} variant="outline" className={`text-xs ${sourceBadgeClass(s)}`}>
                  {s}
                </Badge>
              ))}
              <span className="text-xs text-muted-foreground">
                {t.item_count} items
              </span>
              {t.relevance_matches && t.relevance_matches.length > 0 && (
                <span className="text-xs text-muted-foreground">
                  &middot; matches: {t.relevance_matches.slice(0, 3).join(", ")}
                </span>
              )}
            </CardDescription>
          </CardHeader>
          {t.items.length > 0 && (
            <CardContent className="space-y-1.5">
              {t.items.slice(0, 2).map((item) => (
                <a
                  key={item.id}
                  href={item.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block text-sm hover:underline"
                >
                  {item.title}
                  <ExternalLink className="ml-1 inline h-3 w-3 text-muted-foreground" />
                </a>
              ))}
            </CardContent>
          )}
        </Card>
      ))}
    </div>
  );
}

function PipelinesTab({ token }: { token: string }) {
  const [companyMovements, setCompanyMovements] = useState<CompanyMovement[]>([]);
  const [hiringSignals, setHiringSignals] = useState<HiringSignal[]>([]);
  const [regulatoryAlerts, setRegulatoryAlerts] = useState<RegulatoryAlert[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    Promise.all([
      apiFetch<CompanyMovement[]>("/api/intel/company-movements?limit=8", {}, token),
      apiFetch<HiringSignal[]>("/api/intel/hiring-signals?limit=8", {}, token),
      apiFetch<RegulatoryAlert[]>("/api/intel/regulatory-alerts?limit=8", {}, token),
    ])
      .then(([movements, hiring, regulatory]) => {
        if (cancelled) return;
        setCompanyMovements(movements);
        setHiringSignals(hiring);
        setRegulatoryAlerts(regulatory);
      })
      .catch((e) => {
        if (!cancelled) toast.error(e.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [token]);

  const totalSignals = companyMovements.length + hiringSignals.length + regulatoryAlerts.length;

  if (loading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="h-24 animate-pulse rounded-lg bg-muted" />
        ))}
      </div>
    );
  }

  if (totalSignals === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Pipeline signals are quiet</CardTitle>
          <CardDescription>
            Add companies, sectors, or regulatory topics to your watchlist in Settings, then run a fresh scan to populate these focused views.
          </CardDescription>
        </CardHeader>
      </Card>
    );
  }

  const sections = [
    {
      key: "company-movements",
      title: "Company Movements",
      description: "Strategic company changes matched back to watched companies.",
      icon: Building2,
      items: companyMovements,
      renderMeta: (item: CompanyMovement) => [item.company_label, item.movement_type, `${Math.round(item.significance * 100)}% significance`],
    },
    {
      key: "hiring-signals",
      title: "Hiring Signals",
      description: "Hiring changes that may hint at expansion, focus shifts, or new bets.",
      icon: Briefcase,
      items: hiringSignals,
      renderMeta: (item: HiringSignal) => [item.entity_label, item.signal_type, `${Math.round(item.strength * 100)}% strength`],
    },
    {
      key: "regulatory-alerts",
      title: "Regulatory Alerts",
      description: "Policy and standards updates filtered to your watched topics and geographies.",
      icon: ShieldAlert,
      items: regulatoryAlerts,
      renderMeta: (item: RegulatoryAlert) => [item.change_type, item.urgency, `${Math.round(item.relevance * 100)}% relevance`],
    },
  ] as const;

  return (
    <div className="space-y-4">
      <div className="grid gap-3 lg:grid-cols-3">
        <Card className="gap-3 py-4">
          <CardHeader className="px-4 pb-0">
            <CardDescription className="text-xs uppercase tracking-wide">Company</CardDescription>
            <CardTitle className="text-2xl">{companyMovements.length}</CardTitle>
          </CardHeader>
          <CardContent className="px-4 text-xs text-muted-foreground">
            Recent company movement cards matched to watched companies.
          </CardContent>
        </Card>
        <Card className="gap-3 py-4">
          <CardHeader className="px-4 pb-0">
            <CardDescription className="text-xs uppercase tracking-wide">Hiring</CardDescription>
            <CardTitle className="text-2xl">{hiringSignals.length}</CardTitle>
          </CardHeader>
          <CardContent className="px-4 text-xs text-muted-foreground">
            Hiring signals derived from your watched companies.
          </CardContent>
        </Card>
        <Card className="gap-3 py-4">
          <CardHeader className="px-4 pb-0">
            <CardDescription className="text-xs uppercase tracking-wide">Regulatory</CardDescription>
            <CardTitle className="text-2xl">{regulatoryAlerts.length}</CardTitle>
          </CardHeader>
          <CardContent className="px-4 text-xs text-muted-foreground">
            Regulatory alerts relevant to watched sectors, topics, and geographies.
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 xl:grid-cols-3">
        {sections.map((section) => {
          const Icon = section.icon;
          return (
            <Card key={section.key}>
              <CardHeader>
                <div className="flex items-center gap-2">
                  <Icon className="h-4 w-4 text-muted-foreground" />
                  <CardTitle className="text-base">{section.title}</CardTitle>
                </div>
                <CardDescription>{section.description}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {section.items.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No signals yet.</p>
                ) : (
                  section.items.map((item) => {
                    const sourceUrl = item.source_url;
                    const title = item.title;
                    const summary = item.summary;
                    const observedAt = item.observed_at;
                    const metaValues =
                      section.key === "company-movements"
                        ? section.renderMeta(item as CompanyMovement)
                        : section.key === "hiring-signals"
                          ? section.renderMeta(item as HiringSignal)
                          : section.renderMeta(item as RegulatoryAlert);
                    return (
                      <div key={`${section.key}-${item.id}`} className="rounded-lg border p-3">
                        <div className="flex items-start justify-between gap-3">
                          <div className="space-y-1">
                            {sourceUrl ? (
                              <a
                                href={sourceUrl}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-sm font-medium hover:underline"
                              >
                                {title}
                                <ExternalLink className="ml-1 inline h-3 w-3 text-muted-foreground" />
                              </a>
                            ) : (
                              <div className="text-sm font-medium">{title}</div>
                            )}
                            <p className="text-sm text-muted-foreground">{summary}</p>
                          </div>
                          <span className="shrink-0 text-xs text-muted-foreground">{timeAgo(observedAt)}</span>
                        </div>
                        <div className="mt-2 flex flex-wrap gap-1">
                          {metaValues.filter(Boolean).map((value) => (
                            <Badge key={`${section.key}-${item.id}-${value}`} variant="outline" className="text-[10px]">
                              {value}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    );
                  })
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}

const sourceColors: Record<string, string> = {
  hackernews: "bg-orange-500/15 text-orange-600 dark:text-orange-400 border-orange-500/25",
  hn: "bg-orange-500/15 text-orange-600 dark:text-orange-400 border-orange-500/25",
  reddit: "bg-blue-500/15 text-blue-600 dark:text-blue-400 border-blue-500/25",
  arxiv: "bg-red-500/15 text-red-600 dark:text-red-400 border-red-500/25",
  github: "bg-gray-500/15 text-gray-600 dark:text-gray-400 border-gray-500/25",
  rss: "bg-amber-500/15 text-amber-600 dark:text-amber-400 border-amber-500/25",
};

function sourceBadgeClass(source: string): string {
  const key = source.toLowerCase().replace(/[_\s-]/g, "");
  return sourceColors[key] || "";
}

function IntelSkeleton() {
  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="h-4 w-3/4 animate-pulse rounded bg-muted" />
        <div className="flex gap-2">
          <div className="h-5 w-16 animate-pulse rounded bg-muted" />
          <div className="h-4 w-20 animate-pulse rounded bg-muted" />
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-1.5">
          <div className="h-3 w-full animate-pulse rounded bg-muted" />
          <div className="h-3 w-2/3 animate-pulse rounded bg-muted" />
        </div>
      </CardContent>
    </Card>
  );
}

const FEED_PAGE_SIZE = 15;

function isForYou(item: IntelItem): boolean {
  return (item.relevance_score ?? 0) > 0.1;
}

function hasWatchlistMatch(item: IntelItem): boolean {
  return Boolean(item.watchlist_matches && item.watchlist_matches.length > 0);
}

function isSavedForFollowUp(item: IntelItem): boolean {
  return Boolean(item.follow_up?.saved);
}

export default function IntelPage() {
  const token = useToken();
  const [items, setItems] = useState<IntelItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [feedFilter, setFeedFilter] = useState<FeedFilter>("all");
  const [scraping, setScraping] = useState(false);
  const [trendingKey, setTrendingKey] = useState(0);
  const [visibleCount, setVisibleCount] = useState(FEED_PAGE_SIZE);
  const [savingUrl, setSavingUrl] = useState<string | null>(null);
  const [notingUrl, setNotingUrl] = useState<string | null>(null);
  const [noteItem, setNoteItem] = useState<IntelItem | null>(null);
  const [noteDraft, setNoteDraft] = useState("");

  const loadRecent = useCallback(() => {
    if (!token) {
      setLoading(false);
      return;
    }
    apiFetch<IntelItem[]>("/api/intel/recent?limit=50", {}, token)
      .then((data) => { setItems(data); setVisibleCount(FEED_PAGE_SIZE); })
      .catch((e) => toast.error(e.message))
      .finally(() => setLoading(false));
  }, [token]);

  useEffect(() => {
    loadRecent();
  }, [loadRecent]);

  useEffect(() => {
    setVisibleCount(FEED_PAGE_SIZE);
  }, [feedFilter]);

  const handleSearch = async () => {
    if (!token || !query.trim()) {
      loadRecent();
      return;
    }
    setLoading(true);
    try {
      const results = await apiFetch<IntelItem[]>(
        `/api/intel/search?q=${encodeURIComponent(query)}&limit=20`,
        {},
        token
      );
      setItems(results);
      setVisibleCount(FEED_PAGE_SIZE);
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const handleScrape = async () => {
    if (!token) return;
    setScraping(true);
    try {
      await apiFetch("/api/intel/scrape", { method: "POST" }, token);
      toast.success("Scrape completed");
      loadRecent();
      setTrendingKey((k) => k + 1);
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setScraping(false);
    }
  };

  const upsertFollowUp = async (item: IntelItem, saved: boolean, note: string) => {
    if (!token) return;
    const watchlistIds = (item.watchlist_matches || []).map((match) => match.watchlist_id);
    const entry = await apiFetch<IntelItem["follow_up"]>(
      "/api/intel/follow-ups",
      {
        method: "PUT",
        body: JSON.stringify({
          url: item.url,
          title: item.title,
          saved,
          note,
          watchlist_ids: watchlistIds,
        }),
      },
      token
    );
    setItems((prev) => prev.map((existing) => (
      existing.url === item.url ? { ...existing, follow_up: entry } : existing
    )));
  };

  const handleSaveItem = async (item: IntelItem) => {
    setSavingUrl(item.url);
    try {
      const nextSaved = !item.follow_up?.saved;
      await upsertFollowUp(item, nextSaved, item.follow_up?.note || "");
      toast.success(nextSaved ? "Saved for follow-up" : "Removed from saved items");
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setSavingUrl(null);
    }
  };

  const handleNoteItem = async (item: IntelItem) => {
    setNoteItem(item);
    setNoteDraft(item.follow_up?.note || "");
  };

  const handleSaveNote = async () => {
    if (!noteItem) return;
    setNotingUrl(noteItem.url);
    try {
      const trimmedDraft = noteDraft.trim();
      await upsertFollowUp(noteItem, noteItem.follow_up?.saved ?? true, trimmedDraft);
      toast.success(trimmedDraft ? "Note saved" : "Note cleared");
      setNoteItem(null);
      setNoteDraft("");
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setNotingUrl(null);
    }
  };

  const feedCounts = useMemo(
    () => ({
      all: items.length,
      for_you: items.filter(isForYou).length,
      watchlist: items.filter(hasWatchlistMatch).length,
      saved: items.filter(isSavedForFollowUp).length,
    }),
    [items]
  );

  const filteredItems = useMemo(
    () => items.filter((item) => {
      if (feedFilter === "for_you") return isForYou(item);
      if (feedFilter === "watchlist") return hasWatchlistMatch(item);
      if (feedFilter === "saved") return isSavedForFollowUp(item);
      return true;
    }),
    [feedFilter, items]
  );

  const filterOptions: Array<{ value: FeedFilter; label: string; count: number }> = [
    { value: "all", label: "All", count: feedCounts.all },
    { value: "for_you", label: "For you", count: feedCounts.for_you },
    { value: "watchlist", label: "Watchlist", count: feedCounts.watchlist },
    { value: "saved", label: "Saved", count: feedCounts.saved },
  ];

  const feedEmptyState = (() => {
    if (query.trim()) {
      return {
        title: "No matches for that search",
        description: "Try a broader keyword or clear the search to return to your recent radar feed.",
      };
    }

    if (feedFilter === "for_you") {
      return {
        title: "No personalized items yet",
        description: "As your profile, goals, and journal sharpen, highly relevant intel will surface here.",
      };
    }

    if (feedFilter === "watchlist") {
      return {
        title: "No watchlist matches yet",
        description: "Run a fresh scan or expand your watchlist to pull in more bespoke signals.",
      };
    }

    if (feedFilter === "saved") {
      return {
        title: "No saved follow-ups yet",
        description: "Save interesting signals here so you can come back and work through them later.",
      };
    }

    return {
      title: "No recent items",
      description: "Run a scan to pull in the latest signals from your sources, then use the filters to work the feed.",
    };
  })();

  return (
    <div className="mx-auto max-w-5xl space-y-6 p-4 md:p-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="space-y-1">
          <h1 className="text-2xl font-semibold">Radar</h1>
          <p className="text-sm text-muted-foreground">
            Scan the market, surface what matters to you, and save follow-up signals without leaving the feed.
          </p>
        </div>
        <Button
          variant="outline"
          onClick={handleScrape}
          disabled={scraping}
        >
          <RefreshCw className={`mr-2 h-4 w-4 ${scraping ? "animate-spin" : ""}`} />
          {scraping ? "Scanning..." : "Scan Now"}
        </Button>
      </div>

      {/* Scraper Health */}
      {token && <HealthDashboard key={`health-${trendingKey}`} token={token} />}

      <Tabs defaultValue="trending" id="radar-tabs">
        <TabsList>
          <TabsTrigger value="trending">
            <TrendingUp className="mr-1 h-4 w-4" />
            Trending
          </TabsTrigger>
          <TabsTrigger value="feed">
            <Newspaper className="mr-1 h-4 w-4" />
            Feed
          </TabsTrigger>
          <TabsTrigger value="pipelines">
            <Building2 className="mr-1 h-4 w-4" />
            Pipelines
          </TabsTrigger>
        </TabsList>

        <TabsContent value="trending">
          {token && <TrendingTab key={`trending-${trendingKey}`} token={token} />}
        </TabsContent>

        <TabsContent value="pipelines">
          {token && <PipelinesTab key={`pipelines-${trendingKey}`} token={token} />}
        </TabsContent>

        <TabsContent value="feed">
          <div className="mb-4 grid gap-3 lg:grid-cols-3">
            <Card className="gap-3 py-4">
              <CardHeader className="px-4 pb-0">
                <CardDescription className="text-xs uppercase tracking-wide">Loaded</CardDescription>
                <CardTitle className="text-2xl">{feedCounts.all}</CardTitle>
              </CardHeader>
              <CardContent className="px-4 text-xs text-muted-foreground">
                Recent or searched items currently in your feed workspace.
              </CardContent>
            </Card>
            <Card className="gap-3 py-4">
              <CardHeader className="px-4 pb-0">
                <CardDescription className="text-xs uppercase tracking-wide">For you</CardDescription>
                <CardTitle className="text-2xl">{feedCounts.for_you}</CardTitle>
              </CardHeader>
              <CardContent className="px-4 text-xs text-muted-foreground">
                Signals with stronger profile or goal relevance.
              </CardContent>
            </Card>
            <Card className="gap-3 py-4">
              <CardHeader className="px-4 pb-0">
                <CardDescription className="text-xs uppercase tracking-wide">Saved</CardDescription>
                <CardTitle className="text-2xl">{feedCounts.saved}</CardTitle>
              </CardHeader>
              <CardContent className="px-4 text-xs text-muted-foreground">
                Follow-up items you have explicitly kept for later.
              </CardContent>
            </Card>
          </div>

          <Card className="gap-3 py-4">
            <CardContent className="flex flex-col gap-3 px-4">
              <div className="flex flex-wrap gap-2">
                {filterOptions.map((option) => (
                  <Button
                    key={option.value}
                    size="sm"
                    variant={feedFilter === option.value ? "default" : "outline"}
                    onClick={() => setFeedFilter(option.value)}
                  >
                    {option.label}
                    <Badge
                      variant={feedFilter === option.value ? "secondary" : "outline"}
                      className="ml-1"
                    >
                      {option.count}
                    </Badge>
                  </Button>
                ))}
              </div>

              <div className="flex flex-col gap-2 sm:flex-row">
                <div className="relative max-w-2xl flex-1">
                  <Input
                    placeholder="Search your radar..."
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                    className="pr-9"
                  />
                  {query && (
                    <button
                      onClick={() => {
                        setQuery("");
                        loadRecent();
                      }}
                      className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                    >
                      <X className="h-3.5 w-3.5" />
                    </button>
                  )}
                </div>
                <Button variant="outline" onClick={handleSearch}>
                  <Search className="h-4 w-4" />
                  Search
                </Button>
                {(feedFilter !== "all" || query.trim()) && (
                  <Button
                    variant="ghost"
                    onClick={() => {
                      setFeedFilter("all");
                      if (query.trim()) {
                        setQuery("");
                        loadRecent();
                      }
                    }}
                  >
                    Reset
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>

          <p className="text-sm text-muted-foreground">
            {filteredItems.length === items.length
              ? `${items.length} items in view`
              : `Showing ${filteredItems.length} of ${items.length} items`}
          </p>

          {/* Loading */}
          {loading && (
            <div className="space-y-3">
              {Array.from({ length: 5 }).map((_, i) => (
                <IntelSkeleton key={i} />
              ))}
            </div>
          )}

          {/* Empty state */}
          {!loading && filteredItems.length === 0 && (
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-muted">
                <Newspaper className="h-7 w-7 text-muted-foreground" />
              </div>
              <h3 className="text-lg font-medium">{feedEmptyState.title}</h3>
              <p className="mt-1 max-w-sm text-sm text-muted-foreground">
                {feedEmptyState.description}
              </p>
              <div className="mt-4 flex flex-wrap justify-center gap-2">
                <Button
                  variant="outline"
                  onClick={handleScrape}
                  disabled={scraping}
                >
                  <RefreshCw className={`mr-2 h-4 w-4 ${scraping ? "animate-spin" : ""}`} />
                  {scraping ? "Scanning..." : query.trim() ? "Run fresh scan" : "Run First Scan"}
                </Button>
                {(feedFilter !== "all" || query.trim()) && (
                  <Button
                    variant="ghost"
                    onClick={() => {
                      setFeedFilter("all");
                      if (query.trim()) {
                        setQuery("");
                        loadRecent();
                      }
                    }}
                  >
                    Reset filters
                  </Button>
                )}
              </div>
            </div>
          )}

          {/* Items */}
          {!loading && filteredItems.length > 0 && (
            <div className="space-y-3">
              {filteredItems.slice(0, visibleCount).map((item, i) => (
                <Card key={i}>
                  <CardHeader className="pb-2">
                    <div className="flex items-start justify-between">
                      <div>
                        <CardTitle className="text-base">
                          <a
                            href={item.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="hover:underline"
                          >
                            {item.title}
                            <ExternalLink className="ml-1 inline h-3 w-3" />
                          </a>
                        </CardTitle>
                        <CardDescription className="flex flex-wrap items-center gap-2">
                          <Badge variant="outline" className={sourceBadgeClass(item.source)}>{item.source}</Badge>
                          {item.relevance_score != null && item.relevance_score > 0.1 && (
                            <Badge variant="default" className="text-xs bg-primary/80">For you</Badge>
                          )}
                          {item.watchlist_matches && item.watchlist_matches.length > 0 && (
                            <Badge variant="default" className="text-xs bg-emerald-600/90">
                              Watchlist: {item.watchlist_matches[0].label}
                            </Badge>
                          )}
                          {item.published && (
                            <span>{new Date(item.published).toLocaleDateString()}</span>
                          )}
                          {item.match_reasons && item.match_reasons.length > 0 && (
                            <span className="text-xs text-muted-foreground">
                              &middot; {item.match_reasons.slice(0, 3).join(", ")}
                            </span>
                          )}
                        </CardDescription>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground">{item.summary}</p>
                    {item.why_this_matters && (
                      <div className="mt-3 rounded-lg border border-emerald-500/20 bg-emerald-500/5 p-3">
                        <p className="text-xs font-medium uppercase tracking-wide text-emerald-700 dark:text-emerald-300">
                          Why this matters to you
                        </p>
                        <p className="mt-1 text-sm text-muted-foreground">{item.why_this_matters}</p>
                      </div>
                    )}
                    {item.tags && item.tags.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1">
                        {item.tags.map((t) => (
                          <Badge key={t} variant="secondary" className="text-xs">
                            {t}
                          </Badge>
                        ))}
                      </div>
                    )}
                    {item.watchlist_matches && item.watchlist_matches.length > 1 && (
                      <div className="mt-2 flex flex-wrap gap-1">
                        {item.watchlist_matches.slice(1).map((match) => (
                          <Badge key={match.watchlist_id} variant="outline" className="text-xs">
                            Also matched: {match.label}
                          </Badge>
                        ))}
                      </div>
                    )}
                    <div className="mt-3 flex flex-wrap gap-2">
                      <Button
                        size="sm"
                        variant={item.follow_up?.saved ? "default" : "outline"}
                        onClick={() => handleSaveItem(item)}
                        disabled={savingUrl === item.url}
                      >
                        <Bookmark className="mr-1 h-3 w-3" />
                        {savingUrl === item.url ? "Saving..." : item.follow_up?.saved ? "Saved" : "Save"}
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleNoteItem(item)}
                        disabled={notingUrl === item.url}
                      >
                        {notingUrl === item.url ? "Saving note..." : item.follow_up?.note ? "Edit Note" : "Add Note"}
                      </Button>
                    </div>
                    {item.follow_up?.note && (
                      <p className="mt-2 text-sm text-muted-foreground">Note: {item.follow_up.note}</p>
                    )}
                  </CardContent>
                </Card>
              ))}
              {visibleCount < filteredItems.length && (
                <div className="flex justify-center pt-2">
                  <Button
                    variant="outline"
                    onClick={() => setVisibleCount((v) => v + FEED_PAGE_SIZE)}
                  >
                    Load more ({filteredItems.length - visibleCount} remaining)
                  </Button>
                </div>
              )}
            </div>
          )}
        </TabsContent>
      </Tabs>

      <Sheet open={Boolean(noteItem)} onOpenChange={(open) => {
        if (!open) {
          setNoteItem(null);
          setNoteDraft("");
        }
      }}>
        <SheetContent className="sm:max-w-lg">
          <SheetHeader>
            <SheetTitle>Follow-up note</SheetTitle>
            <SheetDescription>
              Save a short reminder so this signal turns into an action instead of disappearing in the feed.
            </SheetDescription>
          </SheetHeader>

          <div className="space-y-4 px-6 pb-2">
            <div className="space-y-1">
              <Label>Item</Label>
              <p className="text-sm font-medium">{noteItem?.title}</p>
              {noteItem && (
                <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                  <Badge variant="outline" className={sourceBadgeClass(noteItem.source)}>
                    {noteItem.source}
                  </Badge>
                  {hasWatchlistMatch(noteItem) && (
                    <Badge variant="outline">Watchlist match</Badge>
                  )}
                  {isForYou(noteItem) && (
                    <Badge variant="outline">For you</Badge>
                  )}
                </div>
              )}
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="intel-note">Note</Label>
              <Textarea
                id="intel-note"
                rows={8}
                placeholder="What should you remember or do next?"
                value={noteDraft}
                onChange={(e) => setNoteDraft(e.target.value)}
              />
              <p className="text-xs text-muted-foreground">
                Saving a note also keeps the item in your follow-up list if it was not already saved.
              </p>
            </div>
          </div>

          <SheetFooter>
            <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
              <Button
                variant="ghost"
                onClick={() => {
                  setNoteItem(null);
                  setNoteDraft("");
                }}
              >
                Cancel
              </Button>
              <Button
                variant="outline"
                disabled={!noteDraft.trim() && !(noteItem?.follow_up?.note || "").trim()}
                onClick={() => setNoteDraft("")}
              >
                Clear draft
              </Button>
              <Button onClick={handleSaveNote} disabled={!noteItem || notingUrl === noteItem.url}>
                {notingUrl === noteItem?.url ? "Saving..." : "Save note"}
              </Button>
            </div>
          </SheetFooter>
        </SheetContent>
      </Sheet>
    </div>
  );
}
