"use client";

import { useRef, useEffect, useState, useCallback } from "react";
import Link from "next/link";
import { toast } from "sonner";
import { ChatAttachmentBadges, ChatPdfAttachmentPicker } from "@/components/ChatPdfAttachments";
import { MessageRenderer } from "@/components/MessageRenderer";
import { ExternalLink, Send, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useChatPdfAttachments } from "@/hooks/useChatPdfAttachments";
import { Textarea } from "@/components/ui/textarea";
import { apiFetchSSE } from "@/lib/api";
import { TOOL_LABELS } from "@/lib/constants";
import type { ChatMessage } from "@/types/chat";

export function BriefInlineChat({
  token,
  initialQuestion,
  onDismiss,
}: {
  token: string;
  initialQuestion: string;
  onDismiss: () => void;
}) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    { role: "user", content: initialQuestion },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [toolStatus, setToolStatus] = useState<string | null>(null);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const sentInitial = useRef(false);
  const { attachments, addFiles, removeAttachment, uploadPending, uploading } =
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

  // Fire initial question on mount
  useEffect(() => {
    if (sentInitial.current) return;
    sentInitial.current = true;
    sendMessage(initialQuestion, null);
  }, [initialQuestion, sendMessage]);

  // Auto-scroll on new messages
  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
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
    <div className="mx-auto max-w-2xl rounded-lg border bg-card">
      {/* Header */}
      <div className="flex items-center justify-between border-b px-3 py-2">
        <span className="text-xs font-medium text-muted-foreground">Conversation</span>
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
            onClick={onDismiss}
          >
            <X className="h-3.5 w-3.5" />
          </Button>
        </div>
      </div>

      {/* Messages */}
      <div ref={scrollRef} className="max-h-96 space-y-3 overflow-y-auto px-4 py-3">
        {messages.map((msg, i) => (
          <div
            key={i}
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
    </div>
  );
}
