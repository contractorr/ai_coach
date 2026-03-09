"use client";

import { useRef, useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import ReactMarkdown from "react-markdown";
import {
  Brain,
  BookOpen,
  Home,
  MessageSquare,
  Newspaper,
  Target,
  Sparkles,
  Send,
  FlaskConical,
  ArrowRight,
  ExternalLink,
  Globe,
  Server,
  Shield,
  Rocket,
  BarChart3,
  Cloud,
  Smartphone,
  GitBranch,
  Link,
  Rss,
  Check,
  type LucideIcon,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useToken } from "@/hooks/useToken";
import { apiFetch } from "@/lib/api";
import { toast } from "sonner";

type Phase = "intro" | "name" | "welcome" | "chat" | "feeds" | "guide" | "done";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

interface FeedCategoryItem {
  id: string;
  label: string;
  icon: string;
  feed_count: number;
  preselected: boolean;
}

const CATEGORY_ICONS: Record<string, LucideIcon> = {
  ai_ml: Brain,
  web_dev: Globe,
  systems_infra: Server,
  security: Shield,
  startups_vc: Rocket,
  data_science: BarChart3,
  devops_cloud: Cloud,
  mobile: Smartphone,
  general_tech: Newspaper,
  open_source: GitBranch,
  blockchain_web3: Link,
};

const introSections = [
  {
    icon: Newspaper,
    title: "Intelligence Radar",
    description:
      "Scans HN, GitHub trending, arXiv, Reddit & RSS. Surfaces what matters, skips the noise.",
  },
  {
    icon: Brain,
    title: "AI Steward",
    description:
      "Proactive guidance grounded in your context and real-time intel. Spots opportunities, flags what needs attention.",
  },
  {
    icon: Target,
    title: "Goal Alignment",
    description:
      "Tracks objectives against trends and opportunities. Flags when priorities should shift.",
  },
  {
    icon: BookOpen,
    title: "Journal",
    description:
      "Capture reflections, decisions, and observations. Every entry sharpens your steward's guidance.",
  },
  {
    icon: FlaskConical,
    title: "Deep Research",
    description:
      "Deep dives into opportunities, technologies, or trends — driven by your goals and interests.",
  },
];

export const guideCards = [
  {
    icon: Home,
    title: "Check your brief",
    description: "Your daily dashboard — prioritized tasks, goal updates, and signals. Start here each day.",
  },
  {
    icon: BookOpen,
    title: "Journal daily",
    description: "Capture thoughts, decisions, observations. Every entry sharpens your steward's guidance.",
  },
  {
    icon: MessageSquare,
    title: "Ask anything",
    description: "Decisions, priorities, strategy — tap any item or type a question to start a conversation.",
  },
  {
    icon: Newspaper,
    title: "Intel runs in background",
    description: "Scrapers watch HN, GitHub, arXiv, Reddit & RSS. Relevant items surface automatically.",
  },
];

export default function OnboardingPage() {
  const token = useToken();
  const router = useRouter();
  const [phase, setPhase] = useState<Phase>("name");
  const [provider, setProvider] = useState("auto");
  const [apiKey, setApiKey] = useState("");
  const [saving, setSaving] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [goalsCreated, setGoalsCreated] = useState(0);
  const [turn, setTurn] = useState(0);
  const [hasApiKey, setHasApiKey] = useState<boolean | null>(null);
  const [usingSharedKey, setUsingSharedKey] = useState(false);
  const [name, setName] = useState("");
  const [feedCategories, setFeedCategories] = useState<FeedCategoryItem[]>([]);
  const [selectedFeeds, setSelectedFeeds] = useState<Set<string>>(new Set());
  const [feedsAdded, setFeedsAdded] = useState(0);
  const [savingFeeds, setSavingFeeds] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Check if user already has API key to skip welcome phase
  useEffect(() => {
    if (!token) return;
    apiFetch<{ llm_api_key_set: boolean; using_shared_key: boolean }>("/api/settings", {}, token)
      .then((s) => {
        setHasApiKey(s.llm_api_key_set);
        setUsingSharedKey(s.using_shared_key);
        if (s.llm_api_key_set) setPhase("chat");
      })
      .catch(() => setHasApiKey(false));
  }, [token]);

  // Auto-start chat when entering chat phase
  useEffect(() => {
    if (phase !== "chat" || !token || messages.length > 0) return;
    (async () => {
      setSending(true);
      try {
        const res = await apiFetch<{ message: string; done: boolean; turn: number }>(
          "/api/onboarding/start",
          { method: "POST" },
          token
        );
        setMessages([{ role: "assistant", content: res.message }]);
        setTurn(res.turn);
      } catch (e) {
        toast.error((e as Error).message);
      } finally {
        setSending(false);
      }
    })();
  }, [phase, token, messages.length]);

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages, sending]);

  const handleDone = useCallback(() => {
    router.replace("/");
  }, [router]);

  // Auto-redirect after done
  useEffect(() => {
    if (phase === "done") {
      const timer = setTimeout(handleDone, 3000);
      return () => clearTimeout(timer);
    }
  }, [phase, handleDone]);

  const handleSaveName = async () => {
    if (!token || !name.trim()) return;
    try {
      await apiFetch(
        "/api/user/me",
        { method: "PATCH", body: JSON.stringify({ name: name.trim() }) },
        token
      );
    } catch {
      // non-blocking — name is optional
    }
    setPhase(hasApiKey ? "chat" : "welcome");
  };

  const handleSkipKey = () => {
    setUsingSharedKey(true);
    setPhase("chat");
  };

  const [testing, setTesting] = useState(false);

  const handleSaveKey = async () => {
    if (!apiKey.trim()) {
      toast.error("Please enter an API key");
      return;
    }
    if (!token) return;
    setSaving(true);
    try {
      const payload: Record<string, string> = { llm_api_key: apiKey };
      if (provider !== "auto") payload.llm_provider = provider;
      await apiFetch(
        "/api/settings",
        { method: "PUT", body: JSON.stringify(payload) },
        token
      );

      // Connectivity test
      setTesting(true);
      try {
        await apiFetch<{ ok: boolean; provider: string }>(
          "/api/settings/test-llm",
          { method: "POST" },
          token
        );
        toast.success("Connected to LLM");
      } catch (e) {
        toast.error(`Key saved but LLM test failed: ${(e as Error).message}`);
      } finally {
        setTesting(false);
      }

      setPhase("chat");
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setSaving(false);
    }
  };

  const handleSend = async () => {
    if (!input.trim() || sending || !token) return;
    const text = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setSending(true);

    try {
      const res = await apiFetch<{
        message: string;
        done: boolean;
        goals_created: number;
        turn: number;
      }>(
        "/api/onboarding/chat",
        { method: "POST", body: JSON.stringify({ message: text }) },
        token
      );
      setMessages((prev) => [...prev, { role: "assistant", content: res.message }]);
      setTurn(res.turn);
      if (res.done) {
        setGoalsCreated(res.goals_created);
        setPhase("feeds");
      }
    } catch (e) {
      const msg = (e as Error).message;
      if (msg.includes("No active onboarding session")) {
        // Session lost (server restart) — re-start and replay the message
        toast.info("Session expired, restarting...");
        setMessages([]);
        setTurn(0);
        setPhase("chat"); // triggers auto-start effect
      } else {
        toast.error(msg);
      }
    } finally {
      setSending(false);
    }
  };

  // Load feed categories when entering feeds phase
  useEffect(() => {
    if (phase !== "feeds" || !token) return;
    (async () => {
      try {
        const cats = await apiFetch<FeedCategoryItem[]>(
          "/api/onboarding/feed-categories",
          {},
          token
        );
        setFeedCategories(cats);
        setSelectedFeeds(new Set(cats.filter((c) => c.preselected).map((c) => c.id)));
      } catch (e) {
        toast.error((e as Error).message);
        handleDone();
      }
    })();
  }, [phase, token, handleDone]);

  const handleToggleFeed = (id: string) => {
    setSelectedFeeds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const handleSaveFeeds = async () => {
    if (!token) return;
    setSavingFeeds(true);
    try {
      const res = await apiFetch<{ feeds_added: number; categories: string[] }>(
        "/api/onboarding/feeds",
        {
          method: "POST",
          body: JSON.stringify({ selected_category_ids: [...selectedFeeds] }),
        },
        token
      );
      setFeedsAdded(res.feeds_added);
      handleDone();
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setSavingFeeds(false);
    }
  };

  if (!token || hasApiKey === null) return null;

  return (
    <div className="flex h-full items-center justify-center p-4">
      <div className="flex w-full max-w-2xl flex-col rounded-xl border bg-card shadow-sm"
        style={{ height: "min(85vh, 720px)" }}>

        {phase === "intro" && (
          <div className="flex flex-1 flex-col overflow-hidden">
            <div className="px-6 pt-6 pb-2 text-center">
              <div className="mx-auto mb-2 flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
                <Brain className="h-6 w-6 text-primary" />
              </div>
              <h1 className="text-xl font-semibold text-primary">StewardMe</h1>
              <p className="text-sm text-muted-foreground">
                Scans the world. Learns your context. Tells you what matters next.
              </p>
            </div>

            <div className="flex-1 space-y-4 overflow-y-auto px-6 py-4">
              {introSections.map(({ icon: Icon, title, description }) => (
                <div key={title} className="flex gap-3">
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-muted">
                    <Icon className="h-4 w-4 text-muted-foreground" />
                  </div>
                  <div>
                    <p className="text-sm font-medium">{title}</p>
                    <p className="text-xs text-muted-foreground leading-relaxed">
                      {description}
                    </p>
                  </div>
                </div>
              ))}
              <div className="rounded-lg border bg-muted/50 p-3 text-xs text-muted-foreground leading-relaxed">
                <span className="font-medium text-foreground">How it connects:</span>{" "}
                Journal + intel feed your steward. Goals shape what surfaces.
                More context = sharper guidance.
              </div>
            </div>

            <div className="px-6 pb-6">
              <Button
                onClick={() => setPhase("name")}
                className="w-full"
              >
                Continue
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </div>
          </div>
        )}

        {phase === "name" && (
          <div className="flex flex-1 flex-col items-center justify-center px-6">
            <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
              <Brain className="h-6 w-6 text-primary" />
            </div>
            <h2 className="text-lg font-semibold">What should I call you?</h2>
            <p className="mt-1 text-sm text-muted-foreground text-center">
              First name is fine — used for greetings only.
            </p>
            <Input
              value={name}
              onChange={(e) => setName(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSaveName()}
              placeholder="Your name"
              className="mt-4 max-w-xs text-center"
              autoFocus
            />
            <Button onClick={handleSaveName} className="mt-4 w-full max-w-xs">
              Continue
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </div>
        )}

        {phase === "welcome" && (
          <div className="flex flex-1 flex-col overflow-hidden">
            <div className="px-6 pt-6 pb-2 text-center">
              <div className="mx-auto mb-2 flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
                <Brain className="h-6 w-6 text-primary" />
              </div>
              <h1 className="text-xl font-semibold">
                <span className="text-primary">StewardMe</span>
              </h1>
              <p className="text-sm text-muted-foreground">
                Let&apos;s set up your AI steward
              </p>
            </div>

            <div className="flex-1 space-y-6 overflow-y-auto px-6 py-4">
              <div className="rounded-lg border bg-muted/50 p-3 text-xs text-muted-foreground space-y-2">
                <p>
                  An API key is required to power your steward. Your key is
                  encrypted and stored per-user.
                </p>
                <p>
                  <span className="font-medium text-foreground">Need a key?</span>{" "}
                  Go to{" "}
                  <a
                    href="https://console.anthropic.com/settings/keys"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-0.5 underline hover:text-foreground"
                  >
                    console.anthropic.com
                    <ExternalLink className="h-3 w-3" />
                  </a>
                  {" "}&rarr; create a key &rarr; paste it below.
                </p>
              </div>

              <div className="space-y-4">
                <div className="space-y-1.5">
                  <Label>Provider</Label>
                  <Select value={provider} onValueChange={setProvider}>
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
                  <Label>API Key</Label>
                  <Input
                    type="password"
                    placeholder="sk-... or your provider key"
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                  />
                </div>
              </div>
            </div>

            <div className="px-6 pb-6 space-y-2">
              <Button
                onClick={handleSaveKey}
                disabled={saving || testing}
                className="w-full"
              >
                {testing ? "Testing connection..." : saving ? "Saving..." : "Get Started"}
              </Button>
              <button
                onClick={handleSkipKey}
                className="w-full text-center text-xs text-muted-foreground hover:text-foreground"
              >
                Skip &mdash; use lite mode
              </button>
              <div className="rounded-lg border border-amber-200 bg-amber-50 dark:border-amber-900 dark:bg-amber-950/30 p-3 text-xs text-muted-foreground space-y-1">
                <p className="font-medium text-foreground">Lite mode</p>
                <p>Haiku model &middot; 30 queries/day &middot; No deep research</p>
                <p>Add your own key anytime in Settings for the full experience.</p>
              </div>
            </div>
          </div>
        )}

        {phase === "chat" && (
          <div className="flex flex-1 flex-col overflow-hidden">
            <div className="px-6 pt-5 pb-3 border-b">
              <h2 className="text-base font-semibold">
                Let&apos;s set up your profile
              </h2>
              <p className="text-sm text-muted-foreground">
                Answer a few questions so we can personalize your experience
              </p>
            </div>

            <div className="px-6 pt-2">
              <div className="flex items-center justify-between text-xs text-muted-foreground mb-1">
                <span>Question {turn} of ~8</span>
                <span>{Math.min(100, Math.round((turn / 8) * 100))}%</span>
              </div>
              <div className="h-1.5 w-full rounded-full bg-muted overflow-hidden">
                <div
                  className="h-full rounded-full bg-primary transition-all duration-500"
                  style={{ width: `${Math.min(100, (turn / 8) * 100)}%` }}
                />
              </div>
            </div>

            <div
              ref={scrollRef}
              className="flex-1 space-y-3 overflow-y-auto px-6 py-4"
            >
              {messages.map((msg, i) => (
                <div
                  key={i}
                  className={
                    msg.role === "user"
                      ? "ml-8 rounded-lg bg-primary/10 px-3 py-2 text-sm"
                      : "mr-8 rounded-lg bg-muted px-3 py-2 text-sm"
                  }
                >
                  {msg.role === "assistant" ? (
                    <div className="prose prose-sm max-w-none dark:prose-invert">
                      <ReactMarkdown>{msg.content}</ReactMarkdown>
                    </div>
                  ) : (
                    msg.content
                  )}
                </div>
              ))}
              {sending && (
                <div className="mr-8 rounded-lg bg-muted px-3 py-3">
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <div className="flex gap-1">
                      <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-muted-foreground [animation-delay:0ms]" />
                      <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-muted-foreground [animation-delay:150ms]" />
                      <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-muted-foreground [animation-delay:300ms]" />
                    </div>
                    Thinking...
                  </div>
                </div>
              )}
            </div>

            <div className="border-t px-6 py-3">
              <div className="flex gap-2">
                <Textarea
                  placeholder="Type your answer..."
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      handleSend();
                    }
                  }}
                  disabled={sending}
                  rows={2}
                  className="flex-1 max-h-32"
                />
                <Button
                  size="icon"
                  onClick={handleSend}
                  disabled={sending || !input.trim()}
                >
                  <Send className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>
        )}

        {phase === "feeds" && (
          <div className="flex flex-1 flex-col overflow-hidden">
            <div className="px-6 pt-6 pb-2 text-center">
              <div className="mx-auto mb-2 flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
                <Rss className="h-6 w-6 text-primary" />
              </div>
              <h2 className="text-lg font-semibold">Set up your radar</h2>
              <p className="text-sm text-muted-foreground">
                Pick topics to follow — we&apos;ll add curated RSS feeds for each.
              </p>
            </div>

            <div className="flex-1 overflow-y-auto px-6 py-4">
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
                {feedCategories.map((cat) => {
                  const Icon = CATEGORY_ICONS[cat.id] || Newspaper;
                  const selected = selectedFeeds.has(cat.id);
                  return (
                    <button
                      key={cat.id}
                      onClick={() => handleToggleFeed(cat.id)}
                      className={`relative flex flex-col items-center gap-1.5 rounded-lg border p-3 text-center transition-colors ${
                        selected
                          ? "border-primary bg-primary/10 ring-1 ring-primary/30"
                          : "border-muted hover:border-muted-foreground/30"
                      }`}
                    >
                      {selected && (
                        <span className="absolute top-1.5 right-1.5 flex h-4 w-4 items-center justify-center rounded-full bg-primary">
                          <Check className="h-2.5 w-2.5 text-primary-foreground" />
                        </span>
                      )}
                      <Icon className={`h-5 w-5 ${selected ? "text-primary" : "text-muted-foreground"}`} />
                      <span className="text-sm font-medium">{cat.label}</span>
                      <span className="text-xs text-muted-foreground">{cat.feed_count} feeds</span>
                    </button>
                  );
                })}
              </div>
            </div>

            <div className="border-t px-6 py-4">
              <p className="mb-3 text-center text-xs text-muted-foreground">
                {selectedFeeds.size} topic{selectedFeeds.size !== 1 ? "s" : ""} selected
                {" "}&mdash; you can add more from Settings anytime.
              </p>
              <Button
                onClick={handleSaveFeeds}
                disabled={savingFeeds}
                className="w-full"
              >
                {savingFeeds ? "Adding feeds..." : "Continue"}
                {!savingFeeds && <ArrowRight className="ml-2 h-4 w-4" />}
              </Button>
              <button
                onClick={handleDone}
                className="mt-2 w-full text-center text-xs text-muted-foreground hover:text-foreground"
              >
                Skip for now
              </button>
            </div>
          </div>
        )}

        {phase === "guide" && (
          <div className="flex flex-1 flex-col overflow-hidden">
            <div className="px-6 pt-6 pb-2 text-center">
              <div className="mx-auto mb-2 flex h-12 w-12 items-center justify-center rounded-full bg-green-100 dark:bg-green-900/30">
                <Sparkles className="h-6 w-6 text-green-600 dark:text-green-400" />
              </div>
              <h2 className="text-lg font-semibold">
                Profile created
                {goalsCreated > 0
                  ? ` + ${goalsCreated} goal${goalsCreated > 1 ? "s" : ""}`
                  : ""}
                {feedsAdded > 0
                  ? ` + ${feedsAdded} feed${feedsAdded > 1 ? "s" : ""}`
                  : ""}
              </h2>
              <p className="text-sm text-muted-foreground">
                Here&apos;s how to get the most out of your steward.
              </p>
            </div>

            <div className="flex-1 space-y-4 overflow-y-auto px-6 py-4">
              {guideCards.map(({ icon: Icon, title, description }) => (
                <div key={title} className="flex gap-3">
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-muted">
                    <Icon className="h-4 w-4 text-muted-foreground" />
                  </div>
                  <div>
                    <p className="text-sm font-medium">{title}</p>
                    <p className="text-xs text-muted-foreground leading-relaxed">
                      {description}
                    </p>
                  </div>
                </div>
              ))}
              <div className="rounded-lg border bg-muted/50 p-3 text-xs text-muted-foreground leading-relaxed">
                <span className="font-medium text-foreground">Tip:</span>{" "}
                The more you journal and set goals, the sharper your brief gets.
                You can always revisit this from the sidebar.
              </div>
              {usingSharedKey && (
                <div className="rounded-lg border border-amber-200 bg-amber-50 dark:border-amber-900 dark:bg-amber-950/30 p-3 text-xs text-muted-foreground space-y-1">
                  <p className="font-medium text-foreground">Upgrade anytime</p>
                  <p>
                    You&apos;re on lite mode. Add your API key in Settings for
                    fuller responses, deep research, and unlimited usage.
                  </p>
                </div>
              )}
            </div>

            <div className="px-6 pb-6">
              <Button onClick={handleDone} className="w-full">
                Go to Dashboard
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </div>
          </div>
        )}

        {phase === "done" && (
          <div className="flex flex-1 flex-col items-center justify-center px-6">
            <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-green-100 dark:bg-green-900/30">
              <Sparkles className="h-6 w-6 text-green-600 dark:text-green-400" />
            </div>
            <h2 className="text-xl font-semibold">You&apos;re all set!</h2>
            <p className="mt-1 text-sm text-muted-foreground text-center">
              Profile created
              {goalsCreated > 0
                ? ` and ${goalsCreated} goal${goalsCreated > 1 ? "s" : ""} set up`
                : ""}{" "}
              — your steward is ready.
            </p>
            <Button onClick={handleDone} className="mt-6">
              Go to Dashboard
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
