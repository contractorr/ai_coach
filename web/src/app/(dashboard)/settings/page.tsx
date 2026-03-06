"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Pencil, Check, X, RefreshCw, Rss, Loader2, Trash2, Plus } from "lucide-react";
import { useToken } from "@/hooks/useToken";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { ApiKeyInput } from "@/components/ApiKeyInput";
import { DeleteAccountModal } from "@/components/DeleteAccountModal";
import { apiFetch } from "@/lib/api";

interface Settings {
  llm_provider: string | null;
  llm_model: string | null;
  llm_api_key_set: boolean;
  llm_api_key_hint: string | null;
  using_shared_key: boolean;
  has_own_key: boolean;
  tavily_api_key_set: boolean;
  tavily_api_key_hint: string | null;
  github_token_set: boolean;
  github_token_hint: string | null;
  eventbrite_token_set: boolean;
}

interface UserMe {
  name: string | null;
  email: string | null;
}

interface RSSFeed {
  id: number;
  url: string;
  name: string | null;
  added_by: string;
  created_at: string;
}

interface WatchlistItem {
  id: string;
  label: string;
  kind: string;
  why: string;
  priority: "high" | "medium" | "low";
  tags: string[];
  created_at: string;
  updated_at: string;
}

interface ProfileData {
  current_role: string;
  career_stage: string;
  skills: { name: string; proficiency: number }[];
  interests: string[];
  aspirations: string;
  location: string;
  languages_frameworks: string[];
  learning_style: string;
  weekly_hours_available: number;
  goals_short_term: string;
  goals_long_term: string;
  industries_watching: string[];
  technologies_watching: string[];
  constraints: Record<string, unknown>;
  fears_risks: string[];
  active_projects: string[];
  updated_at: string | null;
  summary: string;
  is_stale: boolean;
}

// Editable field config
type FieldType = "text" | "textarea" | "tags" | "skills";

interface FieldConfig {
  key: keyof ProfileData;
  label: string;
  type: FieldType;
}

const PROFILE_FIELDS: FieldConfig[] = [
  { key: "current_role", label: "Role", type: "text" },
  { key: "career_stage", label: "Career Stage", type: "text" },
  { key: "skills", label: "Skills", type: "skills" },
  { key: "interests", label: "Interests", type: "tags" },
  { key: "languages_frameworks", label: "Languages & Frameworks", type: "tags" },
  { key: "goals_short_term", label: "6-Month Goals", type: "textarea" },
  { key: "goals_long_term", label: "3-Year Vision", type: "textarea" },
  { key: "aspirations", label: "Aspirations", type: "textarea" },
  { key: "industries_watching", label: "Industries Watching", type: "tags" },
  { key: "technologies_watching", label: "Technologies Watching", type: "tags" },
  { key: "active_projects", label: "Active Projects", type: "tags" },
  { key: "fears_risks", label: "Risks & Concerns", type: "tags" },
  { key: "location", label: "Location", type: "text" },
  { key: "learning_style", label: "Learning Style", type: "text" },
];

function TagsEditor({
  value,
  onChange,
}: {
  value: string[];
  onChange: (v: string[]) => void;
}) {
  const [input, setInput] = useState("");
  const add = () => {
    const tag = input.trim();
    if (tag && !value.includes(tag)) {
      onChange([...value, tag]);
    }
    setInput("");
  };
  return (
    <div className="space-y-2">
      <div className="flex flex-wrap gap-1">
        {value.map((t) => (
          <Badge key={t} variant="secondary" className="gap-1">
            {t}
            <button
              onClick={() => onChange(value.filter((v) => v !== t))}
              className="ml-0.5 hover:text-destructive"
            >
              <X className="h-3 w-3" />
            </button>
          </Badge>
        ))}
      </div>
      <div className="flex gap-2">
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), add())}
          placeholder="Add item..."
          className="h-8 text-sm"
        />
        <Button size="sm" variant="outline" onClick={add} className="h-8">
          Add
        </Button>
      </div>
    </div>
  );
}

function SkillsEditor({
  value,
  onChange,
}: {
  value: { name: string; proficiency: number }[];
  onChange: (v: { name: string; proficiency: number }[]) => void;
}) {
  const [input, setInput] = useState("");
  const add = () => {
    const name = input.trim();
    if (name && !value.find((s) => s.name === name)) {
      onChange([...value, { name, proficiency: 3 }]);
    }
    setInput("");
  };
  return (
    <div className="space-y-2">
      <div className="flex flex-wrap gap-1">
        {value.map((s) => (
          <Badge key={s.name} variant="secondary" className="gap-1">
            {s.name} ({s.proficiency})
            <button
              onClick={() => onChange(value.filter((v) => v.name !== s.name))}
              className="ml-0.5 hover:text-destructive"
            >
              <X className="h-3 w-3" />
            </button>
          </Badge>
        ))}
      </div>
      <div className="flex gap-2">
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), add())}
          placeholder="Add skill..."
          className="h-8 text-sm"
        />
        <Button size="sm" variant="outline" onClick={add} className="h-8">
          Add
        </Button>
      </div>
    </div>
  );
}

function ProfileField({
  config,
  profile,
  token,
  onUpdated,
}: {
  config: FieldConfig;
  profile: ProfileData;
  token: string;
  onUpdated: (p: ProfileData) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState<unknown>(null);
  const [saving, setSaving] = useState(false);

  const rawValue = profile[config.key];

  const startEdit = () => {
    setDraft(
      config.type === "tags" || config.type === "skills"
        ? JSON.parse(JSON.stringify(rawValue))
        : rawValue
    );
    setEditing(true);
  };

  const cancel = () => {
    setEditing(false);
    setDraft(null);
  };

  const save = async () => {
    setSaving(true);
    try {
      await apiFetch(
        "/api/profile",
        { method: "PATCH", body: JSON.stringify({ [config.key]: draft }) },
        token
      );
      const updated = await apiFetch<ProfileData>("/api/profile", {}, token);
      onUpdated(updated);
      setEditing(false);
      toast.success(`${config.label} updated`);
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setSaving(false);
    }
  };

  // Display value
  const displayValue = () => {
    if (config.type === "skills") {
      const skills = rawValue as { name: string; proficiency: number }[];
      if (!skills.length) return <span className="text-muted-foreground text-sm">Not set</span>;
      return (
        <div className="flex flex-wrap gap-1">
          {skills.map((s) => (
            <Badge key={s.name} variant="outline" className="text-xs">
              {s.name} ({s.proficiency})
            </Badge>
          ))}
        </div>
      );
    }
    if (config.type === "tags") {
      const tags = rawValue as string[];
      if (!tags.length) return <span className="text-muted-foreground text-sm">Not set</span>;
      return (
        <div className="flex flex-wrap gap-1">
          {tags.map((t) => (
            <Badge key={t} variant="outline" className="text-xs">
              {t}
            </Badge>
          ))}
        </div>
      );
    }
    const str = String(rawValue || "");
    if (!str) return <span className="text-muted-foreground text-sm">Not set</span>;
    return <span className="text-sm">{str}</span>;
  };

  return (
    <div className="flex items-start gap-2 py-2">
      <div className="flex-1 min-w-0">
        <Label className="text-xs text-muted-foreground">{config.label}</Label>
        {editing ? (
          <div className="mt-1 space-y-2">
            {config.type === "text" && (
              <Input
                value={draft as string}
                onChange={(e) => setDraft(e.target.value)}
                className="h-8 text-sm"
              />
            )}
            {config.type === "textarea" && (
              <Textarea
                value={draft as string}
                onChange={(e) => setDraft(e.target.value)}
                rows={3}
                className="text-sm"
              />
            )}
            {config.type === "tags" && (
              <TagsEditor
                value={draft as string[]}
                onChange={(v) => setDraft(v)}
              />
            )}
            {config.type === "skills" && (
              <SkillsEditor
                value={draft as { name: string; proficiency: number }[]}
                onChange={(v) => setDraft(v)}
              />
            )}
            <div className="flex gap-1">
              <Button size="sm" variant="outline" onClick={save} disabled={saving} className="h-7 text-xs">
                <Check className="mr-1 h-3 w-3" />
                Save
              </Button>
              <Button size="sm" variant="ghost" onClick={cancel} className="h-7 text-xs">
                Cancel
              </Button>
            </div>
          </div>
        ) : (
          <div className="mt-0.5">{displayValue()}</div>
        )}
      </div>
      {!editing && (
        <Button size="icon" variant="ghost" onClick={startEdit} className="h-7 w-7 shrink-0 mt-3">
          <Pencil className="h-3 w-3" />
        </Button>
      )}
    </div>
  );
}

function SettingsSkeleton() {
  return (
    <div className="mx-auto max-w-2xl space-y-6 p-4 md:p-6">
      <div className="h-7 w-24 animate-pulse rounded bg-muted" />
      {Array.from({ length: 3 }).map((_, i) => (
        <Card key={i}>
          <CardHeader>
            <div className="h-5 w-32 animate-pulse rounded bg-muted" />
            <div className="h-3 w-48 animate-pulse rounded bg-muted" />
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="h-9 w-full animate-pulse rounded bg-muted" />
            <div className="h-9 w-full animate-pulse rounded bg-muted" />
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

export default function SettingsPage() {
  const token = useToken();
  const router = useRouter();
  const [settings, setSettings] = useState<Settings | null>(null);
  const [profile, setProfile] = useState<ProfileData | null>(null);
  const [userMe, setUserMe] = useState<UserMe | null>(null);
  const [form, setForm] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  const [nameDraft, setNameDraft] = useState("");
  const [editingName, setEditingName] = useState(false);
  const [savingName, setSavingName] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [rssFeeds, setRssFeeds] = useState<RSSFeed[]>([]);
  const [rssUrl, setRssUrl] = useState("");
  const [rssAdding, setRssAdding] = useState(false);
  const [rssRemoving, setRssRemoving] = useState<string | null>(null);
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([]);
  const [watchLabel, setWatchLabel] = useState("");
  const [watchWhy, setWatchWhy] = useState("");
  const [watchTags, setWatchTags] = useState("");
  const [watchPriority, setWatchPriority] = useState<"high" | "medium" | "low">("medium");
  const [watchSaving, setWatchSaving] = useState(false);
  const [watchRemoving, setWatchRemoving] = useState<string | null>(null);
  const [editingWatchId, setEditingWatchId] = useState<string | null>(null);

  const isDirty = Object.keys(form).length > 0;

  useEffect(() => {
    if (!token) return;
    apiFetch<Settings>("/api/settings", {}, token)
      .then(setSettings)
      .catch((e) => toast.error(e.message));
    apiFetch<ProfileData>("/api/profile", {}, token)
      .then(setProfile)
      .catch(() => {}); // profile may not exist yet
    apiFetch<UserMe>("/api/user/me", {}, token)
      .then((u) => { setUserMe(u); setNameDraft(u.name || ""); })
      .catch(() => {});
    apiFetch<RSSFeed[]>("/api/intel/rss-feeds", {}, token)
      .then(setRssFeeds)
      .catch(() => {});
    apiFetch<WatchlistItem[]>("/api/intel/watchlist", {}, token)
      .then(setWatchlist)
      .catch(() => {});
  }, [token]);

  const resetWatchForm = () => {
    setWatchLabel("");
    setWatchWhy("");
    setWatchTags("");
    setWatchPriority("medium");
    setEditingWatchId(null);
  };

  const handleSaveName = async () => {
    if (!token) return;
    setSavingName(true);
    try {
      const updated = await apiFetch<UserMe>(
        "/api/user/me",
        { method: "PATCH", body: JSON.stringify({ name: nameDraft.trim() }) },
        token
      );
      setUserMe(updated);
      setEditingName(false);
      toast.success("Name updated");
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setSavingName(false);
    }
  };

  const handleSave = async () => {
    if (!token) return;
    setSaving(true);
    try {
      const payload: Record<string, string | number> = {};
      for (const [key, val] of Object.entries(form)) {
        if (val) payload[key] = val;
      }
      const updated = await apiFetch<Settings>(
        "/api/settings",
        { method: "PUT", body: JSON.stringify(payload) },
        token
      );
      setSettings(updated);
      setForm({});
      toast.success("Settings saved");
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setSaving(false);
    }
  };

  const handleAddFeed = async () => {
    if (!token || !rssUrl.trim()) return;
    setRssAdding(true);
    try {
      const feed = await apiFetch<RSSFeed>(
        "/api/intel/rss-feeds",
        { method: "POST", body: JSON.stringify({ url: rssUrl.trim() }) },
        token
      );
      setRssFeeds((prev) => [feed, ...prev]);
      setRssUrl("");
      toast.success("Feed added");
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setRssAdding(false);
    }
  };

  const handleRemoveFeed = async (url: string) => {
    if (!token) return;
    setRssRemoving(url);
    try {
      await apiFetch(
        "/api/intel/rss-feeds",
        { method: "DELETE", body: JSON.stringify({ url }) },
        token
      );
      setRssFeeds((prev) => prev.filter((f) => f.url !== url));
      toast.success("Feed removed");
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setRssRemoving(null);
    }
  };

  const handleSaveWatch = async () => {
    if (!token || !watchLabel.trim()) return;
    setWatchSaving(true);
    try {
      const payload = {
        label: watchLabel.trim(),
        why: watchWhy.trim(),
        priority: watchPriority,
        tags: watchTags.split(",").map((part) => part.trim()).filter(Boolean),
      };
      const endpoint = editingWatchId
        ? `/api/intel/watchlist/${editingWatchId}`
        : "/api/intel/watchlist";
      const method = editingWatchId ? "PATCH" : "POST";
      const saved = await apiFetch<WatchlistItem>(
        endpoint,
        { method, body: JSON.stringify(payload) },
        token
      );
      setWatchlist((prev) => {
        const others = prev.filter((item) => item.id !== saved.id);
        return [saved, ...others].sort((a, b) => a.label.localeCompare(b.label));
      });
      resetWatchForm();
      toast.success(editingWatchId ? "Watchlist item updated" : "Watchlist item added");
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setWatchSaving(false);
    }
  };

  const handleEditWatch = (item: WatchlistItem) => {
    setEditingWatchId(item.id);
    setWatchLabel(item.label);
    setWatchWhy(item.why || "");
    setWatchPriority(item.priority || "medium");
    setWatchTags((item.tags || []).join(", "));
  };

  const handleRemoveWatch = async (itemId: string) => {
    if (!token) return;
    setWatchRemoving(itemId);
    try {
      await apiFetch(`/api/intel/watchlist/${itemId}`, { method: "DELETE" }, token);
      setWatchlist((prev) => prev.filter((item) => item.id !== itemId));
      if (editingWatchId === itemId) resetWatchForm();
      toast.success("Watchlist item removed");
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setWatchRemoving(null);
    }
  };

  if (!settings) return <SettingsSkeleton />;

  return (
    <div className="mx-auto max-w-2xl space-y-6 p-4 md:p-6">
      <h1 className="text-2xl font-semibold">Settings</h1>

      <Card>
        <CardHeader>
          <CardTitle>Account</CardTitle>
          <CardDescription>Your display name</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-start gap-2">
            <div className="flex-1 min-w-0">
              <Label className="text-xs text-muted-foreground">Name</Label>
              {editingName ? (
                <div className="mt-1 space-y-2">
                  <Input
                    value={nameDraft}
                    onChange={(e) => setNameDraft(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleSaveName()}
                    className="h-8 text-sm"
                    autoFocus
                  />
                  <div className="flex gap-1">
                    <Button size="sm" variant="outline" onClick={handleSaveName} disabled={savingName} className="h-7 text-xs">
                      <Check className="mr-1 h-3 w-3" />
                      Save
                    </Button>
                    <Button size="sm" variant="ghost" onClick={() => { setEditingName(false); setNameDraft(userMe?.name || ""); }} className="h-7 text-xs">
                      Cancel
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="mt-0.5">
                  {userMe?.name
                    ? <span className="text-sm">{userMe.name}</span>
                    : <span className="text-sm text-muted-foreground">Not set</span>
                  }
                </div>
              )}
            </div>
            {!editingName && (
              <Button size="icon" variant="ghost" onClick={() => setEditingName(true)} className="h-7 w-7 shrink-0 mt-3">
                <Pencil className="h-3 w-3" />
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>LLM Provider</CardTitle>
          <CardDescription>Configure your AI model provider</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-1.5">
            <Label>Provider</Label>
            <p className="text-xs text-muted-foreground">Auto-detect picks provider based on your API key.</p>
            <Select
              value={form.llm_provider || settings.llm_provider || "auto"}
              onValueChange={(v) => setForm({ ...form, llm_provider: v })}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="auto">Auto-detect</SelectItem>
                <SelectItem value="claude">Claude</SelectItem>
                <SelectItem value="openai">OpenAI</SelectItem>
                <SelectItem value="gemini">Gemini</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label>Model (optional)</Label>
            <p className="text-xs text-muted-foreground">Leave blank for the provider&apos;s default model.</p>
            <Input
              placeholder="e.g. claude-sonnet-4-20250514"
              value={form.llm_model || ""}
              onChange={(e) => setForm({ ...form, llm_model: e.target.value })}
            />
          </div>
          {settings.using_shared_key && (
            <div className="rounded-lg border border-amber-200 bg-amber-50 dark:border-amber-900 dark:bg-amber-950/30 p-3 text-xs text-amber-800 dark:text-amber-200">
              You&apos;re using lite mode (Haiku, 30 queries/day). Add your own key below for full-quality responses, deep research, and unlimited usage.
            </div>
          )}
          <ApiKeyInput
            label="LLM API Key"
            name="llm_api_key"
            value={form.llm_api_key || ""}
            onChange={(v) => setForm({ ...form, llm_api_key: v })}
            isSet={settings.llm_api_key_set}
            hint={settings.llm_api_key_hint}
            description="Optional. Your key is encrypted and stored per-user. Without it, lite mode (Haiku, 30 queries/day) is used."
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>API Keys</CardTitle>
          <CardDescription>Keys for intelligence and research</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <ApiKeyInput
            label="Tavily API Key"
            name="tavily_api_key"
            value={form.tavily_api_key || ""}
            onChange={(v) => setForm({ ...form, tavily_api_key: v })}
            isSet={settings.tavily_api_key_set}
            hint={settings.tavily_api_key_hint}
            description="Optional. Enables web search for deep research. Falls back to DuckDuckGo if not set."
          />
          <ApiKeyInput
            label="GitHub Token"
            name="github_token"
            value={form.github_token || ""}
            onChange={(v) => setForm({ ...form, github_token: v })}
            isSet={settings.github_token_set}
            hint={settings.github_token_hint}
            description="Optional. Raises GitHub scraper rate limit from 60 to 5,000 req/hr. Needs only public_repo scope."
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Rss className="h-4 w-4" />
            RSS Feeds
          </CardTitle>
          <CardDescription>Custom feeds added to your intel radar</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {rssFeeds.length === 0 && (
            <p className="text-sm text-muted-foreground">No custom feeds yet.</p>
          )}
          {rssFeeds.map((feed) => (
            <div key={feed.id} className="flex items-center justify-between gap-2 rounded-md border p-2">
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium">
                  {feed.name || new URL(feed.url).hostname}
                </p>
                <p className="truncate text-xs text-muted-foreground">{feed.url}</p>
              </div>
              <div className="flex items-center gap-1.5 shrink-0">
                {feed.added_by === "advisor" && (
                  <Badge variant="outline" className="text-[10px]">advisor</Badge>
                )}
                <Button
                  size="icon"
                  variant="ghost"
                  className="h-7 w-7"
                  disabled={rssRemoving === feed.url}
                  onClick={() => handleRemoveFeed(feed.url)}
                >
                  {rssRemoving === feed.url
                    ? <Loader2 className="h-3 w-3 animate-spin" />
                    : <Trash2 className="h-3 w-3" />
                  }
                </Button>
              </div>
            </div>
          ))}
          <div className="flex gap-2">
            <Input
              value={rssUrl}
              onChange={(e) => setRssUrl(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleAddFeed()}
              placeholder="https://example.com/feed.xml"
              className="h-8 text-sm"
            />
            <Button
              size="sm"
              variant="outline"
              onClick={handleAddFeed}
              disabled={rssAdding || !rssUrl.trim()}
              className="h-8 shrink-0"
            >
              {rssAdding ? <Loader2 className="mr-1 h-3 w-3 animate-spin" /> : <Plus className="mr-1 h-3 w-3" />}
              Add
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Watchlist</CardTitle>
          <CardDescription>
            Track specific companies, technologies, roles, or themes so Radar can rank bespoke matches first.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            {watchlist.length === 0 && (
              <p className="text-sm text-muted-foreground">
                No watchlist items yet. Add a few themes you want me to track closely.
              </p>
            )}
            {watchlist.map((item) => (
              <div key={item.id} className="flex items-start justify-between gap-3 rounded-xl border p-3">
                <div className="min-w-0 flex-1 space-y-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="font-medium">{item.label}</p>
                    <Badge variant="outline" className="text-[10px]">{item.priority}</Badge>
                  </div>
                  {item.why && <p className="text-sm text-muted-foreground">{item.why}</p>}
                  {item.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1 pt-1">
                      {item.tags.map((tag) => (
                        <Badge key={tag} variant="secondary" className="text-[10px]">{tag}</Badge>
                      ))}
                    </div>
                  )}
                </div>
                <div className="flex items-center gap-1 shrink-0">
                  <Button size="icon" variant="ghost" className="h-7 w-7" onClick={() => handleEditWatch(item)}>
                    <Pencil className="h-3 w-3" />
                  </Button>
                  <Button
                    size="icon"
                    variant="ghost"
                    className="h-7 w-7"
                    disabled={watchRemoving === item.id}
                    onClick={() => handleRemoveWatch(item.id)}
                  >
                    {watchRemoving === item.id
                      ? <Loader2 className="h-3 w-3 animate-spin" />
                      : <Trash2 className="h-3 w-3" />}
                  </Button>
                </div>
              </div>
            ))}
          </div>

          <Separator />

          <div className="space-y-3">
            <div>
              <Label className="text-xs text-muted-foreground">What should I watch?</Label>
              <Input
                value={watchLabel}
                onChange={(e) => setWatchLabel(e.target.value)}
                placeholder="e.g. OpenAI, AI agents, staff+ roles"
                className="mt-1 h-8 text-sm"
              />
            </div>
            <div>
              <Label className="text-xs text-muted-foreground">Why it matters</Label>
              <Textarea
                value={watchWhy}
                onChange={(e) => setWatchWhy(e.target.value)}
                placeholder="e.g. relevant to my next role and current product bets"
                className="mt-1 min-h-[70px] text-sm"
              />
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              <div>
                <Label className="text-xs text-muted-foreground">Priority</Label>
                <Select value={watchPriority} onValueChange={(value) => setWatchPriority(value as "high" | "medium" | "low") }>
                  <SelectTrigger className="mt-1 h-8 text-sm">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="high">High</SelectItem>
                    <SelectItem value="medium">Medium</SelectItem>
                    <SelectItem value="low">Low</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label className="text-xs text-muted-foreground">Tags</Label>
                <Input
                  value={watchTags}
                  onChange={(e) => setWatchTags(e.target.value)}
                  placeholder="career, startup, infrastructure"
                  className="mt-1 h-8 text-sm"
                />
              </div>
            </div>
            <div className="flex gap-2">
              <Button onClick={handleSaveWatch} disabled={watchSaving || !watchLabel.trim()}>
                {watchSaving ? "Saving..." : editingWatchId ? "Update Watch" : "Add Watch"}
              </Button>
              {editingWatchId && (
                <Button variant="ghost" onClick={resetWatchForm}>
                  Cancel
                </Button>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Profile</CardTitle>
              <CardDescription>
                Your profile context — used to personalise advice and recommendations
              </CardDescription>
            </div>
            {profile?.is_stale && (
              <Badge variant="secondary" className="text-xs">Needs update</Badge>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {profile && token ? (
            <div className="divide-y">
              {PROFILE_FIELDS.map((f) => (
                <ProfileField
                  key={f.key}
                  config={f}
                  profile={profile}
                  token={token}
                  onUpdated={setProfile}
                />
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">
              I don&apos;t have a profile for you yet. Run onboarding to get me up to speed.
            </p>
          )}
          <Separator className="my-4" />
          <Button variant="outline" onClick={() => router.push("/onboarding")}>
            <RefreshCw className="mr-2 h-4 w-4" />
            Restart Onboarding
          </Button>
        </CardContent>
      </Card>

      <Separator />
      <div className="flex items-center gap-3">
        <Button onClick={handleSave} disabled={saving || !isDirty}>
          {saving ? "Saving..." : isDirty ? "Save Changes" : "No Changes"}
        </Button>
        {isDirty && (
          <span className="text-xs text-muted-foreground">
            {Object.keys(form).length} unsaved {Object.keys(form).length === 1 ? "change" : "changes"}
          </span>
        )}
      </div>

      <Card className="border-destructive/50 bg-destructive/5">
        <CardHeader>
          <CardTitle className="text-destructive">Danger Zone</CardTitle>
          <CardDescription>Irreversible actions</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium">Delete account</p>
              <p className="text-xs text-muted-foreground">Permanently delete your account and all data</p>
            </div>
            <Button variant="destructive" onClick={() => setDeleteOpen(true)}>
              Delete account
            </Button>
          </div>
        </CardContent>
      </Card>
      <DeleteAccountModal open={deleteOpen} onOpenChange={setDeleteOpen} />
    </div>
  );
}
