"use client";

import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useToken } from "@/hooks/useToken";
import { BookOpen, Plus, Calendar, Search, Tag, X } from "lucide-react";
import { WorkspacePageHeader } from "@/components/WorkspacePageHeader";
import { MindMapCard } from "@/components/journal/MindMapCard";
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
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { apiFetch } from "@/lib/api";
import { logEngagement } from "@/lib/engagement";

/** Strip markdown syntax for plain-text card previews. */
function stripMarkdown(text: string): string {
  return text
    .replace(/^#{1,6}\s*/gm, "")          // headings (with or without space)
    .replace(/^[-*=]{3,}\s*$/gm, "")      // horizontal rules / setext underlines
    .replace(/^\s*>\s?/gm, "")            // blockquotes
    .replace(/\*\*(.+?)\*\*/g, "$1")      // bold
    .replace(/\*(.+?)\*/g, "$1")          // italic
    .replace(/`(.+?)`/g, "$1")            // inline code
    .replace(/^\s*[-*+]\s+/gm, "")        // unordered list markers
    .replace(/^\s*\d+\.\s+/gm, "")        // ordered list markers
    .replace(/\[(.+?)\]\(.+?\)/g, "$1")   // links
    .replace(/!\[.*?\]\(.+?\)/g, "")       // images
    .replace(/\n{2,}/g, " ")              // collapse blank lines
    .trim();
}

interface JournalEntry {
  path: string;
  title: string;
  type: string;
  created: string | null;
  tags: string[];
  preview: string;
  content?: string;
}

type JournalFilter = "all" | "daily" | "project" | "goal" | "reflection";

function EntrySkeleton() {
  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div className="h-4 w-40 animate-pulse rounded bg-muted" />
          <div className="h-5 w-14 animate-pulse rounded bg-muted" />
        </div>
        <div className="h-3 w-24 animate-pulse rounded bg-muted" />
      </CardHeader>
      <CardContent>
        <div className="space-y-1.5">
          <div className="h-3 w-full animate-pulse rounded bg-muted" />
          <div className="h-3 w-3/4 animate-pulse rounded bg-muted" />
        </div>
      </CardContent>
    </Card>
  );
}

export default function JournalPage() {
  const token = useToken();
  const [entries, setEntries] = useState<JournalEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<JournalEntry | null>(null);
  const [creating, setCreating] = useState(false);
  const [sheetOpen, setSheetOpen] = useState(false);
  const [deletingPath, setDeletingPath] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [typeFilter, setTypeFilter] = useState<JournalFilter>("all");
  const [tagFilter, setTagFilter] = useState<string | null>(null);
  const [form, setForm] = useState({
    title: "",
    content: "",
    entry_type: "daily",
    tags: "",
  });

  const loadEntries = () => {
    if (!token) {
      setLoading(false);
      return;
    }
    apiFetch<JournalEntry[]>("/api/journal?limit=100", {}, token)
      .then(setEntries)
      .catch((e) => toast.error(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(loadEntries, [token]);

  const handleCreate = async () => {
    const trimmedContent = form.content.trim();
    const trimmedTitle = form.title.trim();
    if (!token || !trimmedContent) return;
    setCreating(true);
    try {
      await apiFetch(
        "/api/journal",
        {
          method: "POST",
          body: JSON.stringify({
            ...form,
            title: trimmedTitle,
            content: trimmedContent,
            tags: form.tags
              ? form.tags.split(",").map((t) => t.trim()).filter(Boolean)
              : undefined,
          }),
        },
        token
      );
      setForm({ title: "", content: "", entry_type: "daily", tags: "" });
      setSheetOpen(false);
      toast.success("Entry created");
      loadEntries();
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (path: string) => {
    if (!token) return;
    try {
      await apiFetch(`/api/journal/${encodeURIComponent(path)}`, { method: "DELETE" }, token);
      toast.success("Deleted");
      setSelected(null);
      setDeletingPath(null);
      loadEntries();
    } catch (e) {
      toast.error((e as Error).message);
    }
  };

  const viewEntry = async (path: string) => {
    if (!token) return;
    try {
      const entry = await apiFetch<JournalEntry>(
        `/api/journal/${encodeURIComponent(path)}`,
        {},
        token
      );
      setSelected(entry);
      logEngagement(token, "opened", "journal", path);
    } catch (e) {
      toast.error((e as Error).message);
    }
  };

  const typeColors: Record<string, { badge: string; border: string }> = {
    daily: { badge: "bg-info/15 text-info border-info/25", border: "border-l-info" },
    quick: { badge: "bg-info/15 text-info border-info/25", border: "border-l-info" },
    project: { badge: "bg-purple-500/15 text-purple-600 dark:text-purple-400 border-purple-500/25", border: "border-l-purple-500" },
    goal: { badge: "bg-success/15 text-success border-success/25", border: "border-l-success" },
    reflection: { badge: "bg-warning/15 text-warning border-warning/25", border: "border-l-warning" },
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return null;
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / 86400000);
    if (diffDays === 0) return "Today";
    if (diffDays === 1) return "Yesterday";
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  };

  const entryCounts = useMemo(
    () => ({
      all: entries.length,
      daily: entries.filter((entry) => entry.type === "daily").length,
      project: entries.filter((entry) => entry.type === "project").length,
      goal: entries.filter((entry) => entry.type === "goal").length,
      reflection: entries.filter((entry) => entry.type === "reflection").length,
    }),
    [entries]
  );

  const availableTags = useMemo(
    () => [...new Set(entries.flatMap((entry) => entry.tags))].sort((left, right) => left.localeCompare(right)),
    [entries]
  );

  const filteredEntries = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();

    return entries.filter((entry) => {
      if (typeFilter !== "all" && entry.type !== typeFilter) return false;
      if (tagFilter && !entry.tags.includes(tagFilter)) return false;
      if (!normalizedQuery) return true;

      return [entry.title, entry.preview, entry.content ?? "", entry.tags.join(" ")]
        .join(" ")
        .toLowerCase()
        .includes(normalizedQuery);
    });
  }, [entries, query, tagFilter, typeFilter]);

  const hasActiveFilters = Boolean(query.trim()) || typeFilter !== "all" || Boolean(tagFilter);

  const filteredEmptyState = (() => {
    if (query.trim()) {
      return {
        title: "No entries match that search",
        description: "Try a broader keyword or reset your filters to return to the full journal.",
      };
    }

    if (tagFilter) {
      return {
        title: `No entries tagged ${tagFilter}`,
        description: "Choose another tag or reset filters to browse everything you’ve captured.",
      };
    }

    if (typeFilter !== "all") {
      return {
        title: `No ${typeFilter} entries yet`,
        description: "Capture one in the composer or switch filters to browse other journal types.",
      };
    }

    return {
      title: "Nothing here yet",
      description: "Add a journal entry and I’ll start building a picture of what matters to you.",
    };
  })();

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-4 md:p-6">
      <WorkspacePageHeader
        eyebrow="Capture"
        title="Journal"
        description="Capture context, then narrow it fast with local search, type filters, and tag chips."
        badge={!loading && entries.length > 0 ? `${entries.length} ${entries.length === 1 ? "entry" : "entries"}` : undefined}
        actions={
          <Sheet open={sheetOpen} onOpenChange={setSheetOpen}>
            <SheetTrigger asChild>
              <Button>
                <Plus className="h-4 w-4" /> New Entry
              </Button>
            </SheetTrigger>
          <SheetContent className="w-full sm:max-w-lg md:max-w-xl overflow-y-auto">
            <SheetHeader>
              <SheetTitle>New entry</SheetTitle>
              <SheetDescription>What&apos;s on your mind? Capture thoughts, decisions, or progress.</SheetDescription>
            </SheetHeader>
            <div className="mt-6 space-y-4 px-6 pb-6">
              <div className="space-y-1.5">
                <Label>Title</Label>
                <Input
                  value={form.title}
                  onChange={(e) =>
                    setForm({ ...form, title: e.target.value })
                  }
                  placeholder="Optional title"
                />
                <p className="text-xs text-muted-foreground">
                  Leave this blank if you want StewardMe to generate a title for you.
                </p>
              </div>
              <div className="space-y-1.5">
                <Label>Type</Label>
                <Select
                  value={form.entry_type}
                  onValueChange={(v) => setForm({ ...form, entry_type: v })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="daily">Daily</SelectItem>
                    <SelectItem value="project">Project</SelectItem>
                    <SelectItem value="goal">Goal</SelectItem>
                    <SelectItem value="reflection">Reflection</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1.5">
                <Label>Tags (comma-separated)</Label>
                <Input
                  value={form.tags}
                  onChange={(e) =>
                    setForm({ ...form, tags: e.target.value })
                  }
                  placeholder="e.g. work, ideas"
                />
              </div>
              <div className="space-y-1.5">
                <Label>Content</Label>
                <Textarea
                  rows={12}
                  value={form.content}
                  onChange={(e) =>
                    setForm({ ...form, content: e.target.value })
                  }
                  placeholder="What happened, what you're thinking, or what you want to work through..."
                />
              </div>
              <Button onClick={handleCreate} disabled={creating || !form.content.trim()}>
                {creating ? "Saving..." : "Save Entry"}
              </Button>
            </div>
          </SheetContent>
        </Sheet>
        }
      />

      {!loading && entries.length > 0 && (
        <>
          <div className="grid gap-3 sm:grid-cols-4">
            <Card className="gap-3 py-4">
              <CardHeader className="px-4 pb-0">
                <CardDescription className="text-xs uppercase tracking-wide">All</CardDescription>
                <CardTitle className="text-2xl">{entryCounts.all}</CardTitle>
              </CardHeader>
              <CardContent className="px-4 text-xs text-muted-foreground">
                Everything currently loaded into the journal workspace.
              </CardContent>
            </Card>
            <Card className="gap-3 py-4">
              <CardHeader className="px-4 pb-0">
                <CardDescription className="text-xs uppercase tracking-wide">Daily</CardDescription>
                <CardTitle className="text-2xl">{entryCounts.daily}</CardTitle>
              </CardHeader>
              <CardContent className="px-4 text-xs text-muted-foreground">
                Ongoing reflections and day-to-day context.
              </CardContent>
            </Card>
            <Card className="gap-3 py-4">
              <CardHeader className="px-4 pb-0">
                <CardDescription className="text-xs uppercase tracking-wide">Project</CardDescription>
                <CardTitle className="text-2xl">{entryCounts.project}</CardTitle>
              </CardHeader>
              <CardContent className="px-4 text-xs text-muted-foreground">
                Delivery notes, project learnings, and progress logs.
              </CardContent>
            </Card>
            <Card className="gap-3 py-4">
              <CardHeader className="px-4 pb-0">
                <CardDescription className="text-xs uppercase tracking-wide">Reflection</CardDescription>
                <CardTitle className="text-2xl">{entryCounts.reflection}</CardTitle>
              </CardHeader>
              <CardContent className="px-4 text-xs text-muted-foreground">
                Higher-signal entries you may want to revisit later.
              </CardContent>
            </Card>
          </div>

          <Card className="gap-3 py-4">
            <CardContent className="flex flex-col gap-3 px-4">
              <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
                <div className="relative w-full lg:max-w-md">
                  <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    placeholder="Search titles, previews, and tags"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    className="pl-9 pr-9"
                  />
                  {query && (
                    <button
                      onClick={() => setQuery("")}
                      className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                    >
                      <X className="h-3.5 w-3.5" />
                    </button>
                  )}
                </div>

                <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
                  <Select value={typeFilter} onValueChange={(value) => setTypeFilter(value as JournalFilter)}>
                    <SelectTrigger className="w-full sm:w-44">
                      <SelectValue placeholder="Filter by type" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All types</SelectItem>
                      <SelectItem value="daily">Daily</SelectItem>
                      <SelectItem value="project">Project</SelectItem>
                      <SelectItem value="goal">Goal</SelectItem>
                      <SelectItem value="reflection">Reflection</SelectItem>
                    </SelectContent>
                  </Select>

                  {hasActiveFilters && (
                    <Button
                      variant="ghost"
                      onClick={() => {
                        setQuery("");
                        setTypeFilter("all");
                        setTagFilter(null);
                      }}
                    >
                      Reset filters
                    </Button>
                  )}
                </div>
              </div>

              {availableTags.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {availableTags.slice(0, 12).map((tag) => (
                    <Button
                      key={tag}
                      size="sm"
                      variant={tagFilter === tag ? "default" : "outline"}
                      onClick={() => setTagFilter((current) => current === tag ? null : tag)}
                    >
                      #{tag}
                    </Button>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          <p className="text-sm text-muted-foreground">
            {filteredEntries.length === entries.length
              ? `${entries.length} entries in view`
              : `Showing ${filteredEntries.length} of ${entries.length} entries`}
          </p>
        </>
      )}

      {/* Loading skeleton */}
      {loading && (
        <div className="grid gap-4 md:grid-cols-2">
          {Array.from({ length: 4 }).map((_, i) => (
            <EntrySkeleton key={i} />
          ))}
        </div>
      )}

      {/* Empty state */}
      {!loading && entries.length === 0 && (
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-muted">
            <BookOpen className="h-7 w-7 text-muted-foreground" />
          </div>
          <h3 className="text-lg font-medium">Nothing here yet</h3>
          <p className="mt-1 max-w-sm text-sm text-muted-foreground">
            I don&apos;t have enough context yet. Add a journal entry and I&apos;ll
            start building a picture of what matters to you.
          </p>
          <Button className="mt-4" variant="outline" onClick={() => setSheetOpen(true)}>
            <Plus className="h-4 w-4" /> Write your first entry
          </Button>
        </div>
      )}

      {/* Entry list */}
      {!loading && entries.length > 0 && filteredEntries.length === 0 && (
        <Card className="border-dashed py-10 text-center">
          <CardContent className="space-y-3 px-6">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-muted">
              <BookOpen className="h-5 w-5 text-muted-foreground" />
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
                    setQuery("");
                    setTypeFilter("all");
                    setTagFilter(null);
                  }}
                >
                  Reset filters
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {!loading && filteredEntries.length > 0 && (
        <div className="grid gap-4 md:grid-cols-2">
          {filteredEntries.map((e) => {
            const tc = typeColors[e.type] || typeColors.daily;
            return (
              <Card
                key={e.path}
                className={`cursor-pointer border-l-2 ${tc.border}`}
                onClick={() => viewEntry(e.path)}
              >
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-base">{e.title}</CardTitle>
                    <Badge variant="outline" className={tc.badge}>{e.type}</Badge>
                  </div>
                  {e.created && (
                    <CardDescription>
                      {formatDate(e.created)}
                    </CardDescription>
                  )}
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground line-clamp-3">
                    {stripMarkdown(e.preview)}
                  </p>
                  {e.tags.length > 0 && (
                    <div className="mt-2 flex gap-1">
                      {e.tags.map((t) => (
                        <Badge key={t} variant="secondary" className="text-xs">
                          {t}
                        </Badge>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {/* Selected entry detail */}
      {selected && (
        <Sheet open={!!selected} onOpenChange={() => { setSelected(null); setDeletingPath(null); }}>
          <SheetContent className="w-full sm:max-w-xl md:max-w-2xl overflow-y-auto">
            <SheetHeader>
              <div className="flex items-center gap-2">
                <Badge variant="outline" className={(typeColors[selected.type] || typeColors.daily).badge}>
                  {selected.type}
                </Badge>
                {selected.created && (
                  <span className="flex items-center gap-1 text-xs text-muted-foreground">
                    <Calendar className="h-3 w-3" />
                    {new Date(selected.created).toLocaleDateString("en-US", {
                      weekday: "short",
                      month: "short",
                      day: "numeric",
                      year: "numeric",
                    })}
                  </span>
                )}
              </div>
              <SheetTitle className="text-lg">{selected.title}</SheetTitle>
              {selected.tags?.length > 0 && (
                <div className="flex items-center gap-1.5 pt-1">
                  <Tag className="h-3 w-3 text-muted-foreground" />
                  {selected.tags.map((t) => (
                    <Badge key={t} variant="secondary" className="text-xs">
                      {t}
                    </Badge>
                  ))}
                </div>
              )}
            </SheetHeader>
            <div className="mt-6 space-y-6 px-6 pb-6">
              <div className="prose prose-sm max-w-none dark:prose-invert prose-p:leading-relaxed prose-headings:mt-4 prose-headings:mb-2">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {selected.content || ""}
                </ReactMarkdown>
              </div>
              <MindMapCard entry={selected} token={token} />
              <div className="border-t pt-4">
                {deletingPath === selected.path ? (
                  <div className="flex items-center gap-2 rounded-md border border-destructive/50 bg-destructive/5 p-3">
                    <p className="flex-1 text-sm">Delete this entry? This can&apos;t be undone.</p>
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={() => handleDelete(selected.path)}
                    >
                      Confirm
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setDeletingPath(null)}
                    >
                      Cancel
                    </Button>
                  </div>
                ) : (
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-destructive hover:text-destructive hover:bg-destructive/10"
                    onClick={() => setDeletingPath(selected.path)}
                  >
                    Delete entry
                  </Button>
                )}
              </div>
            </div>
          </SheetContent>
        </Sheet>
      )}
    </div>
  );
}
