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
import { Switch } from "@/components/ui/switch";
import { ApiKeyInput } from "@/components/ApiKeyInput";
import { DeleteAccountModal } from "@/components/DeleteAccountModal";
import { WorkspacePageHeader } from "@/components/WorkspacePageHeader";
import { apiFetch } from "@/lib/api";

interface LLMProviderKeyStatus {
  provider: string;
  configured: boolean;
  hint: string | null;
  council_eligible: boolean;
}

interface CustomProvider {
  id: string;
  display_name: string;
  base_url: string;
  model: string;
}

interface Settings {
  llm_provider: string | null;
  llm_model: string | null;
  llm_council_enabled: boolean;
  llm_council_ready: boolean;
  llm_provider_keys: LLMProviderKeyStatus[];
  llm_custom_providers: CustomProvider[];
  llm_api_key_set: boolean;
  llm_api_key_hint: string | null;
  using_shared_key: boolean;
  has_own_key: boolean;
  tavily_api_key_set: boolean;
  tavily_api_key_hint: string | null;
  github_token_set: boolean;
  github_token_hint: string | null;
  eventbrite_token_set: boolean;
  feature_extended_thinking: boolean;
  feature_memory_enabled: boolean;
  feature_threads_enabled: boolean;
  feature_recommendations_enabled: boolean;
  feature_research_enabled: boolean;
  feature_entity_extraction_enabled: boolean;
  feature_trending_radar_enabled: boolean;
  feature_heartbeat_enabled: boolean;
  feature_company_movement_enabled: boolean;
  feature_hiring_signals_enabled: boolean;
  feature_regulatory_signals_enabled: boolean;
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
  aliases: string[];
  why: string;
  priority: "high" | "medium" | "low";
  tags: string[];
  goal: string;
  time_horizon: string;
  source_preferences: string[];
  domain: string;
  github_org: string;
  ticker: string;
  topics: string[];
  geographies: string[];
  linked_dossier_ids: string[];
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

interface UsageModelStats {
  model: string;
  input_tokens: number;
  output_tokens: number;
  query_count: number;
  estimated_cost_usd: number;
}

interface UsageStats {
  days: number;
  total_queries: number;
  total_estimated_cost_usd: number;
  by_model: UsageModelStats[];
}

interface MemoryFact {
  id: string;
  text: string;
  category: string;
  source_type: string;
  source_id: string;
  confidence: number;
  created_at: string;
  updated_at: string;
}

interface MemoryStats {
  total_active: number;
  total_superseded: number;
  by_category: Record<string, number>;
}

// Editable field config
type FieldType = "text" | "textarea" | "tags" | "skills";

interface FieldConfig {
  key: keyof ProfileData;
  label: string;
  type: FieldType;
}

const WATCH_KINDS = [
  { value: "theme", label: "Theme" },
  { value: "company", label: "Company" },
  { value: "sector", label: "Sector" },
  { value: "regulation", label: "Regulation" },
];

function splitCommaValues(value: string): string[] {
  return value.split(",").map((part) => part.trim()).filter(Boolean);
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
              type="button"
              aria-label={`Remove ${t}`}
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
              type="button"
              aria-label={`Remove ${s.name}`}
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
        "/api/v1/profile",
        { method: "PATCH", body: JSON.stringify({ [config.key]: draft }) },
        token
      );
      const updated = await apiFetch<ProfileData>("/api/v1/profile", {}, token);
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
        <Button size="icon" variant="ghost" onClick={startEdit} className="h-7 w-7 shrink-0 mt-3" aria-label={`Edit ${config.label}`}>
          <Pencil className="h-3 w-3" />
        </Button>
      )}
    </div>
  );
}

function SettingsSkeleton() {
  return (
    <div className="mx-auto max-w-7xl space-y-6 p-4 md:p-6">
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
  const [usageStats, setUsageStats] = useState<UsageStats | null>(null);
  const [memoryFacts, setMemoryFacts] = useState<MemoryFact[]>([]);
  const [memoryStats, setMemoryStats] = useState<MemoryStats | null>(null);
  const [deletingFactId, setDeletingFactId] = useState<string | null>(null);
  const [watchLabel, setWatchLabel] = useState("");
  const [watchKind, setWatchKind] = useState("theme");
  const [watchWhy, setWatchWhy] = useState("");
  const [watchAliases, setWatchAliases] = useState("");
  const [watchTags, setWatchTags] = useState("");
  const [watchPriority, setWatchPriority] = useState<"high" | "medium" | "low">("medium");
  const [watchGoal, setWatchGoal] = useState("");
  const [watchSourcePreferences, setWatchSourcePreferences] = useState("");
  const [watchDomain, setWatchDomain] = useState("");
  const [watchGithubOrg, setWatchGithubOrg] = useState("");
  const [watchTicker, setWatchTicker] = useState("");
  const [watchTopics, setWatchTopics] = useState("");
  const [watchGeographies, setWatchGeographies] = useState("");
  const [watchSaving, setWatchSaving] = useState(false);
  const [watchRemoving, setWatchRemoving] = useState<string | null>(null);
  const [editingWatchId, setEditingWatchId] = useState<string | null>(null);
  const [testingProvider, setTestingProvider] = useState<string | null>(null);
  const [customProviderDisplayName, setCustomProviderDisplayName] = useState("");
  const [customProviderBaseUrl, setCustomProviderBaseUrl] = useState("");
  const [customProviderApiKey, setCustomProviderApiKey] = useState("");
  const [customProviderModel, setCustomProviderModel] = useState("");
  const [editingCustomProviderId, setEditingCustomProviderId] = useState<string | null>(null);
  const [customProviderSaving, setCustomProviderSaving] = useState(false);
  const [testingCustomProviderId, setTestingCustomProviderId] = useState<string | null>(null);

  const sectionLinks = [
    { id: "account", label: "Account" },
    { id: "ai-settings", label: "AI" },
    { id: "usage", label: "Usage" },
    { id: "api-keys", label: "Keys" },
    { id: "features", label: "Features" },
    { id: "rss-feeds", label: "RSS" },
    { id: "watchlist", label: "Watchlist" },
    { id: "profile", label: "Profile" },
    { id: "memory", label: "Memory" },
    { id: "danger-zone", label: "Danger" },
  ];

  const isDirty = Object.keys(form).length > 0;

  useEffect(() => {
    if (!token) return;
    apiFetch<Settings>("/api/v1/settings", {}, token)
      .then(setSettings)
      .catch((e) => toast.error(e.message));
    apiFetch<ProfileData>("/api/v1/profile", {}, token)
      .then(setProfile)
      .catch(() => {}); // profile may not exist yet
    apiFetch<UserMe>("/api/v1/user/me", {}, token)
      .then((u) => { setUserMe(u); setNameDraft(u.name || ""); })
      .catch(() => {});
    apiFetch<RSSFeed[]>("/api/v1/intel/rss-feeds", {}, token)
      .then(setRssFeeds)
      .catch(() => {});
    apiFetch<WatchlistItem[]>("/api/v1/intel/watchlist", {}, token)
      .then(setWatchlist)
      .catch(() => {});
    apiFetch<UsageStats>("/api/v1/settings/usage", {}, token)
      .then(setUsageStats)
      .catch(() => {});
    apiFetch<MemoryFact[]>("/api/v1/memory/facts?limit=50", {}, token)
      .then(setMemoryFacts)
      .catch(() => {});
    apiFetch<MemoryStats>("/api/v1/memory/stats", {}, token)
      .then(setMemoryStats)
      .catch(() => {});
  }, [token]);

  const resetWatchForm = () => {
    setWatchLabel("");
    setWatchKind("theme");
    setWatchWhy("");
    setWatchAliases("");
    setWatchTags("");
    setWatchPriority("medium");
    setWatchGoal("");
    setWatchSourcePreferences("");
    setWatchDomain("");
    setWatchGithubOrg("");
    setWatchTicker("");
    setWatchTopics("");
    setWatchGeographies("");
    setEditingWatchId(null);
  };

  const handleSaveName = async () => {
    if (!token) return;
    setSavingName(true);
    try {
      const updated = await apiFetch<UserMe>(
        "/api/v1/user/me",
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
        "/api/v1/settings",
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

  const providerStatus = (provider: string) =>
    settings?.llm_provider_keys.find((item) => item.provider === provider);

  const handleRemoveProviderKey = async (provider: string) => {
    if (!token) return;
    setTestingProvider(provider);
    try {
      const updated = await apiFetch<Settings>(
        "/api/v1/settings",
        { method: "PUT", body: JSON.stringify({ llm_remove_providers: [provider] }) },
        token
      );
      setSettings(updated);
      setForm((prev) => {
        const next = { ...prev };
        delete next[`llm_api_key_${provider}`];
        return next;
      });
      toast.success(`${provider} key removed`);
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setTestingProvider(null);
    }
  };

  const handleTestProvider = async (provider: string) => {
    if (!token) return;
    setTestingProvider(provider);
    try {
      const result = await apiFetch<{ ok: boolean; provider: string }>(
        `/api/v1/settings/test-llm?provider=${encodeURIComponent(provider)}`,
        { method: "POST" },
        token
      );
      toast.success(`${result.provider.charAt(0).toUpperCase() + result.provider.slice(1)} connection successful!`);
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setTestingProvider(null);
    }
  };

  const handleDeleteFact = async (factId: string) => {
    if (!token) return;
    setDeletingFactId(factId);
    try {
      await apiFetch(`/api/v1/memory/facts/${encodeURIComponent(factId)}`, { method: "DELETE" }, token);
      setMemoryFacts((prev) => prev.filter((fact) => fact.id !== factId));
      setMemoryStats((prev) => {
        if (!prev) return prev;
        const removed = memoryFacts.find((fact) => fact.id === factId);
        const nextByCategory = { ...prev.by_category };
        if (removed?.category && nextByCategory[removed.category]) {
          nextByCategory[removed.category] = Math.max(0, nextByCategory[removed.category] - 1);
        }
        return {
          ...prev,
          total_active: Math.max(0, prev.total_active - 1),
          by_category: nextByCategory,
        };
      });
      toast.success("Memory fact deleted");
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setDeletingFactId(null);
    }
  };

  const handleAddFeed = async () => {
    if (!token || !rssUrl.trim()) return;
    setRssAdding(true);
    try {
      const feed = await apiFetch<RSSFeed>(
        "/api/v1/intel/rss-feeds",
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
        "/api/v1/intel/rss-feeds",
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
        kind: watchKind,
        aliases: splitCommaValues(watchAliases),
        why: watchWhy.trim(),
        priority: watchPriority,
        tags: splitCommaValues(watchTags),
        goal: watchGoal.trim(),
        source_preferences: splitCommaValues(watchSourcePreferences),
        domain: watchDomain.trim(),
        github_org: watchGithubOrg.trim(),
        ticker: watchTicker.trim().toUpperCase(),
        topics: splitCommaValues(watchTopics),
        geographies: splitCommaValues(watchGeographies),
      };
      const endpoint = editingWatchId
        ? `/api/v1/intel/watchlist/${editingWatchId}`
        : "/api/v1/intel/watchlist";
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
    setWatchKind(item.kind || "theme");
    setWatchWhy(item.why || "");
    setWatchAliases((item.aliases || []).join(", "));
    setWatchPriority(item.priority || "medium");
    setWatchTags((item.tags || []).join(", "));
    setWatchGoal(item.goal || "");
    setWatchSourcePreferences((item.source_preferences || []).join(", "));
    setWatchDomain(item.domain || "");
    setWatchGithubOrg(item.github_org || "");
    setWatchTicker(item.ticker || "");
    setWatchTopics((item.topics || []).join(", "));
    setWatchGeographies((item.geographies || []).join(", "));
  };

  const handleRemoveWatch = async (itemId: string) => {
    if (!token) return;
    setWatchRemoving(itemId);
    try {
      await apiFetch(`/api/v1/intel/watchlist/${itemId}`, { method: "DELETE" }, token);
      setWatchlist((prev) => prev.filter((item) => item.id !== itemId));
      if (editingWatchId === itemId) resetWatchForm();
      toast.success("Watchlist item removed");
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setWatchRemoving(null);
    }
  };

  const resetCustomProviderForm = () => {
    setCustomProviderDisplayName("");
    setCustomProviderBaseUrl("");
    setCustomProviderApiKey("");
    setCustomProviderModel("");
    setEditingCustomProviderId(null);
  };

  const handleSaveCustomProvider = async () => {
    if (!token) return;
    if (!customProviderDisplayName.trim() || !customProviderBaseUrl.trim() ||
        !customProviderApiKey.trim() || !customProviderModel.trim()) {
      toast.error("All fields are required");
      return;
    }
    const urlPattern = /^https?:\/\/[^\s/$.?#].[^\s]*$/;
    if (!urlPattern.test(customProviderBaseUrl.trim())) {
      toast.error("Invalid base URL format");
      return;
    }
    setCustomProviderSaving(true);
    try {
      const payload: Record<string, unknown> = {};
      if (editingCustomProviderId) {
        payload.llm_custom_provider_update = {
          id: editingCustomProviderId,
          display_name: customProviderDisplayName.trim(),
          base_url: customProviderBaseUrl.trim(),
          api_key: customProviderApiKey.trim(),
          model: customProviderModel.trim(),
        };
      } else {
        payload.llm_custom_provider_add = {
          display_name: customProviderDisplayName.trim(),
          base_url: customProviderBaseUrl.trim(),
          api_key: customProviderApiKey.trim(),
          model: customProviderModel.trim(),
        };
      }
      const updated = await apiFetch<Settings>(
        "/api/v1/settings",
        { method: "PUT", body: JSON.stringify(payload) },
        token
      );
      setSettings(updated);
      resetCustomProviderForm();
      toast.success(editingCustomProviderId ? "Provider updated" : "Provider added");
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setCustomProviderSaving(false);
    }
  };

  const handleEditCustomProvider = (provider: CustomProvider) => {
    setEditingCustomProviderId(provider.id);
    setCustomProviderDisplayName(provider.display_name);
    setCustomProviderBaseUrl(provider.base_url);
    setCustomProviderModel(provider.model);
    setCustomProviderApiKey("");
  };

  const handleRemoveCustomProvider = async (providerId: string) => {
    if (!token) return;
    setTestingCustomProviderId(providerId);
    try {
      const updated = await apiFetch<Settings>(
        "/api/v1/settings",
        { method: "PUT", body: JSON.stringify({ llm_custom_providers_remove: [providerId] }) },
        token
      );
      setSettings(updated);
      if (editingCustomProviderId === providerId) resetCustomProviderForm();
      toast.success("Provider removed");
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setTestingCustomProviderId(null);
    }
  };

  const handleTestCustomProvider = async (providerId: string) => {
    if (!token) return;
    setTestingCustomProviderId(providerId);
    try {
      const result = await apiFetch<{ ok: boolean; provider: string }>(
        `/api/v1/settings/test-custom-provider?provider_id=${encodeURIComponent(providerId)}`,
        { method: "POST" },
        token
      );
      toast.success(`${result.provider} connection successful!`);
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setTestingCustomProviderId(null);
    }
  };

  if (!settings) return <SettingsSkeleton />;

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-4 pb-28 md:p-6 md:pb-32">
      <WorkspacePageHeader
        eyebrow="Control center"
        title="Settings"
        description="Manage model access, private keys, radar inputs, and the profile StewardMe uses to personalise guidance."
        badge={settings.using_shared_key ? "Lite mode active" : "Full mode"}
      />

      <nav aria-label="Settings sections" className="flex flex-wrap gap-2">
        {sectionLinks.map((section) => (
          <Button key={section.id} asChild size="sm" variant="outline">
            <a href={`#${section.id}`}>{section.label}</a>
          </Button>
        ))}
      </nav>

      <section id="account">
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
              <Button size="icon" variant="ghost" onClick={() => setEditingName(true)} className="h-7 w-7 shrink-0 mt-3" aria-label="Edit display name">
                <Pencil className="h-3 w-3" />
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
      </section>

      <section id="ai-settings">
      <Card>
        <CardHeader>
          <CardTitle>LLM Providers</CardTitle>
          <CardDescription>Configure your default provider and connect multiple council members</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-1.5">
            <Label>Default lead provider</Label>
            <p className="text-xs text-muted-foreground">Normal fast answers use this provider when its key is configured.</p>
            <Select
              value={
                (form.llm_provider as string | undefined)
                || (["claude", "openai", "gemini"].includes(settings.llm_provider || "")
                  ? (settings.llm_provider || "claude")
                  : "claude")
              }
              onValueChange={(v) => setForm({ ...form, llm_provider: v })}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="claude">Claude</SelectItem>
                <SelectItem value="openai">OpenAI</SelectItem>
                <SelectItem value="gemini">Gemini</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label>Council mode</Label>
            <p className="text-xs text-muted-foreground">When enabled, steward can use multiple configured providers for important or open-ended advice prompts.</p>
            <Select
              value={(form.llm_council_enabled as string | undefined) || String(settings.llm_council_enabled)}
              onValueChange={(v) => setForm({ ...form, llm_council_enabled: v })}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="true">Enabled</SelectItem>
                <SelectItem value="false">Disabled</SelectItem>
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
          <div className="rounded-lg border p-3 text-sm">
            <div className="flex items-center justify-between gap-2">
              <div>
                <p className="font-medium">Council readiness</p>
                <p className="text-xs text-muted-foreground">
                  {settings.llm_council_ready
                    ? "Two or more provider keys are configured, so council mode can be used on eligible advice prompts."
                    : "Add at least two provider keys to enable council-assisted answers."}
                </p>
              </div>
              <Badge variant={settings.llm_council_ready ? "default" : "secondary"}>
                {settings.llm_council_ready ? "Council ready" : "Need 2 providers"}
              </Badge>
            </div>
          </div>

          <div className="space-y-4">
            {[
              { provider: "claude", label: "Claude API Key" },
              { provider: "openai", label: "OpenAI API Key" },
              { provider: "gemini", label: "Gemini API Key" },
            ].map(({ provider, label }) => {
              const status = providerStatus(provider);
              return (
                <div key={provider} className="space-y-2 rounded-lg border p-3">
                  <div className="flex items-center justify-between gap-2">
                    <div>
                      <p className="text-sm font-medium capitalize">{provider}</p>
                      <p className="text-xs text-muted-foreground">
                        Stored separately so steward can compare perspectives when council mode is eligible.
                      </p>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        type="button"
                        size="sm"
                        variant="outline"
                        disabled={!status?.configured || testingProvider === provider}
                        onClick={() => handleTestProvider(provider)}
                      >
                        {testingProvider === provider ? "Testing..." : "Test"}
                      </Button>
                      <Button
                        type="button"
                        size="sm"
                        variant="ghost"
                        disabled={!status?.configured || testingProvider === provider}
                        onClick={() => handleRemoveProviderKey(provider)}
                      >
                        <Trash2 className="mr-1 h-3.5 w-3.5" />
                        Remove
                      </Button>
                    </div>
                  </div>
                  <ApiKeyInput
                    label={label}
                    name={`llm_api_key_${provider}`}
                    value={(form[`llm_api_key_${provider}`] as string | undefined) || ""}
                    onChange={(v) => setForm({ ...form, [`llm_api_key_${provider}`]: v })}
                    isSet={status?.configured || false}
                    hint={status?.hint}
                    description="Optional. Your key is encrypted and stored per-user."
                  />
                </div>
              );
            })}
          </div>

          <Separator className="my-6" />

          <div className="space-y-4">
            <div>
              <h3 className="text-sm font-semibold">Custom Providers (OpenAI-compatible)</h3>
              <p className="text-xs text-muted-foreground mt-1">
                Add any provider that implements the OpenAI chat completions API: Together AI, Groq, Fireworks, OpenRouter, Ollama, vLLM, LM Studio, etc.
              </p>
            </div>

            {settings.llm_custom_providers.length > 0 && (
              <div className="space-y-2">
                {settings.llm_custom_providers.map((provider) => (
                  <div key={provider.id} className="rounded-lg border p-3">
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-medium">{provider.display_name}</p>
                        <p className="text-xs text-muted-foreground truncate">
                          {provider.base_url} • {provider.model}
                        </p>
                      </div>
                      <div className="flex gap-1 shrink-0">
                        <Button
                          type="button"
                          size="sm"
                          variant="outline"
                          disabled={testingCustomProviderId === provider.id}
                          onClick={() => handleTestCustomProvider(provider.id)}
                          className="h-7 text-xs"
                        >
                          {testingCustomProviderId === provider.id ? "Testing..." : "Test"}
                        </Button>
                        <Button
                          type="button"
                          size="sm"
                          variant="ghost"
                          onClick={() => handleEditCustomProvider(provider)}
                          className="h-7 w-7 p-0"
                          aria-label={`Edit ${provider.display_name}`}
                        >
                          <Pencil className="h-3 w-3" />
                        </Button>
                        <Button
                          type="button"
                          size="sm"
                          variant="ghost"
                          disabled={testingCustomProviderId === provider.id}
                          onClick={() => handleRemoveCustomProvider(provider.id)}
                          className="h-7 w-7 p-0"
                          aria-label={`Remove ${provider.display_name}`}
                        >
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            <div className="space-y-3 rounded-lg border p-4 bg-muted/30">
              <p className="text-sm font-medium">{editingCustomProviderId ? "Edit Provider" : "Add Provider"}</p>
              <div className="grid gap-3 sm:grid-cols-2">
                <div>
                  <Label className="text-xs text-muted-foreground">Display Name</Label>
                  <Input
                    value={customProviderDisplayName}
                    onChange={(e) => setCustomProviderDisplayName(e.target.value)}
                    placeholder="e.g., Together – Llama 3"
                    className="mt-1 h-8 text-sm"
                  />
                </div>
                <div>
                  <Label className="text-xs text-muted-foreground">Base URL</Label>
                  <Input
                    value={customProviderBaseUrl}
                    onChange={(e) => setCustomProviderBaseUrl(e.target.value)}
                    placeholder="https://api.together.xyz/v1"
                    className="mt-1 h-8 text-sm"
                  />
                </div>
              </div>
              <div className="grid gap-3 sm:grid-cols-2">
                <div>
                  <Label className="text-xs text-muted-foreground">API Key</Label>
                  <Input
                    type="password"
                    value={customProviderApiKey}
                    onChange={(e) => setCustomProviderApiKey(e.target.value)}
                    placeholder="Your API key"
                    className="mt-1 h-8 text-sm"
                  />
                </div>
                <div>
                  <Label className="text-xs text-muted-foreground">Model ID</Label>
                  <Input
                    value={customProviderModel}
                    onChange={(e) => setCustomProviderModel(e.target.value)}
                    placeholder="e.g., meta-llama/Llama-3-70b-chat-hf"
                    className="mt-1 h-8 text-sm"
                  />
                </div>
              </div>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  onClick={handleSaveCustomProvider}
                  disabled={customProviderSaving}
                  className="h-8"
                >
                  {customProviderSaving ? "Saving..." : editingCustomProviderId ? "Update" : "Add"}
                </Button>
                {editingCustomProviderId && (
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={resetCustomProviderForm}
                    className="h-8"
                  >
                    Cancel
                  </Button>
                )}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
      </section>

      <section id="usage">
      <Card>
        <CardHeader>
          <CardTitle>Usage</CardTitle>
          <CardDescription>Estimated LLM cost for advisor queries (last 30 days)</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {usageStats && usageStats.by_model.length > 0 ? (
            <>
              <div className="flex flex-wrap gap-4 text-sm">
                <div>
                  <p className="text-xs text-muted-foreground">Total queries</p>
                  <p className="text-lg font-semibold">{usageStats.total_queries}</p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Estimated cost</p>
                  <p className="text-lg font-semibold">${usageStats.total_estimated_cost_usd.toFixed(4)}</p>
                </div>
              </div>
              <div className="space-y-2">
                {usageStats.by_model.map((m) => (
                  <div key={m.model} className="flex items-center justify-between rounded-lg border p-3 text-sm">
                    <div>
                      <p className="font-medium">{m.model}</p>
                      <p className="text-xs text-muted-foreground">
                        {m.query_count} {m.query_count === 1 ? "query" : "queries"} &middot; {m.input_tokens.toLocaleString()} in / {m.output_tokens.toLocaleString()} out tokens
                      </p>
                    </div>
                    <p className="font-mono text-xs">${m.estimated_cost_usd.toFixed(4)}</p>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <p className="text-sm text-muted-foreground">No usage data yet.</p>
          )}
        </CardContent>
      </Card>
      </section>

      <section id="api-keys">
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
      </section>

      <section id="features">
      <Card>
        <CardHeader>
          <CardTitle>Features</CardTitle>
          <CardDescription>Enable or disable optional capabilities for your account.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-3">
            <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Advisor</p>
            {([
              { key: "feature_extended_thinking", label: "Extended thinking", description: "Deeper reasoning before responding. Higher token cost." },
              { key: "feature_memory_enabled", label: "Memory", description: "Distilled facts from journal entries to personalise advice." },
              { key: "feature_threads_enabled", label: "Recurring thoughts", description: "Detect patterns across journal entries." },
              { key: "feature_recommendations_enabled", label: "Weekly recommendations", description: "Generate action recommendations each week." },
            ] as const).map(({ key, label, description }) => (
              <div key={key} className="flex items-center justify-between gap-4 rounded-lg border p-3">
                <div className="space-y-0.5">
                  <p className="text-sm font-medium">{label}</p>
                  <p className="text-xs text-muted-foreground">{description}</p>
                </div>
                <Switch
                  checked={form[key] !== undefined ? form[key] === "true" : settings?.[key] ?? false}
                  onCheckedChange={(checked) => setForm({ ...form, [key]: String(checked) })}
                />
              </div>
            ))}
          </div>

          <Separator />

          <div className="space-y-3">
            <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Intelligence</p>
            {([
              { key: "feature_research_enabled", label: "Research", description: "Generate topic reports from saved context and live web search." },
              { key: "feature_entity_extraction_enabled", label: "Entity extraction", description: "Extract companies, people, and concepts from intel." },
              { key: "feature_trending_radar_enabled", label: "Trending radar", description: "Cross-source topic convergence detection." },
              { key: "feature_heartbeat_enabled", label: "Goal-intel matching", description: "Proactively match incoming intel to your goals." },
            ] as const).map(({ key, label, description }) => (
              <div key={key} className="flex items-center justify-between gap-4 rounded-lg border p-3">
                <div className="space-y-0.5">
                  <p className="text-sm font-medium">{label}</p>
                  <p className="text-xs text-muted-foreground">{description}</p>
                </div>
                <Switch
                  checked={form[key] !== undefined ? form[key] === "true" : settings?.[key] ?? false}
                  onCheckedChange={(checked) => setForm({ ...form, [key]: String(checked) })}
                />
              </div>
            ))}
          </div>

          <Separator />

          <div className="space-y-3">
            <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">Signal pipelines</p>
            {([
              { key: "feature_company_movement_enabled", label: "Company movements", description: "Track strategic moves at watchlisted companies." },
              { key: "feature_hiring_signals_enabled", label: "Hiring signals", description: "Detect hiring spikes and role pattern shifts." },
              { key: "feature_regulatory_signals_enabled", label: "Regulatory alerts", description: "Surface relevant regulatory changes." },
            ] as const).map(({ key, label, description }) => (
              <div key={key} className="flex items-center justify-between gap-4 rounded-lg border p-3">
                <div className="space-y-0.5">
                  <p className="text-sm font-medium">{label}</p>
                  <p className="text-xs text-muted-foreground">{description}</p>
                </div>
                <Switch
                  checked={form[key] !== undefined ? form[key] === "true" : settings?.[key] ?? false}
                  onCheckedChange={(checked) => setForm({ ...form, [key]: String(checked) })}
                />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
      </section>

      <section id="rss-feeds">
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
                  aria-label={`Remove ${feed.name || new URL(feed.url).hostname}`}
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
      </section>

      <section id="watchlist">
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
                    <Badge variant="outline" className="text-[10px]">{item.kind}</Badge>
                    <Badge variant="outline" className="text-[10px]">{item.priority}</Badge>
                  </div>
                  {item.why && <p className="text-sm text-muted-foreground">{item.why}</p>}
                  {(item.domain || item.github_org || item.ticker || item.topics.length > 0 || item.geographies.length > 0) && (
                    <p className="text-xs text-muted-foreground">
                      {[item.domain, item.github_org, item.ticker, ...item.topics, ...item.geographies]
                        .filter(Boolean)
                        .slice(0, 4)
                        .join(" ? ")}
                    </p>
                  )}
                  {item.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1 pt-1">
                      {item.tags.map((tag) => (
                        <Badge key={tag} variant="secondary" className="text-[10px]">{tag}</Badge>
                      ))}
                    </div>
                  )}
                </div>
                <div className="flex items-center gap-1 shrink-0">
                  <Button size="icon" variant="ghost" className="h-7 w-7" onClick={() => handleEditWatch(item)} aria-label={`Edit ${item.label}`}>
                    <Pencil className="h-3 w-3" />
                  </Button>
                  <Button
                    size="icon"
                    variant="ghost"
                    className="h-7 w-7"
                    disabled={watchRemoving === item.id}
                    onClick={() => handleRemoveWatch(item.id)}
                    aria-label={`Remove ${item.label}`}
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
            <div className="grid gap-3 sm:grid-cols-2">
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
                <Label className="text-xs text-muted-foreground">Type</Label>
                <Select value={watchKind} onValueChange={setWatchKind}>
                  <SelectTrigger className="mt-1 h-8 text-sm">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {WATCH_KINDS.map((kind) => (
                      <SelectItem key={kind.value} value={kind.value}>{kind.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
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
                <Select value={watchPriority} onValueChange={(value) => setWatchPriority(value as "high" | "medium" | "low")}>
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
                <Label className="text-xs text-muted-foreground">Aliases</Label>
                <Input
                  value={watchAliases}
                  onChange={(e) => setWatchAliases(e.target.value)}
                  placeholder="Open AI, OA"
                  className="mt-1 h-8 text-sm"
                />
              </div>
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              <div>
                <Label className="text-xs text-muted-foreground">Tags</Label>
                <Input
                  value={watchTags}
                  onChange={(e) => setWatchTags(e.target.value)}
                  placeholder="career, startup, infrastructure"
                  className="mt-1 h-8 text-sm"
                />
              </div>
              <div>
                <Label className="text-xs text-muted-foreground">Goal / intent</Label>
                <Input
                  value={watchGoal}
                  onChange={(e) => setWatchGoal(e.target.value)}
                  placeholder="e.g. competitor tracking"
                  className="mt-1 h-8 text-sm"
                />
              </div>
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              <div>
                <Label className="text-xs text-muted-foreground">Source preferences</Label>
                <Input
                  value={watchSourcePreferences}
                  onChange={(e) => setWatchSourcePreferences(e.target.value)}
                  placeholder="rss, eu, sec"
                  className="mt-1 h-8 text-sm"
                />
              </div>
              {watchKind === "company" ? (
                <div>
                  <Label className="text-xs text-muted-foreground">Company domain</Label>
                  <Input
                    value={watchDomain}
                    onChange={(e) => setWatchDomain(e.target.value)}
                    placeholder="openai.com"
                    className="mt-1 h-8 text-sm"
                  />
                </div>
              ) : (
                <div>
                  <Label className="text-xs text-muted-foreground">Topics</Label>
                  <Input
                    value={watchTopics}
                    onChange={(e) => setWatchTopics(e.target.value)}
                    placeholder="AI Act, privacy"
                    className="mt-1 h-8 text-sm"
                  />
                </div>
              )}
            </div>
            {watchKind === "company" ? (
              <div className="grid gap-3 sm:grid-cols-2">
                <div>
                  <Label className="text-xs text-muted-foreground">GitHub org</Label>
                  <Input
                    value={watchGithubOrg}
                    onChange={(e) => setWatchGithubOrg(e.target.value)}
                    placeholder="openai"
                    className="mt-1 h-8 text-sm"
                  />
                </div>
                <div>
                  <Label className="text-xs text-muted-foreground">Ticker</Label>
                  <Input
                    value={watchTicker}
                    onChange={(e) => setWatchTicker(e.target.value)}
                    placeholder="MSFT"
                    className="mt-1 h-8 text-sm"
                  />
                </div>
              </div>
            ) : (
              <div>
                <Label className="text-xs text-muted-foreground">Geographies</Label>
                <Input
                  value={watchGeographies}
                  onChange={(e) => setWatchGeographies(e.target.value)}
                  placeholder="EU, UK, US"
                  className="mt-1 h-8 text-sm"
                />
              </div>
            )}
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
      </section>

      <section id="profile">
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
      </section>

      <section id="memory">
      <Card>
        <CardHeader>
          <CardTitle>What I know about you</CardTitle>
          <CardDescription>
            Transparent memory facts that help StewardMe personalize advice, focus, and monitoring.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {memoryStats ? (
            <div className="flex flex-wrap gap-2 text-xs text-muted-foreground">
              <Badge variant="secondary">{memoryStats.total_active} active facts</Badge>
              {Object.entries(memoryStats.by_category).map(([category, count]) => (
                <Badge key={category} variant="outline">
                  {category}: {count}
                </Badge>
              ))}
            </div>
          ) : null}

          {memoryFacts.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No active memory facts yet. As you capture notes and ask questions, durable facts will show up here.
            </p>
          ) : (
            <div className="space-y-3">
              {memoryFacts.map((fact) => (
                <div key={fact.id} className="flex items-start justify-between gap-3 rounded-lg border p-3">
                  <div className="space-y-2">
                    <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                      <Badge variant="secondary">{fact.category}</Badge>
                      <Badge variant="outline">Confidence {Math.round(fact.confidence * 100)}%</Badge>
                      <span>
                        Updated {fact.updated_at ? new Date(fact.updated_at).toLocaleDateString() : "recently"}
                      </span>
                    </div>
                    <p className="text-sm">{fact.text}</p>
                    <p className="text-xs text-muted-foreground">
                      Source: {fact.source_type}{fact.source_id ? ` • ${fact.source_id}` : ""}
                    </p>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 shrink-0"
                    onClick={() => handleDeleteFact(fact.id)}
                    disabled={deletingFactId === fact.id}
                    aria-label={`Delete memory fact ${fact.id}`}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
      </section>

      <section id="danger-zone">
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
      </section>
      <DeleteAccountModal open={deleteOpen} onOpenChange={setDeleteOpen} />

      {isDirty && (
        <div className="fixed bottom-0 left-0 right-0 z-20 border-t bg-background/95 backdrop-blur lg:left-60">
          <div className="mx-auto flex max-w-7xl flex-col gap-3 px-4 py-3 sm:flex-row sm:items-center sm:justify-between md:px-6">
            <div>
              <p className="text-sm font-medium">You have unsaved settings changes</p>
              <p className="text-xs text-muted-foreground">
                {Object.keys(form).length} pending {Object.keys(form).length === 1 ? "update" : "updates"} across provider and key settings.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Button variant="outline" onClick={() => setForm({})} disabled={saving}>
                Discard
              </Button>
              <Button onClick={handleSave} disabled={saving}>
                {saving ? "Saving..." : "Save changes"}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
