"use client";

import { useRef, useCallback, useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import { Brain, BookOpen, Newspaper, Target, Sparkles, Send, FlaskConical, ArrowRight, ExternalLink } from "lucide-react";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
  SheetFooter,
} from "@/components/ui/sheet";
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
import { apiFetch } from "@/lib/api";
import { toast } from "sonner";

interface OnboardingDialogProps {
  open: boolean;
  onClose: () => void;
  onComplete?: () => void;
  token: string;
  startPhase?: Phase;
}

type Phase = "intro" | "name" | "welcome" | "chat" | "done";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

const features = [
  { icon: Newspaper, text: "Watch what matters across HN, GitHub, arXiv, Reddit, and RSS" },
  { icon: Sparkles, text: "Ask for grounded guidance shaped by your context and live signals" },
  { icon: Target, text: "Keep goals connected to the changes and opportunities around you" },
  { icon: BookOpen, text: "Capture notes and research that sharpen future guidance" },
];

const introSections = [
  {
    icon: Newspaper,
    title: "Radar",
    description:
      "Watches HN, GitHub, arXiv, Reddit, and RSS so the strongest signals rise to the top.",
  },
  {
    icon: Brain,
    title: "Guidance",
    description:
      "Turns your notes, goals, and live signals into grounded help with what to do next.",
  },
  {
    icon: Target,
    title: "Goals",
    description:
      "Keeps your priorities visible so StewardMe can rank what matters against them.",
  },
  {
    icon: BookOpen,
    title: "Journal",
    description:
      "Capture reflections, decisions, and observations. Every entry sharpens future guidance.",
  },
  {
    icon: FlaskConical,
    title: "Research",
    description:
      "Deep dives into opportunities, technologies, or trends — driven by your goals and interests.",
  },
];

export function OnboardingDialog({ open, onClose, onComplete, token, startPhase = "intro" }: OnboardingDialogProps) {
  const [phase, setPhase] = useState<Phase>(startPhase);
  const [name, setName] = useState("");
  const [provider, setProvider] = useState("auto");
  const [apiKey, setApiKey] = useState("");
  const [saving, setSaving] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [goalsCreated, setGoalsCreated] = useState(0);
  const [turn, setTurn] = useState(0);
  const scrollRef = useRef<HTMLDivElement>(null);

  const handleClose = useCallback((completed = false) => {
    if (completed && onComplete) onComplete();
    onClose();
  }, [onClose, onComplete]);

  // When opening in chat phase directly, start the interview
  useEffect(() => {
    if (!open) return;
    setPhase(startPhase);
    setMessages([]);
    setGoalsCreated(0);
    if (startPhase === "chat") {
      (async () => {
        setSending(true);
        try {
          const res = await apiFetch<{ message: string; done: boolean; turn: number }>(
            "/api/v1/onboarding/start",
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
    }
  }, [open, startPhase, token]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, sending]);

  // Auto-close after done
  useEffect(() => {
    if (phase === "done") {
      const timer = setTimeout(() => {
        handleClose(true);
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [phase, handleClose]);

  const handleSaveName = async () => {
    const trimmed = name.trim();
    if (!trimmed) {
      toast.error("Please enter your name");
      return;
    }
    try {
      await apiFetch("/api/v1/user/me", { method: "PATCH", body: JSON.stringify({ name: trimmed }) }, token);
    } catch {
      // non-blocking — name save failure shouldn't block onboarding
    }
    setPhase("welcome");
  };

  const handleSaveKey = async () => {
    if (!apiKey.trim()) {
      toast.error("Please enter an API key");
      return;
    }
    setSaving(true);
    try {
      const payload: Record<string, string> = { llm_api_key: apiKey };
      if (provider !== "auto") payload.llm_provider = provider;
      await apiFetch("/api/v1/settings", { method: "PUT", body: JSON.stringify(payload) }, token);

      // Start onboarding chat
      setSending(true);
      const res = await apiFetch<{ message: string; done: boolean; turn: number }>(
        "/api/v1/onboarding/start",
        { method: "POST" },
        token
      );
      setMessages([{ role: "assistant", content: res.message }]);
      setTurn(res.turn);
      setPhase("chat");
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setSaving(false);
      setSending(false);
    }
  };

  const handleSend = async () => {
    if (!input.trim() || sending) return;
    const text = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setSending(true);

    try {
      const res = await apiFetch<{ message: string; done: boolean; goals_created: number; turn: number }>(
        "/api/v1/onboarding/chat",
        { method: "POST", body: JSON.stringify({ message: text }) },
        token
      );
      setMessages((prev) => [...prev, { role: "assistant", content: res.message }]);
      setTurn(res.turn);
      if (res.done) {
        setGoalsCreated(res.goals_created);
        setPhase("done");
      }
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setSending(false);
    }
  };

  return (
    <Sheet open={open} onOpenChange={(v) => !v && handleClose()}>
      <SheetContent side="right" className="flex flex-col sm:max-w-lg overflow-hidden">
        {phase === "intro" && (
          <>
            <SheetHeader>
              <div className="mx-auto mb-1 flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
                <Brain className="h-6 w-6 text-primary" />
              </div>
              <SheetTitle className="text-center text-xl text-primary">StewardMe</SheetTitle>
              <SheetDescription className="text-center">
                Scans the world. Learns your context. Tells you what matters next.
              </SheetDescription>
            </SheetHeader>

            <div className="flex-1 space-y-4 overflow-y-auto px-4 py-2">
              {introSections.map(({ icon: Icon, title, description }) => (
                <div key={title} className="flex gap-3">
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-muted">
                    <Icon className="h-4 w-4 text-muted-foreground" />
                  </div>
                  <div>
                    <p className="text-sm font-medium">{title}</p>
                    <p className="text-xs text-muted-foreground leading-relaxed">{description}</p>
                  </div>
                </div>
              ))}

              <div className="rounded-lg border bg-muted/50 p-3 text-xs text-muted-foreground leading-relaxed">
                <span className="font-medium text-foreground">How it connects:</span>{" "}
                Journal and goals shape what matters. Radar watches the world. Research helps when a topic needs a deeper dive.
              </div>
            </div>

            <SheetFooter>
              <Button onClick={() => setPhase("name")} className="w-full">
                Continue
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </SheetFooter>
          </>
        )}

        {phase === "name" && (
          <>
            <SheetHeader>
              <div className="mx-auto mb-1 flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
                <Brain className="h-6 w-6 text-primary" />
              </div>
              <SheetTitle className="text-center text-xl">What&apos;s your name?</SheetTitle>
              <SheetDescription className="text-center">
                Your steward will use this to personalise your experience
              </SheetDescription>
            </SheetHeader>

            <div className="flex-1 flex items-center px-4">
              <div className="w-full space-y-1.5">
                <Label htmlFor="user-name">Name</Label>
                <Input
                  id="user-name"
                  placeholder="Alex"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleSaveName()}
                  autoFocus
                />
              </div>
            </div>

            <SheetFooter>
              <Button onClick={handleSaveName} className="w-full">
                Continue
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </SheetFooter>
          </>
        )}

        {phase === "welcome" && (
          <>
            <SheetHeader>
              <div className="mx-auto mb-1 flex h-12 w-12 items-center justify-center rounded-full bg-primary/10">
                <Brain className="h-6 w-6 text-primary" />
              </div>
              <SheetTitle className="text-center text-xl"><span className="text-primary">StewardMe</span></SheetTitle>
              <SheetDescription className="text-center">
                Let&apos;s set up your steward
              </SheetDescription>
            </SheetHeader>

            <div className="space-y-6 px-4 flex-1 overflow-y-auto">
              <div className="space-y-3">
                {features.map(({ icon: Icon, text }) => (
                  <div key={text} className="flex items-center gap-3 text-sm">
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-muted">
                      <Icon className="h-4 w-4 text-muted-foreground" />
                    </div>
                    <span>{text}</span>
                  </div>
                ))}
              </div>

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

            <SheetFooter className="flex-col gap-2">
              <Button onClick={handleSaveKey} disabled={saving} className="w-full">
                {saving ? "Setting up..." : "Get Started"}
              </Button>
              <button
                onClick={() => {
                  // Skip key — start onboarding chat on shared key
                  (async () => {
                    setSending(true);
                    try {
                      const res = await apiFetch<{ message: string; done: boolean; turn: number }>(
                        "/api/v1/onboarding/start",
                        { method: "POST" },
                        token
                      );
                      setMessages([{ role: "assistant", content: res.message }]);
                      setTurn(res.turn);
                      setPhase("chat");
                    } catch (e) {
                      toast.error((e as Error).message);
                    } finally {
                      setSending(false);
                    }
                  })();
                }}
                className="w-full text-center text-xs text-muted-foreground hover:text-foreground"
              >
                Skip &mdash; use lite mode
              </button>
              <div className="rounded-lg border border-amber-200 bg-amber-50 dark:border-amber-900 dark:bg-amber-950/30 p-3 text-xs text-muted-foreground space-y-1">
                <p className="font-medium text-foreground">Lite mode</p>
                <p>Haiku model &middot; 30 queries/day &middot; No deep research</p>
                <p>Add your own key anytime in Settings for the full experience.</p>
              </div>
            </SheetFooter>
          </>
        )}

        {phase === "chat" && (
          <>
            <SheetHeader>
              <SheetTitle className="text-base">Let&apos;s set up your profile</SheetTitle>
              <SheetDescription>
                Answer a few questions so we can personalize your experience
              </SheetDescription>
            </SheetHeader>

            <div className="px-4 pt-2">
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

            <div ref={scrollRef} className="flex-1 space-y-3 overflow-y-auto px-4 py-2">
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

            <div className="flex gap-2 px-4 pb-2">
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
              <Button size="icon" onClick={handleSend} disabled={sending || !input.trim()}>
                <Send className="h-4 w-4" />
              </Button>
            </div>
          </>
        )}

        {phase === "done" && (
          <>
            <SheetHeader>
              <div className="mx-auto mb-1 flex h-12 w-12 items-center justify-center rounded-full bg-green-100 dark:bg-green-900/30">
                <Sparkles className="h-6 w-6 text-green-600 dark:text-green-400" />
              </div>
              <SheetTitle className="text-center text-xl">You&apos;re all set!</SheetTitle>
              <SheetDescription className="text-center">
                Profile created{goalsCreated > 0 ? ` and ${goalsCreated} goal${goalsCreated > 1 ? "s" : ""} set up` : ""} — your steward is ready.
              </SheetDescription>
            </SheetHeader>

            <div className="flex-1" />

            <SheetFooter>
              <Button onClick={() => handleClose(true)} className="w-full">
                Go to Dashboard
              </Button>
            </SheetFooter>
          </>
        )}
      </SheetContent>
    </Sheet>
  );
}
