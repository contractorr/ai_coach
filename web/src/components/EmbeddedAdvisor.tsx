"use client";

import { useRef, useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { toast } from "sonner";
import { ChatAttachmentBadges, ChatPdfAttachmentPicker } from "@/components/ChatPdfAttachments";
import { MessageRenderer } from "@/components/MessageRenderer";
import { Brain, Send, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useChatPdfAttachments } from "@/hooks/useChatPdfAttachments";
import { Textarea } from "@/components/ui/textarea";
import { apiFetch, apiFetchSSE } from "@/lib/api";
import { TOOL_LABELS } from "@/lib/constants";
import type { ChatMessage } from "@/types/chat";

const CONV_KEY = "dashboard_conv_id";

export function EmbeddedAdvisor({
  token,
  prefillQuestion,
  onQuestionConsumed,
}: {
  token: string;
  prefillQuestion?: string;
  onQuestionConsumed?: () => void;
}) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [toolStatus, setToolStatus] = useState<string | null>(null);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { attachments, addFiles, removeAttachment, uploadPending, uploading } =
    useChatPdfAttachments(token);

  // Restore conversation on mount
  useEffect(() => {
    const saved = localStorage.getItem(CONV_KEY);
    if (!saved) return;
    (async () => {
      try {
        const conv = await apiFetch<{
          id: string;
          messages: ChatMessage[];
        }>(`/api/advisor/conversations/${saved}`, {}, token);
        setConversationId(saved);
        // Show last 5 messages
        setMessages(conv.messages.slice(-5));
      } catch {
        localStorage.removeItem(CONV_KEY);
      }
    })();
  }, [token]);

  // Handle prefill from "ask about this" buttons
  useEffect(() => {
    if (prefillQuestion) {
      setInput(prefillQuestion);
      onQuestionConsumed?.();
      // Focus and scroll to textarea
      setTimeout(() => {
        textareaRef.current?.focus();
        textareaRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
      }, 100);
    }
  }, [prefillQuestion, onQuestionConsumed]);

  const prevMsgCount = useRef(messages.length);

  useEffect(() => {
    const prev = prevMsgCount.current;
    prevMsgCount.current = messages.length;

    if (!scrollRef.current) return;

    if (loading || messages.length === 0) {
      scrollRef.current.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
      return;
    }
    if (messages.length > prev) {
      const last = messages[messages.length - 1];
      if (last?.role === "assistant") {
        const cards = scrollRef.current.querySelectorAll("[data-msg]");
        const lastCard = cards[cards.length - 1] as HTMLElement | undefined;
        lastCard?.scrollIntoView({ behavior: "smooth", block: "start" });
        return;
      }
    }
    scrollRef.current.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, loading]);

  const handleSend = useCallback(async () => {
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
          })),
        },
      ]);

      await apiFetchSSE(
        "/api/advisor/ask/stream",
        {
          method: "POST",
          body: JSON.stringify({
            question,
            advice_type: "general",
            conversation_id: conversationId,
            attachment_ids: uploaded.map((item) => item.attachment_id),
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
            localStorage.setItem(CONV_KEY, cid);
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
        }
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
  }, [input, loading, conversationId, token, attachments.length, uploadPending]);

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center justify-between text-base">
          <span className="flex items-center gap-2">
            <Brain className="h-4 w-4" />
            Ask Your Steward
          </span>
          <Button variant="ghost" size="sm" asChild>
            <Link href="/advisor" className="flex items-center gap-1 text-xs">
              All conversations <ArrowRight className="h-3 w-3" />
            </Link>
          </Button>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {/* Messages */}
        <div
          ref={scrollRef}
          className="mb-3 max-h-80 space-y-3 overflow-y-auto"
        >
          {messages.length === 0 && !loading && (
            <div className="flex flex-col items-center py-6 text-center">
              <Brain className="mb-2 h-8 w-8 text-muted-foreground" />
              <p className="text-sm text-muted-foreground">
                Ask a question or click &quot;Ask about this&quot; on any card above.
              </p>
            </div>
          )}
          {messages.map((msg, i) => (
            <div
              key={i}
              data-msg
              className={`rounded-md p-2 text-sm ${
                msg.role === "user"
                  ? "ml-8 bg-primary/5"
                  : "mr-8 bg-muted"
              }`}
            >
              <span className="mb-0.5 block text-xs font-medium text-muted-foreground">
                {msg.role === "user" ? "You" : "Steward"}
              </span>
              {msg.role === "user" && <ChatAttachmentBadges attachments={msg.attachments} />}
              {msg.role === "assistant" ? (
                <MessageRenderer content={msg.content} onAction={(text) => { setInput(text); setTimeout(() => textareaRef.current?.focus(), 100); }} compact />
              ) : (
                <span>{msg.content}</span>
              )}
            </div>
          ))}
          {loading && (
            <div className="mr-8 rounded-md bg-muted p-2 text-sm">
              <div className="flex items-center gap-2 text-muted-foreground">
                <div className="flex gap-1">
                  <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-muted-foreground [animation-delay:0ms]" />
                  <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-muted-foreground [animation-delay:150ms]" />
                  <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-muted-foreground [animation-delay:300ms]" />
                </div>
                {toolStatus || "Thinking..."}
              </div>
            </div>
          )}
        </div>

        {/* Input */}
        <div className="space-y-3">
          <ChatPdfAttachmentPicker
            attachments={attachments}
            disabled={loading || uploading}
            onAddFiles={addFiles}
            onRemove={removeAttachment}
          />
          <div className="flex gap-2">
            <Textarea
              ref={textareaRef}
              rows={2}
              placeholder="Ask a question..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              className="flex-1"
            />
            <Button
              onClick={handleSend}
              disabled={loading || uploading || !input.trim()}
              className="self-end"
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
