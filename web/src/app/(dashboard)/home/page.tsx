"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import { Check, ExternalLink, PenLine, Send, Sparkles } from "lucide-react";
import { toast } from "sonner";

import { ChatAttachmentBadges, ChatPdfAttachmentPicker } from "@/components/ChatPdfAttachments";
import { LearningSnapshotCard } from "@/components/home/LearningSnapshotCard";
import { ReturnBriefCard } from "@/components/home/ReturnBriefCard";
import { WhyNowChip } from "@/components/shared/WhyNowChip";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { useChatPdfAttachments } from "@/hooks/useChatPdfAttachments";
import { useHomeStats } from "@/hooks/useHomeStats";
import { useToken } from "@/hooks/useToken";
import { apiFetch, apiFetchSSE } from "@/lib/api";
import { logEngagement } from "@/lib/engagement";
import { TOOL_LABELS } from "@/lib/constants";
import type { ChatMessage } from "@/types/chat";
import type { GreetingResponse, ReturnBrief } from "@/types/greeting";
import type { SuggestionItem } from "@/types/suggestions";
import { MessageRenderer } from "@/components/MessageRenderer";

type InputMode = "ask" | "capture";

const MODE_COPY: Record<
  InputMode,
  { title: string; helper: string; placeholder: string }
> = {
  capture: {
    title: "Capture",
    helper: "Save a thought, reflection, or rough note to your journal before deciding what to do with it.",
    placeholder: "Write a note worth keeping",
  },
  ask: {
    title: "Ask for guidance",
    helper: "Use this when you want grounded help with a decision, a priority, or the draft in front of you.",
    placeholder: "Ask a question or paste context",
  },
};

interface CapturedNote {
  path: string;
  text: string;
  title: string;
}

const QUESTION_PREFIXES = [
  "who",
  "what",
  "when",
  "where",
  "why",
  "how",
  "should",
  "can",
  "could",
  "would",
  "will",
  "do",
  "does",
  "did",
  "is",
  "are",
  "am",
];

function looksLikeQuestion(value: string) {
  const trimmed = value.trim();
  if (!trimmed) return false;
  if (trimmed.endsWith("?")) return true;
  const firstWord = trimmed.split(/\s+/, 1)[0]?.toLowerCase() ?? "";
  return QUESTION_PREFIXES.includes(firstWord);
}

function timeGreeting(): string {
  const h = new Date().getHours();
  if (h < 12) return "Good morning";
  if (h < 18) return "Good afternoon";
  return "Good evening";
}

const SUGGESTION_ACCENT: Record<string, string> = {
  company_movement: "border-l-sky-400",
  hiring_signal: "border-l-sky-400",
  regulatory_alert: "border-l-rose-400",
  dossier_escalation: "border-l-rose-400",
  assumption_alert: "border-l-rose-400",
  goal_stale: "border-l-amber-400",
  goal_at_risk: "border-l-amber-400",
};

function sourceWorkspace(item: SuggestionItem) {
  if (["company_movement", "hiring_signal", "regulatory_alert", "dossier_escalation"].includes(item.kind)) {
    return "/radar";
  }
  if (item.kind === "assumption_alert") {
    return "/settings#watchlist";
  }
  return "/goals";
}

const HOME_LINKS = [
  { href: "/goals", label: "Goals" },
  { href: "/research", label: "Research" },
  { href: "/learn", label: "Guide Library" },
  { href: "/journal", label: "Journal" },
];

export default function HomePage() {
  const token = useToken();
  const stats = useHomeStats();
  const [greeting, setGreeting] = useState<string | null>(null);
  const [returnBrief, setReturnBrief] = useState<ReturnBrief | null>(null);
  const [dismissedReturnBriefAt, setDismissedReturnBriefAt] = useState<string | null>(null);
  const [greetingLoaded, setGreetingLoaded] = useState(false);
  const [userName, setUserName] = useState<string | null>(null);
  const [nextSteps, setNextSteps] = useState<SuggestionItem[]>([]);

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [mode, setMode] = useState<InputMode>("capture");
  const [modeLocked, setModeLocked] = useState(false);
  const [loading, setLoading] = useState(false);
  const [toolStatus, setToolStatus] = useState<string | null>(null);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [captured, setCaptured] = useState(false);
  const [lastCapturedNote, setLastCapturedNote] = useState<CapturedNote | null>(null);
  const { attachments, addFiles, removeAttachment, uploadPending, uploading, clearAttachments } =
    useChatPdfAttachments(token);

  const scrollRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const retried = useRef(false);
  const lastReturnBriefAt = useRef<string | null>(null);

  const applyGreetingResponse = useCallback((data: GreetingResponse) => {
    setGreeting(data.text);

    const nextReturnBrief = data.return_brief ?? null;
    setReturnBrief(nextReturnBrief);

    const nextGeneratedAt = nextReturnBrief?.generated_at ?? null;
    if (nextGeneratedAt && nextGeneratedAt !== lastReturnBriefAt.current) {
      setDismissedReturnBriefAt(null);
    }
    lastReturnBriefAt.current = nextGeneratedAt;
  }, []);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;

    apiFetch<GreetingResponse>("/api/v1/greeting", {}, token)
      .then((data) => {
        if (cancelled) return;
        applyGreetingResponse(data);
        if (data.stale && !retried.current) {
          retried.current = true;
          setTimeout(() => {
            apiFetch<GreetingResponse>("/api/v1/greeting", {}, token)
              .then((fresh) => {
                if (!cancelled && !fresh.stale) applyGreetingResponse(fresh);
              })
              .catch(() => {});
          }, 5000);
        }
      })
      .catch(() => {})
      .finally(() => {
        if (!cancelled) setGreetingLoaded(true);
      });

    apiFetch<{ name: string | null }>("/api/v1/user/me", {}, token)
      .then((user) => {
        if (!cancelled && user.name) setUserName(user.name);
      })
      .catch(() => {});

    apiFetch<SuggestionItem[]>("/api/v1/suggestions?limit=3", {}, token)
      .then((items) => {
        if (!cancelled) setNextSteps(items.slice(0, 3));
      })
      .catch(() => {});

    return () => {
      cancelled = true;
    };
  }, [token, applyGreetingResponse]);

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages, loading]);

  useEffect(() => {
    if (mode === "capture") clearAttachments();
  }, [mode, clearAttachments]);

  useEffect(() => {
    const trimmed = input.trim();
    if (!trimmed) {
      if (modeLocked) setModeLocked(false);
      if (mode !== "capture") setMode("capture");
      return;
    }
    if (modeLocked) return;
    const inferredMode: InputMode = looksLikeQuestion(trimmed) ? "ask" : "capture";
    if (mode !== inferredMode) setMode(inferredMode);
  }, [input, mode, modeLocked]);

  const sendMessage = useCallback(
    async (question: string, convId: string | null, attachmentIds: string[] = []) => {
      setLoading(true);
      setToolStatus(null);

      try {
        await apiFetchSSE(
          "/api/v1/advisor/ask/stream",
          {
            method: "POST",
            body: JSON.stringify({
              question,
              advice_type: "general",
              conversation_id: convId,
              attachment_ids: attachmentIds,
            }),
          },
          token,
          (event) => {
            const type = event.type as string;
            if (type === "tool_start") {
              setToolStatus(TOOL_LABELS[event.tool as string] || `Running ${event.tool}`);
            } else if (type === "tool_done") {
              setToolStatus(null);
            } else if (type === "answer") {
              const cid = event.conversation_id as string;
              setConversationId(cid);
              const prefix = event.council_used ? "Council-assisted answer\n\n" : "";
              setMessages((prev) => [...prev, { role: "assistant", content: prefix + (event.content as string) }]);
            } else if (type === "error") {
              toast.error(event.detail as string);
              setMessages((prev) => [
                ...prev,
                { role: "assistant", content: "Error: " + (event.detail as string) },
              ]);
            }
          }
        );
      } catch (error) {
        toast.error((error as Error).message);
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: "Error: " + (error as Error).message },
        ]);
      } finally {
        setLoading(false);
        setToolStatus(null);
      }
    },
    [token]
  );

  const handleAsk = useCallback(
    async (questionOverride?: string) => {
      const question = (questionOverride ?? input).trim();
      const useComposerState = !questionOverride;
      if (!question || loading) return;

      if (useComposerState) {
        setInput("");
      }
      setLoading(true);
      setToolStatus(useComposerState && attachments.length ? "Uploading PDFs..." : null);

      try {
        const uploaded = useComposerState ? await uploadPending() : [];
        setMessages((prev) => [
          ...prev,
          {
            role: "user",
            content: question,
            attachments: uploaded.map((item) => ({
              library_item_id: item.attachment_id,
              file_name: item.file_name,
              mime_type: item.mime_type,
              index_status: item.index_status,
              visibility_state: item.visibility_state,
              warning: item.warning,
            })),
          },
        ]);
        if (useComposerState) {
          clearAttachments();
        }
        await sendMessage(
          question,
          conversationId,
          uploaded.map((item) => item.attachment_id)
        );
      } catch (error) {
        toast.error((error as Error).message);
        setLoading(false);
        setToolStatus(null);
      }
    },
    [attachments.length, clearAttachments, conversationId, input, loading, sendMessage, uploadPending]
  );

  const handleCapture = useCallback(async () => {
    if (!input.trim() || !token) return;
    const text = input.trim();
    setInput("");
    try {
      const entry = await apiFetch<{ path: string; title: string }>(
        "/api/v1/journal/quick",
        { method: "POST", body: JSON.stringify({ content: text }) },
        token
      );
      setCaptured(true);
      setLastCapturedNote({ path: entry.path, text, title: entry.title });
      toast.success("Saved to journal");
      setTimeout(() => setCaptured(false), 2000);
    } catch (error) {
      toast.error((error as Error).message);
    }
  }, [input, token]);

  const effectiveMode = mode;

  const handleModeSelect = useCallback((nextMode: InputMode) => {
    setMode(nextMode);
    setModeLocked(true);
  }, []);

  const handleInputChange = useCallback((value: string) => {
    setInput(value);
    if (!value.trim()) {
      setModeLocked(false);
    }
  }, []);

  const handleSubmit = useCallback(() => {
    if (effectiveMode === "ask") {
      void handleAsk();
      return;
    }
    void handleCapture();
  }, [effectiveMode, handleAsk, handleCapture]);

  if (!token || !greetingLoaded) {
    return (
      <div className="flex h-full flex-col">
        <div className="mx-auto w-full max-w-4xl flex-1 animate-pulse space-y-4 px-4 py-8">
          <div className="h-28 rounded-2xl bg-muted" />
          <div className="h-44 rounded-2xl bg-muted" />
          <div className="h-52 rounded-2xl bg-muted" />
        </div>
      </div>
    );
  }

  const hasConversation = messages.length > 0;
  const showReturnBrief = Boolean(returnBrief && returnBrief.generated_at !== dismissedReturnBriefAt);
  const replaceGreeting = Boolean(showReturnBrief && returnBrief && returnBrief.absent_hours >= 24 * 7);
  const composerCopy = MODE_COPY[mode];
  const showLearningCard = stats.loading || Boolean(stats.learningStats) || Boolean(stats.learningToday);
  const modeStatus = modeLocked
    ? `${mode === "ask" ? "Ask" : "Capture"} is locked for this draft.`
    : mode === "ask"
      ? "Question detected — Enter will ask Steward."
      : "Enter will save this draft to Journal.";

  return (
    <div className="flex h-full flex-col">
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-4">
        <div className="mx-auto max-w-4xl space-y-4 pb-8">
          {showReturnBrief && returnBrief ? (
            <ReturnBriefCard
              brief={returnBrief}
              onDismiss={() => setDismissedReturnBriefAt(returnBrief.generated_at)}
            />
          ) : null}

          {/* Hero greeting card */}
          {!replaceGreeting ? (
            <div className="relative animate-in fade-in-0 slide-in-from-bottom-2 duration-400 fill-mode-both">
              <div className="pointer-events-none absolute -inset-4 rounded-3xl bg-primary/8 blur-3xl" />
              <div className="relative rounded-2xl border bg-card/60 p-5 shadow-sm backdrop-blur supports-[backdrop-filter]:bg-card/70 sm:p-6">
                <div className="space-y-4">
                  <div className="space-y-1">
                    <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">
                      {timeGreeting()}{userName ? `, ${userName.split(" ")[0]}` : ""}
                    </h1>
                    {greeting ? (
                      <p className="text-sm leading-relaxed text-muted-foreground">{greeting}</p>
                    ) : null}
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {HOME_LINKS.map((link) => (
                      <Button key={link.href} variant="ghost" size="sm" asChild>
                        <Link href={link.href}>{link.label}</Link>
                      </Button>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          ) : null}

          <Card className="animate-in gap-4 border-primary/10 bg-card/70 py-5 shadow-sm fade-in-0 slide-in-from-bottom-2 duration-400 fill-mode-both delay-100">
            <CardHeader className="space-y-3 px-5 pb-0 sm:px-6">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="space-y-1">
                  <CardTitle className="text-xl">Capture or ask</CardTitle>
                  <CardDescription>
                    Start here with a note, a question, or the draft in front of you.
                  </CardDescription>
                </div>
                <div className="flex items-center gap-1 rounded-full border bg-muted/30 p-1">
                  <button
                    type="button"
                    aria-pressed={mode === "capture"}
                    onClick={() => handleModeSelect("capture")}
                    className={`rounded-full px-2.5 py-1 text-xs transition-colors ${mode === "capture" ? "bg-background text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground"}`}
                  >
                    Capture
                  </button>
                  <button
                    type="button"
                    aria-pressed={mode === "ask"}
                    onClick={() => handleModeSelect("ask")}
                    className={`rounded-full px-2.5 py-1 text-xs transition-colors ${mode === "ask" ? "bg-background text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground"}`}
                  >
                    Ask
                  </button>
                </div>
              </div>

              <div className="flex flex-wrap items-center gap-2">
                <Badge variant="secondary" className="text-[11px]">
                  {modeLocked ? "Manual" : "Auto"}
                </Badge>
                <p className="text-xs text-muted-foreground">
                  {modeLocked
                    ? modeStatus
                    : mode === "ask"
                      ? "Question detected. Enter will ask for guidance."
                      : "Enter will save this draft to Journal."}
                </p>
              </div>

              <p className="text-sm text-muted-foreground">{composerCopy.helper}</p>
            </CardHeader>

            <CardContent className="space-y-3 px-5 sm:px-6">
              {mode === "ask" ? (
                <ChatPdfAttachmentPicker
                  attachments={attachments}
                  disabled={loading || uploading}
                  onAddFiles={addFiles}
                  onRemove={removeAttachment}
                />
              ) : null}

              <div className="flex gap-2">
                <Textarea
                  ref={textareaRef}
                  rows={3}
                  placeholder={composerCopy.placeholder}
                  value={input}
                  onChange={(event) => handleInputChange(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter" && !event.shiftKey) {
                      event.preventDefault();
                      handleSubmit();
                    }
                  }}
                  className="min-h-24 flex-1 resize-none"
                />
                <div className="flex flex-col gap-1 self-end">
                  {captured ? (
                    <Button size="icon" variant="ghost" disabled className="h-10 w-10">
                      <Check className="h-4 w-4 text-green-600" />
                    </Button>
                  ) : (
                    <Button
                      size="icon"
                      onClick={handleSubmit}
                      disabled={!input.trim() || loading || uploading}
                      className="h-10 w-10"
                    >
                      {effectiveMode === "ask" ? <Send className="h-4 w-4" /> : <PenLine className="h-4 w-4" />}
                    </Button>
                  )}
                  <span className="text-center text-[10px] text-muted-foreground">
                    {effectiveMode === "ask" ? "ask" : "save"}
                  </span>
                </div>
              </div>

              <p className="text-xs text-muted-foreground">
                {modeLocked
                  ? "Clear the draft to return to automatic mode detection."
                  : "Home switches between capture and ask automatically while you draft."}
              </p>
            </CardContent>
          </Card>

          {lastCapturedNote ? (
            <Card className="border-primary/20 bg-primary/5 py-4 shadow-none">
              <CardHeader className="px-4 pb-0">
                <CardTitle className="text-base">Saved to journal</CardTitle>
                <CardDescription>
                  {lastCapturedNote.title} is captured. Want help thinking through it next?
                </CardDescription>
              </CardHeader>
              <CardContent className="flex flex-wrap gap-2 px-4">
                <Button size="sm" onClick={() => void handleAsk(lastCapturedNote.text)}>
                  Get advice on this
                </Button>
                <Button size="sm" variant="outline" asChild>
                  <Link href="/journal">Open journal</Link>
                </Button>
              </CardContent>
            </Card>
          ) : null}

          {/* Suggestion cards */}
          {nextSteps.length > 0 ? (
            <Card className="animate-in gap-4 py-4 shadow-sm fade-in-0 slide-in-from-bottom-2 duration-400 fill-mode-both delay-200">
              <CardHeader className="space-y-1 px-4 pb-0">
                <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
                  <Sparkles className="h-4 w-4" />
                  Next up
                </div>
                <CardDescription>Keep the list short. Start with the strongest move.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3 px-4">
                {nextSteps.map((item, index) => (
                  <div
                    key={`${item.kind}-${item.title}-${index}`}
                    className={`rounded-2xl border-l-4 bg-background/80 p-4 ${SUGGESTION_ACCENT[item.kind] ?? "border-l-primary"}`}
                  >
                    <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                      <div className="space-y-2">
                        <Badge variant="secondary" className="text-[11px]">
                          {item.kind.replaceAll("_", " ")}
                        </Badge>
                        <div className="space-y-1">
                          <h2 className="text-base font-medium leading-snug">{item.title}</h2>
                          <p className="text-sm text-muted-foreground">{item.description || item.action}</p>
                        </div>
                        {item.why_now?.length ? (
                          <div className="flex flex-wrap gap-2">
                            {item.why_now.map((chip, chipIndex) => (
                              <WhyNowChip key={`${chip.code}-${chipIndex}`} chip={chip} />
                            ))}
                          </div>
                        ) : null}
                      </div>
                      <Button
                        size="sm"
                        variant="outline"
                        asChild
                        onClick={() => {
                          if (token) logEngagement(token, "acted_on", "suggestion", item.title.slice(0, 200));
                        }}
                      >
                        <Link href={sourceWorkspace(item)}>Open</Link>
                      </Button>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          ) : null}

          {showLearningCard ? (
            <LearningSnapshotCard
              stats={stats.learningStats}
              today={stats.learningToday}
              loading={stats.loading}
            />
          ) : null}

          {hasConversation || loading ? (
            <Card className="py-4 shadow-sm">
              <CardHeader className="px-4 pb-0">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="space-y-1">
                    <CardTitle className="text-base">Current thread</CardTitle>
                    <CardDescription>
                      Stay here for a short exchange. Open full chat only when the thread needs more space.
                    </CardDescription>
                  </div>
                  {conversationId ? (
                    <Button variant="ghost" size="sm" className="h-8 gap-1 text-xs" asChild>
                      <Link href={`/advisor?conv=${conversationId}`}>
                        Open full chat <ExternalLink className="h-3 w-3" />
                      </Link>
                    </Button>
                  ) : null}
                </div>
              </CardHeader>
              <CardContent className="space-y-3 px-4">
                {messages.map((msg, index) => (
                  <div
                    key={`${msg.role}-${index}`}
                    className={
                      msg.role === "user"
                        ? "ml-8 rounded-2xl rounded-br-sm bg-primary/10 px-4 py-2.5"
                        : "mr-2 rounded-2xl rounded-bl-sm bg-muted/30 px-4 py-2.5"
                    }
                  >
                    {msg.role === "assistant" ? (
                      <MessageRenderer
                        content={msg.content}
                        onAction={(text) => {
                          setInput(text);
                          setMode("ask");
                          setModeLocked(true);
                          setTimeout(() => textareaRef.current?.focus(), 100);
                        }}
                      />
                    ) : (
                      <div className="space-y-2">
                        <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                        {msg.attachments?.length ? <ChatAttachmentBadges attachments={msg.attachments} /> : null}
                      </div>
                    )}
                  </div>
                ))}

                {loading ? (
                  <div className="mr-2 rounded-2xl rounded-bl-sm bg-muted/30 px-4 py-2.5 text-sm text-muted-foreground">
                    {toolStatus || "Thinking..."}
                  </div>
                ) : null}
              </CardContent>
            </Card>
          ) : null}

          {!hasConversation && !loading ? (
            <div className="pt-1 text-center text-sm text-muted-foreground">
              Write a note, ask a question, or pick up your next lesson in <Link href="/learn" className="underline underline-offset-4">Guide Library</Link>.
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}
