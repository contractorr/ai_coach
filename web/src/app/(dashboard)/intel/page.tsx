"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";
import { useToken } from "@/hooks/useToken";
import {
  Bookmark,
  ChevronDown,
  ChevronRight,
  ExternalLink,
  Heart,
  Newspaper,
  RefreshCw,
  Search,
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { apiFetch } from "@/lib/api";

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

function HealthDashboard({ token, refreshKey }: { token: string; refreshKey: number }) {
  const [health, setHealth] = useState<ScraperHealth[]>([]);
  const [expanded, setExpanded] = useState(false);
  const [loaded, setLoaded] = useState(false);

  const loadHealth = () => {
    apiFetch<{ scrapers: ScraperHealth[] }>("/api/intel/health", {}, token)
      .then((d) => setHealth(d.scrapers))
      .catch(() => {})
      .finally(() => setLoaded(true));
  };

  useEffect(loadHealth, [token, refreshKey]);

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

function TrendingTab({ token, refreshKey }: { token: string; refreshKey: number }) {
  const [snapshot, setSnapshot] = useState<TrendingSnapshot | null>(null);
  const [loading, setLoading] = useState(true);

  const loadTrending = () => {
    setLoading(true);
    apiFetch<TrendingSnapshot>("/api/intel/trending", {}, token)
      .then(setSnapshot)
      .catch((e) => toast.error(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(loadTrending, [token, refreshKey]);

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

export default function IntelPage() {
  const token = useToken();
  const [items, setItems] = useState<IntelItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [scraping, setScraping] = useState(false);
  const [trendingKey, setTrendingKey] = useState(0);
  const [visibleCount, setVisibleCount] = useState(FEED_PAGE_SIZE);
  const [savingUrl, setSavingUrl] = useState<string | null>(null);
  const [notingUrl, setNotingUrl] = useState<string | null>(null);

  const loadRecent = () => {
    if (!token) {
      setLoading(false);
      return;
    }
    apiFetch<IntelItem[]>("/api/intel/recent?limit=50", {}, token)
      .then((data) => { setItems(data); setVisibleCount(FEED_PAGE_SIZE); })
      .catch((e) => toast.error(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(loadRecent, [token]);

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
    setNotingUrl(item.url);
    try {
      const draft = window.prompt("Add a short note for later follow-up", item.follow_up?.note || "");
      if (draft == null) return;
      await upsertFollowUp(item, item.follow_up?.saved ?? true, draft);
      toast.success(draft.trim() ? "Note saved" : "Note cleared");
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setNotingUrl(null);
    }
  };

  return (
    <div className="mx-auto max-w-5xl space-y-6 p-4 md:p-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Radar</h1>
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
      {token && <HealthDashboard token={token} refreshKey={trendingKey} />}

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
        </TabsList>

        <TabsContent value="trending">
          {token && <TrendingTab token={token} refreshKey={trendingKey} />}
        </TabsContent>

        <TabsContent value="feed">
          {/* Search */}
          <div className="flex gap-2 mb-4">
            <div className="relative max-w-md flex-1">
              <Input
                placeholder="Search your radar..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSearch()}
              />
              {query && (
                <button
                  onClick={() => { setQuery(""); loadRecent(); }}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  <X className="h-3.5 w-3.5" />
                </button>
              )}
            </div>
            <Button variant="outline" onClick={handleSearch}>
              <Search className="h-4 w-4" />
            </Button>
          </div>

          {/* Loading */}
          {loading && (
            <div className="space-y-3">
              {Array.from({ length: 5 }).map((_, i) => (
                <IntelSkeleton key={i} />
              ))}
            </div>
          )}

          {/* Empty state */}
          {!loading && items.length === 0 && (
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-muted">
                <Newspaper className="h-7 w-7 text-muted-foreground" />
              </div>
              <h3 className="text-lg font-medium">No recent items</h3>
              <p className="mt-1 max-w-sm text-sm text-muted-foreground">
                No feed items found. Run a scan to pull in the latest signals from
                Hacker News, GitHub, arXiv, and RSS feeds. Check the Trending tab
                for clustered topics.
              </p>
              <Button
                variant="outline"
                className="mt-4"
                onClick={handleScrape}
                disabled={scraping}
              >
                <RefreshCw className={`mr-2 h-4 w-4 ${scraping ? "animate-spin" : ""}`} />
                {scraping ? "Scanning..." : "Run First Scan"}
              </Button>
            </div>
          )}

          {/* Items */}
          {!loading && items.length > 0 && (
            <div className="space-y-3">
              {items.slice(0, visibleCount).map((item, i) => (
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
              {visibleCount < items.length && (
                <div className="flex justify-center pt-2">
                  <Button
                    variant="outline"
                    onClick={() => setVisibleCount((v) => v + FEED_PAGE_SIZE)}
                  >
                    Load more ({items.length - visibleCount} remaining)
                  </Button>
                </div>
              )}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
