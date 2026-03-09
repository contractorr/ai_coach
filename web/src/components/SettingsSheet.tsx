"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";
import { RefreshCw, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
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
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";
import { Separator } from "@/components/ui/separator";
import { ApiKeyInput } from "@/components/ApiKeyInput";
import { OnboardingDialog } from "@/components/OnboardingDialog";
import { apiFetch } from "@/lib/api";

interface LLMProviderKeyStatus {
  provider: string;
  configured: boolean;
  hint: string | null;
  council_eligible: boolean;
}

interface Settings {
  llm_provider: string | null;
  llm_model: string | null;
  llm_council_enabled: boolean;
  llm_council_ready: boolean;
  llm_provider_keys: LLMProviderKeyStatus[];
  llm_api_key_set: boolean;
  llm_api_key_hint: string | null;
  tavily_api_key_set: boolean;
  tavily_api_key_hint: string | null;
  github_token_set: boolean;
  github_token_hint: string | null;
  eventbrite_token_set: boolean;
}

export function SettingsSheet({
  open,
  onOpenChange,
  token,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  token: string;
}) {
  const [settings, setSettings] = useState<Settings | null>(null);
  const [form, setForm] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [testingProvider, setTestingProvider] = useState<string | null>(null);

  const isDirty = Object.keys(form).length > 0;

  useEffect(() => {
    if (!open || !token) return;
    apiFetch<Settings>("/api/settings", {}, token)
      .then(setSettings)
      .catch((e) => toast.error(e.message));
  }, [open, token]);

  const handleSave = async () => {
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

  const providerStatus = (provider: string) =>
    settings?.llm_provider_keys.find((item) => item.provider === provider);

  const handleRemoveProviderKey = async (provider: string) => {
    setTestingProvider(provider);
    try {
      const updated = await apiFetch<Settings>(
        "/api/settings",
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
    setTestingProvider(provider);
    try {
      const result = await apiFetch<{ ok: boolean; provider: string }>(
        `/api/settings/test-llm?provider=${encodeURIComponent(provider)}`,
        { method: "POST" },
        token
      );
      toast.success(`${result.provider} connection ok`);
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setTestingProvider(null);
    }
  };

  return (
    <>
      <Sheet open={open} onOpenChange={onOpenChange}>
        <SheetContent className="overflow-y-auto">
          <SheetHeader>
            <SheetTitle>Settings</SheetTitle>
            <SheetDescription>Configure your steward&apos;s AI model and API keys</SheetDescription>
          </SheetHeader>

          {!settings ? (
            <div className="space-y-4 px-6 py-4">
              {Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="h-9 w-full animate-pulse rounded bg-muted" />
              ))}
            </div>
          ) : (
            <div className="space-y-6 px-6 pb-6">
              {/* LLM Provider */}
              <div className="space-y-4">
                <h3 className="text-sm font-medium">LLM Providers</h3>
                <div className="space-y-1.5">
                  <Label>Default lead provider</Label>
                  <p className="text-xs text-muted-foreground">
                    Normal fast answers use this provider when its key is configured.
                  </p>
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
                  <Label>Model (optional)</Label>
                  <p className="text-xs text-muted-foreground">
                    Leave blank for the provider&apos;s default model.
                  </p>
                  <Input
                    placeholder="e.g. claude-sonnet-4-20250514"
                    value={form.llm_model || ""}
                    onChange={(e) => setForm({ ...form, llm_model: e.target.value })}
                  />
                </div>
                <div className="space-y-1.5">
                  <Label>Council mode</Label>
                  <p className="text-xs text-muted-foreground">
                    Steward can use multiple configured providers for important or open-ended advice prompts.
                  </p>
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
                <div className="rounded-lg border p-3 text-sm">
                  <div className="flex items-center justify-between gap-2">
                    <div>
                      <p className="font-medium">Council readiness</p>
                      <p className="text-xs text-muted-foreground">
                        {settings.llm_council_ready
                          ? "Two or more provider keys are configured, so council mode can be used on eligible prompts."
                          : "Add at least two provider keys to enable council-assisted answers."}
                      </p>
                    </div>
                    <span className="text-xs font-medium text-muted-foreground">
                      {settings.llm_council_ready ? "Council ready" : "Need 2 providers"}
                    </span>
                  </div>
                </div>
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

              <Separator />

              {/* Other API Keys */}
              <div className="space-y-4">
                <h3 className="text-sm font-medium">API Keys</h3>
                <ApiKeyInput
                  label="Tavily API Key"
                  name="tavily_api_key"
                  value={form.tavily_api_key || ""}
                  onChange={(v) => setForm({ ...form, tavily_api_key: v })}
                  isSet={settings.tavily_api_key_set}
                  hint={settings.tavily_api_key_hint}
                  description="Optional. Enables web search for deep research."
                />
                <ApiKeyInput
                  label="GitHub Token"
                  name="github_token"
                  value={form.github_token || ""}
                  onChange={(v) => setForm({ ...form, github_token: v })}
                  isSet={settings.github_token_set}
                  hint={settings.github_token_hint}
                  description="Optional. Raises GitHub scraper rate limit."
                />
              </div>

              <Separator />

              {/* Profile */}
              <div className="space-y-2">
                <h3 className="text-sm font-medium">Profile</h3>
                <p className="text-xs text-muted-foreground">
                  Re-run onboarding to update your profile and goals
                </p>
                <Button variant="outline" size="sm" onClick={() => setShowOnboarding(true)}>
                  <RefreshCw className="mr-2 h-3.5 w-3.5" />
                  Restart Onboarding
                </Button>
              </div>

              <Separator />

              <Button onClick={handleSave} disabled={saving || !isDirty} className="w-full">
                {saving ? "Saving..." : isDirty ? "Save Changes" : "No Changes"}
              </Button>
            </div>
          )}
        </SheetContent>
      </Sheet>

      <OnboardingDialog
        open={showOnboarding}
        onClose={() => setShowOnboarding(false)}
        onComplete={() => {
          apiFetch<Settings>("/api/settings", {}, token)
            .then(setSettings)
            .catch(() => {});
        }}
        token={token}
        startPhase={settings?.llm_api_key_set ? "chat" : "intro"}
      />
    </>
  );
}
