"use client";

import { useRef, useEffect, useState, useCallback } from "react";
import { useSearchParams } from "next/navigation";
import { toast } from "sonner";
import { MessageRenderer } from "@/components/MessageRenderer";
import { Brain, Send, Plus, MessageSquare, Trash2 } from "lucide-react";
import { useToken } from "@/hooks/useToken";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { apiFetch, apiFetchSSE } from "@/lib/api";
import { TOOL_LABELS } from "@/lib/constants";

interface Message {
  role: "user" | "assistant";
  content: string;
  advice_type?: string;
}

interface Conversation {
  id: string;
  title: string;
  updated_at: string;
  message_count: number;
}

const CONV_KEY = "advisor_conversation_id";

export default function AdvisorPage() {
  const token = useToken();
  const searchParams = useSearchParams();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [adviceType, setAdviceType] = useState("general");
  const [loading, setLoading] = useState(false);
  const [toolStatus, setToolStatus] = useState<string | null>(null);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const scrollRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const loadConversations = useCallback(async () => {
    if (!token) return;
    try {
      const list = await apiFetch<Conversation[]>(
        "/api/advisor/conversations",
        {},
        token
      );
      setConversations(list);
    } catch {
      // silent
    }
  }, [token]);

  const loadConversation = useCallback(
    async (id: string) => {
      if (!token) return;
      try {
        const conv = await apiFetch<{
          id: string;
          title: string;
          messages: Message[];
        }>(`/api/advisor/conversations/${id}`, {}, token);
        setMessages(conv.messages);
        setConversationId(id);
        localStorage.setItem(CONV_KEY, id);
      } catch {
        // conversation may have been deleted
        localStorage.removeItem(CONV_KEY);
        setConversationId(null);
        setMessages([]);
      }
    },
    [token]
  );

  // On mount: load conversation list + restore current conversation.
  // Validate saved ID against list to avoid 404 on stale IDs.
  useEffect(() => {
    if (!token) return;
    (async () => {
      let list: Conversation[] = [];
      try {
        list = await apiFetch<Conversation[]>("/api/advisor/conversations", {}, token);
        setConversations(list);
      } catch {
        // silent
      }
      const convParam = searchParams.get("conv");
      const saved = convParam || localStorage.getItem(CONV_KEY);
      if (saved) {
        const exists = list.some((c) => c.id === saved);
        if (exists) {
          loadConversation(saved);
        } else {
          // Stale ID — clean up silently instead of hitting 404
          localStorage.removeItem(CONV_KEY);
        }
      }
    })();
  }, [token, searchParams, loadConversation]);

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages, loading]);

  const handleNewChat = () => {
    setConversationId(null);
    setMessages([]);
    localStorage.removeItem(CONV_KEY);
  };

  const handleDeleteConversation = async (id: string) => {
    if (!token) return;
    try {
      await apiFetch(`/api/advisor/conversations/${id}`, { method: "DELETE" }, token);
      setConversations((prev) => prev.filter((c) => c.id !== id));
      if (conversationId === id) {
        handleNewChat();
      }
    } catch (e) {
      toast.error((e as Error).message);
    }
  };

  const handleSend = async () => {
    if (!token || !input.trim()) return;
    const question = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: question }]);
    setLoading(true);
    setToolStatus(null);

    try {
      await apiFetchSSE(
        "/api/advisor/ask/stream",
        {
          method: "POST",
          body: JSON.stringify({
            question,
            advice_type: adviceType,
            conversation_id: conversationId,
          }),
        },
        token,
        (event) => {
          const type = event.type as string;
          if (type === "tool_start") {
            const tool = event.tool as string;
            setToolStatus(TOOL_LABELS[tool] || `Running ${tool}`);
          } else if (type === "tool_done") {
            setToolStatus(null);
          } else if (type === "answer") {
            const cid = event.conversation_id as string;
            setConversationId(cid);
            localStorage.setItem(CONV_KEY, cid);
            setMessages((prev) => [
              ...prev,
              {
                role: "assistant",
                content: event.content as string,
                advice_type: event.advice_type as string,
              },
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
      loadConversations();
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
  };

  return (
    <div className="flex h-full gap-4 p-4 md:p-6">
      {/* Conversation sidebar */}
      <div className="hidden w-64 flex-col border-r pr-4 md:flex">
        <Button
          variant="outline"
          className="mb-3 w-full justify-start gap-2"
          onClick={handleNewChat}
        >
          <Plus className="h-4 w-4" /> New Chat
        </Button>
        <div className="flex-1 space-y-1 overflow-y-auto">
          {conversations.map((conv) => (
            <div
              key={conv.id}
              className={`group flex cursor-pointer items-center gap-2 rounded-md px-2 py-1.5 text-sm hover:bg-muted ${
                conversationId === conv.id ? "bg-muted font-medium" : ""
              }`}
              onClick={() => loadConversation(conv.id)}
            >
              <MessageSquare className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
              <span className="flex-1 truncate" title={conv.title}>{conv.title}</span>
              <button
                className="hidden shrink-0 text-muted-foreground hover:text-destructive group-hover:block"
                onClick={(e) => {
                  e.stopPropagation();
                  handleDeleteConversation(conv.id);
                }}
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Main chat area */}
      <div className="flex flex-1 flex-col">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-semibold">Steward</h1>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              className="md:hidden"
              onClick={handleNewChat}
            >
              <Plus className="h-4 w-4" />
            </Button>
            <Select value={adviceType} onValueChange={setAdviceType}>
              <SelectTrigger className="w-40">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="general">General</SelectItem>
                <SelectItem value="career">Career</SelectItem>
                <SelectItem value="goals">Goals</SelectItem>
                <SelectItem value="opportunities">Opportunities</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Chat messages */}
        <div ref={scrollRef} className="mt-4 flex-1 space-y-4 overflow-y-auto">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-muted">
                <Brain className="h-7 w-7 text-muted-foreground" />
              </div>
              <h3 className="text-lg font-medium">What&apos;s on your mind?</h3>
              <p className="mt-1 max-w-md text-sm text-muted-foreground">
                Ask about a decision, a career move, a goal you&apos;re stuck on,
                or what to focus on next. I&apos;ll draw on your journal and radar.
              </p>
            </div>
          )}
          {messages.map((msg, i) => (
            <Card
              key={i}
              className={
                msg.role === "user" ? "ml-12 bg-primary/5" : "mr-12"
              }
            >
              <CardHeader className="pb-2">
                <CardTitle className="text-xs text-muted-foreground">
                  {msg.role === "user" ? "You" : "Steward"}
                </CardTitle>
              </CardHeader>
              <CardContent>
                {msg.role === "assistant" ? (
                  <MessageRenderer content={msg.content} onAction={(text) => { setInput(text); setTimeout(() => textareaRef.current?.focus(), 100); }} />
                ) : (
                  <div className="text-sm">{msg.content}</div>
                )}
              </CardContent>
            </Card>
          ))}
          {loading && (
            <Card className="mr-12">
              <CardContent className="py-4">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <div className="flex gap-1">
                    <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-muted-foreground [animation-delay:0ms]" />
                    <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-muted-foreground [animation-delay:150ms]" />
                    <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-muted-foreground [animation-delay:300ms]" />
                  </div>
                  {toolStatus || "Thinking..."}
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Input */}
        <div className="mt-4 flex gap-2 border-t pt-4">
          <Textarea
            ref={textareaRef}
            rows={2}
            placeholder="Ask me anything..."
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
          <Button onClick={handleSend} disabled={loading || !input.trim()}>
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
