"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import Link from "next/link";
import { toast } from "sonner";
import { ChatAttachmentBadges, ChatPdfAttachmentPicker } from "@/components/ChatPdfAttachments";
import { useToken } from "@/hooks/useToken";
import { useChatPdfAttachments } from "@/hooks/useChatPdfAttachments";
import { MessageRenderer } from "@/components/MessageRenderer";
import { Check, ExternalLink, PenLine, Send } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { apiFetch, apiFetchSSE } from "@/lib/api";
import { TOOL_LABELS } from "@/lib/constants";
import type { ChatMessage } from "@/types/chat";
import type { GreetingResponse } from "@/types/greeting";

type InputMode = "ask" | "capture";

export default function HomePage() {
  const token = useToken();
  const [greeting, setGreeting] = useState<string | null>(null);
  const [greetingLoaded, setGreetingLoaded] = useState(false);
  const [userName, setUserName] = useState<string | null>(null);

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [mode, setMode] = useState<InputMode>("ask");
  const [loading, setLoading] = useState(false);
  const [toolStatus, setToolStatus] = useState<string | null>(null);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [captured, setCaptured] = useState(false);
  const { attachments, addFiles, removeAttachment, uploadPending, uploading, clearAttachments } =
    useChatPdfAttachments(token);

  const scrollRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const retried = useRef(false);

  // Fetch greeting + user on mount
  useEffect(() => {
    if (!token) return;
    let cancelled = false;

    apiFetch<GreetingResponse>("/api/greeting", {}, token)
      .then((data) => {
        if (cancelled) return;
        setGreeting(data.text);
        // If stale, retry once after 5s
        if (data.stale && !retried.current) {
          retried.current = true;
          setTimeout(() => {
            apiFetch<GreetingResponse>("/api/greeting", {}, token)
              .then((fresh) => {
                if (!cancelled && !fresh.stale) setGreeting(fresh.text);
              })
              .catch(() => {});
          }, 5000);
        }
      })
      .catch(() => {})
      .finally(() => {
        if (!cancelled) setGreetingLoaded(true);
      });

    apiFetch<{ name: string | null }>("/api/user/me", {}, token)
      .then((user) => {
        if (!cancelled && user.name) setUserName(user.name);
      })
      .catch(() => {});

    return () => {
      cancelled = true;
    };
  }, [token]);

  // Auto-scroll
  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages, loading]);

  useEffect(() => {
    if (mode === "capture") clearAttachments();
  }, [mode, clearAttachments]);

  const sendMessage = useCallback(
    async (question: string, convId: string | null, attachmentIds: string[] = []) => {
      setLoading(true);
      setToolStatus(null);

      try {
        await apiFetchSSE(
          "/api/advisor/ask/stream",
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
              setToolStatus(
                TOOL_LABELS[event.tool as string] || `Running ${event.tool}`,
              );
            } else if (type === "tool_done") {
              setToolStatus(null);
            } else if (type === "answer") {
              const cid = event.conversation_id as string;
              setConversationId(cid);
              setMessages((prev) => [
                ...prev,
                { role: "assistant", content: event.content as string },
              ]);
            } else if (type === "error") {
              toast.error(event.detail as string);
              setMessages((prev) => [
                ...prev,
                { role: "assistant", content: "Error: " + (event.detail as string) },
              ]);
            }
          },
        );
      } catch (e) {
        toast.error((e as Error).message);
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: "Error: " + (e as Error).message },
        ]);
      } finally {
        setLoading(false);
        setToolStatus(null);
      }
    },
    [token],
  );

  const handleAsk = useCallback(async () => {
    if (!input.trim() || loading) return;
    const question = input.trim();
    setInput("");
    setLoading(true);
    setToolStatus(attachments.length ? "Uploading PDFs..." : null);
    try {
      const uploaded = await uploadPending();
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
      clearAttachments();
      sendMessage(
        question,
        conversationId,
        uploaded.map((item) => item.attachment_id),
      );
    } catch (e) {
      toast.error((e as Error).message);
      setLoading(false);
      setToolStatus(null);
    }
  }, [input, loading, conversationId, sendMessage, uploadPending, attachments.length, clearAttachments]);

  const handleCapture = useCallback(async () => {
    if (!input.trim() || !token) return;
    const text = input.trim();
    setInput("");
    try {
      await apiFetch(
        "/api/journal/quick",
        { method: "POST", body: JSON.stringify({ content: text }) },
        token,
      );
      setCaptured(true);
      toast.success("Captured");
      setTimeout(() => setCaptured(false), 2000);
    } catch (e) {
      toast.error((e as Error).message);
    }
  }, [input, token]);

  const handleSubmit = useCallback(() => {
    if (mode === "ask") handleAsk();
    else handleCapture();
  }, [mode, handleAsk, handleCapture]);

  if (!token || !greetingLoaded) {
    return (
      <div className="flex h-full flex-col">
        <div className="mx-auto w-full max-w-2xl flex-1 animate-pulse space-y-4 px-4 py-8">
          <div className="h-16 rounded-2xl bg-muted" />
          <div className="space-y-2">
            <div className="h-3 w-5/6 rounded bg-muted" />
            <div className="h-3 w-2/3 rounded bg-muted" />
          </div>
        </div>
      </div>
    );
  }

  const hasConversation = messages.length > 0;

  return (
    <div className="flex h-full flex-col">
      {/* Messages area */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-4">
        <div className="mx-auto max-w-2xl space-y-3">
          {/* Greeting as first assistant message */}
          {greeting && (
            <div className="mr-4 rounded-2xl rounded-bl-sm px-4 py-2.5">
              <p className="text-sm">
                {userName && (
                  <span className="font-medium">{userName}, </span>
                )}
                {greeting}
              </p>
            </div>
          )}

          {/* Conversation messages */}
          {messages.map((msg, i) => (
            <div
              key={i}
              className={
                msg.role === "user"
                  ? "ml-12 rounded-2xl rounded-br-sm bg-primary/10 px-4 py-2.5"
                  : "mr-4 rounded-2xl rounded-bl-sm px-4 py-2.5"
              }
            >
              {msg.role === "assistant" ? (
                <MessageRenderer
                  content={msg.content}
                  onAction={(text) => {
                    setInput(text);
                    setTimeout(() => textareaRef.current?.focus(), 100);
                  }}
                />
              ) : (
                <div>
                  <ChatAttachmentBadges attachments={msg.attachments} token={token} />
                  <p className="text-sm">{msg.content}</p>
                </div>
              )}
            </div>
          ))}

          {/* Loading indicator */}
          {loading && (
            <div className="mr-4 rounded-2xl rounded-bl-sm px-4 py-3">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <div className="flex gap-1">
                  <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-muted-foreground [animation-delay:0ms]" />
                  <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-muted-foreground [animation-delay:150ms]" />
                  <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-muted-foreground [animation-delay:300ms]" />
                </div>
                {toolStatus || "Thinking..."}
              </div>
            </div>
          )}

          {/* Empty state hint (no messages yet) */}
          {!hasConversation && !loading && (
            <div className="pt-4 text-center">
              <p className="text-sm text-muted-foreground">
                Ask me anything — a decision, a priority, a goal, or what to do next.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Conversation link */}
      {conversationId && (
        <div className="flex justify-center border-t px-4 py-1">
          <Button variant="ghost" size="sm" className="h-7 text-xs gap-1" asChild>
            <Link href={`/advisor?conv=${conversationId}`}>
              Open in Conversations <ExternalLink className="h-3 w-3" />
            </Link>
          </Button>
        </div>
      )}

      {/* Input area */}
      <div className="border-t px-4 py-3">
        <div className="mx-auto max-w-2xl">
          {mode === "ask" && (
            <ChatPdfAttachmentPicker
              attachments={attachments}
              disabled={loading || uploading}
              onAddFiles={addFiles}
              onRemove={removeAttachment}
            />
          )}
          <div className={`flex gap-2 ${mode === "ask" ? "mt-3" : ""}`}>
            <Textarea
              ref={textareaRef}
              rows={1}
              placeholder={mode === "ask" ? "Ask anything..." : "Quick thought..."}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSubmit();
                }
              }}
              className="flex-1 resize-none"
            />
            <div className="flex flex-col gap-1 self-end">
              {captured ? (
                <Button size="icon" variant="ghost" disabled className="h-9 w-9">
                  <Check className="h-4 w-4 text-green-600" />
                </Button>
              ) : (
                <Button
                  size="icon"
                  onClick={handleSubmit}
                  disabled={!input.trim() || loading || uploading}
                  className="h-9 w-9"
                >
                  {mode === "ask" ? (
                    <Send className="h-4 w-4" />
                  ) : (
                    <PenLine className="h-4 w-4" />
                  )}
                </Button>
              )}
              <button
                onClick={() => setMode((m) => (m === "ask" ? "capture" : "ask"))}
                className="text-[10px] text-muted-foreground hover:text-foreground transition-colors"
              >
                {mode === "ask" ? "capture" : "ask"}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
