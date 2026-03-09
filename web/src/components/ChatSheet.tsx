"use client";

import { useRef, useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { toast } from "sonner";
import { ChatAttachmentBadges, ChatPdfAttachmentPicker } from "@/components/ChatPdfAttachments";
import { MessageRenderer } from "@/components/MessageRenderer";
import { ExternalLink, Send, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  Sheet,
  SheetContent,
  SheetTitle,
} from "@/components/ui/sheet";
import { useChatPdfAttachments } from "@/hooks/useChatPdfAttachments";
import { apiFetchSSE } from "@/lib/api";
import { TOOL_LABELS } from "@/lib/constants";
import { useLiteMode } from "@/hooks/useLiteMode";
import type { ChatMessage } from "@/types/chat";

export function ChatSheet({
  token,
  open,
  initialQuestion,
  onOpenChange,
}: {
  token: string;
  open: boolean;
  initialQuestion: string | null;
  onOpenChange: (open: boolean) => void;
}) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [toolStatus, setToolStatus] = useState<string | null>(null);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const lastFiredQuestion = useRef<string | null>(null);
  const liteMode = useLiteMode();
  const { attachments, addFiles, removeAttachment, uploadPending, uploading, clearAttachments } =
    useChatPdfAttachments(token);

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

  // Reset + fire when initialQuestion changes while open
  useEffect(() => {
    if (!open || !initialQuestion) return;
    if (lastFiredQuestion.current === initialQuestion) return;
    lastFiredQuestion.current = initialQuestion;
    setMessages([{ role: "user", content: initialQuestion }]);
    setConversationId(null);
    setInput("");
    clearAttachments();
    sendMessage(initialQuestion, null);
  }, [open, initialQuestion, sendMessage, clearAttachments]);

  // Clear tracking on close
  useEffect(() => {
    if (!open) {
      lastFiredQuestion.current = null;
    }
  }, [open]);

  // Auto-scroll
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
  }, [input, loading, conversationId, sendMessage, uploadPending, attachments.length]);

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent
        side="right"
        showCloseButton={false}
        className="flex flex-col w-full sm:max-w-md p-0 gap-0"
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b px-3 py-2">
          <SheetTitle className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
            Conversation
            {liteMode && (
              <span className="rounded bg-amber-100 px-1.5 py-0.5 text-[10px] font-medium text-amber-700 dark:bg-amber-900/50 dark:text-amber-300">
                lite
              </span>
            )}
          </SheetTitle>
          <div className="flex items-center gap-1">
            {conversationId && (
              <Button variant="ghost" size="sm" className="h-7 text-xs gap-1" asChild>
                <Link href={`/advisor?conv=${conversationId}`}>
                  Open full chat <ExternalLink className="h-3 w-3" />
                </Link>
              </Button>
            )}
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7"
              onClick={() => onOpenChange(false)}
            >
              <X className="h-3.5 w-3.5" />
            </Button>
          </div>
        </div>

        {/* Messages */}
        <div ref={scrollRef} className="flex-1 space-y-3 overflow-y-auto px-4 py-3">
          {messages.map((msg, i) => (
            <div
              key={i}
              data-msg
              className={
                msg.role === "user"
                  ? "ml-12 rounded-2xl rounded-br-sm bg-primary/10 px-4 py-2.5"
                  : "mr-4 rounded-2xl rounded-bl-sm px-4 py-2.5"
              }
            >
              {msg.role === "user" && <ChatAttachmentBadges attachments={msg.attachments} />}
              {msg.role === "assistant" ? (
                <MessageRenderer
                  content={msg.content}
                  onAction={(text) => {
                    setInput(text);
                    setTimeout(() => textareaRef.current?.focus(), 100);
                  }}
                />
              ) : (
                <p className="text-sm">{msg.content}</p>
              )}
            </div>
          ))}
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
        </div>

        {/* Input */}
        <div className="border-t px-3 py-2">
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
                rows={1}
                placeholder="Follow up..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSend();
                  }
                }}
                className="flex-1 resize-none"
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
        </div>
      </SheetContent>
    </Sheet>
  );
}
