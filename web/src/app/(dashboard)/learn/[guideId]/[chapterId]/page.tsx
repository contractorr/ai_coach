"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { toast } from "sonner";
import {
  ArrowLeft,
  ArrowRight,
  Check,
  ChevronLeft,
  Clock,
  ClipboardList,
  PenLine,
  X,
} from "lucide-react";
import { useToken } from "@/hooks/useToken";
import { apiFetch } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { CurriculumRenderer } from "@/components/curriculum/CurriculumRenderer";
import { PreReadingCard } from "@/components/curriculum/PreReadingCard";
import { TeachBackCard } from "@/components/curriculum/TeachBackCard";
import { RelatedChaptersCard } from "@/components/curriculum/RelatedChaptersCard";
import type { ChapterDetail, ChapterStatus, ReviewItem } from "@/types/curriculum";

export default function ChapterReaderPage() {
  const token = useToken();
  const params = useParams();
  const router = useRouter();
  const guideId = params.guideId as string;
  const chapterId = params.chapterId as string;
  const fullChapterId = `${guideId}/${chapterId}`;

  const [chapter, setChapter] = useState<ChapterDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [completing, setCompleting] = useState(false);
  const [quiz, setQuiz] = useState<ReviewItem[] | null>(null);
  const [quizLoading, setQuizLoading] = useState(false);
  const [reflectionPrompt, setReflectionPrompt] = useState<string | null>(null);
  const [savingReflection, setSavingReflection] = useState(false);

  // Reading time tracker
  const readingStart = useRef(Date.now());
  const lastSync = useRef(Date.now());

  const syncProgress = useCallback(
    async (status?: ChapterStatus) => {
      if (!token) return;
      const elapsed = Math.round((Date.now() - lastSync.current) / 1000);
      lastSync.current = Date.now();
      try {
        await apiFetch(
          "/api/curriculum/progress",
          {
            method: "POST",
            body: JSON.stringify({
              chapter_id: fullChapterId,
              guide_id: guideId,
              ...(status ? { status } : {}),
              reading_time_seconds: elapsed > 0 ? elapsed : undefined,
            }),
          },
          token
        );
      } catch {
        // silent
      }
    },
    [token, fullChapterId, guideId]
  );

  // Load chapter
  useEffect(() => {
    if (!token || !guideId || !chapterId) return;
    setLoading(true);
    readingStart.current = Date.now();
    lastSync.current = Date.now();
    apiFetch<ChapterDetail>(
      `/api/curriculum/guides/${guideId}/chapters/${chapterId}`,
      {},
      token
    )
      .then((data) => {
        setChapter(data);
        // Auto mark in progress
        if (!data.progress || data.progress.status === "not_started") {
          syncProgress("in_progress");
        }
      })
      .catch((e) => toast.error((e as Error).message))
      .finally(() => setLoading(false));
  }, [token, guideId, chapterId]); // eslint-disable-line react-hooks/exhaustive-deps

  // Periodic reading time sync (30s)
  useEffect(() => {
    const interval = setInterval(() => syncProgress(), 30000);
    return () => {
      clearInterval(interval);
      // Final sync on unmount
      syncProgress();
    };
  }, [syncProgress]);

  const handleComplete = async () => {
    setCompleting(true);
    try {
      const elapsed = Math.round((Date.now() - lastSync.current) / 1000);
      lastSync.current = Date.now();
      const progressResult = await apiFetch<{
        reflection_prompt?: string;
        memory_facts_extracted?: number;
      }>(
        "/api/curriculum/progress",
        {
          method: "POST",
          body: JSON.stringify({
            chapter_id: fullChapterId,
            guide_id: guideId,
            status: "completed",
            reading_time_seconds: elapsed > 0 ? elapsed : undefined,
          }),
        },
        token!
      );
      toast.success("Chapter completed!");
      if (progressResult.reflection_prompt) {
        setReflectionPrompt(progressResult.reflection_prompt);
      }
      // Refresh to get updated status
      const data = await apiFetch<ChapterDetail>(
        `/api/curriculum/guides/${guideId}/chapters/${chapterId}`,
        {},
        token!
      );
      setChapter(data);
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setCompleting(false);
    }
  };

  const handleSaveReflection = async () => {
    if (!token || !reflectionPrompt) return;
    setSavingReflection(true);
    try {
      await apiFetch(
        "/api/journal",
        {
          method: "POST",
          body: JSON.stringify({
            content: reflectionPrompt,
            entry_type: "reflection",
            title: `Chapter Review: ${chapter?.title ?? chapterId}`,
            tags: ["curriculum", guideId],
          }),
        },
        token
      );
      toast.success("Reflection saved");
      setReflectionPrompt(null);
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setSavingReflection(false);
    }
  };

  const handleStartQuiz = async () => {
    if (!token) return;
    setQuizLoading(true);
    try {
      const data = await apiFetch<{ questions: ReviewItem[] }>(
        `/api/curriculum/quiz/${fullChapterId}/generate`,
        { method: "POST" },
        token
      );
      setQuiz(data.questions);
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setQuizLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-4 max-w-3xl mx-auto">
        <div className="h-6 w-48 animate-pulse rounded bg-muted" />
        <div className="h-96 animate-pulse rounded-lg bg-muted" />
      </div>
    );
  }

  if (!chapter) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">Chapter not found</p>
      </div>
    );
  }

  const isCompleted = chapter.progress?.status === "completed";

  return (
    <div className="max-w-3xl mx-auto space-y-4">
      {/* Sticky header */}
      <div className="sticky top-0 z-10 -mx-4 flex items-center justify-between gap-2 border-b bg-background/95 px-4 py-2.5 backdrop-blur supports-[backdrop-filter]:bg-background/80">
        <div className="flex items-center gap-2 min-w-0">
          <Link href={`/learn/${guideId}`}>
            <Button variant="ghost" size="icon" className="h-7 w-7 shrink-0">
              <ChevronLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div className="truncate">
            <p className="text-xs text-muted-foreground truncate">{guideId.replace(/-/g, " ")}</p>
            <p className="text-sm font-medium truncate">{chapter.title}</p>
          </div>
        </div>
        <div className="flex items-center gap-1.5 shrink-0">
          <Badge variant="outline" className="text-[10px]">
            <Clock className="mr-1 h-2.5 w-2.5" />
            {chapter.reading_time_minutes}m
          </Badge>
          {isCompleted && (
            <Badge className="bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-300 text-[10px]">
              <Check className="mr-1 h-2.5 w-2.5" /> Done
            </Badge>
          )}
        </div>
      </div>

      {/* Pre-reading questions */}
      <PreReadingCard chapterId={fullChapterId} isCompleted={isCompleted} />

      {/* Content */}
      <article className="prose prose-sm dark:prose-invert max-w-none">
        <CurriculumRenderer content={chapter.content} />
      </article>

      {/* Bottom actions */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-t pt-4">
        <div className="flex gap-2">
          {!isCompleted && (
            <Button onClick={handleComplete} disabled={completing}>
              <Check className="mr-1.5 h-3.5 w-3.5" />
              {completing ? "Completing..." : "Mark complete"}
            </Button>
          )}
          <Button
            variant="outline"
            onClick={handleStartQuiz}
            disabled={quizLoading}
          >
            <ClipboardList className="mr-1.5 h-3.5 w-3.5" />
            {quizLoading ? "Generating..." : "Start quiz"}
          </Button>
        </div>
        <div className="flex gap-2">
          {chapter.prev_chapter && (
            <Link href={`/learn/${guideId}/${chapter.prev_chapter.split("/").pop()}`}>
              <Button variant="ghost" size="sm">
                <ArrowLeft className="mr-1 h-3.5 w-3.5" /> Prev
              </Button>
            </Link>
          )}
          {chapter.next_chapter && (
            <Link href={`/learn/${guideId}/${chapter.next_chapter.split("/").pop()}`}>
              <Button variant="ghost" size="sm">
                Next <ArrowRight className="ml-1 h-3.5 w-3.5" />
              </Button>
            </Link>
          )}
        </div>
      </div>

      {/* Reflection prompt */}
      {reflectionPrompt && (
        <div className="rounded-lg border border-primary/20 bg-primary/5 p-4 space-y-3">
          <p className="text-sm">{reflectionPrompt}</p>
          <div className="flex gap-2">
            <Button size="sm" onClick={handleSaveReflection} disabled={savingReflection}>
              <PenLine className="mr-1.5 h-3.5 w-3.5" />
              {savingReflection ? "Saving..." : "Write reflection"}
            </Button>
            <Button size="sm" variant="ghost" onClick={() => setReflectionPrompt(null)}>
              <X className="mr-1.5 h-3.5 w-3.5" /> Dismiss
            </Button>
          </div>
        </div>
      )}

      {/* Teach-back */}
      {isCompleted && <TeachBackCard chapterId={fullChapterId} />}

      {/* Quiz panel (inline) */}
      {quiz && quiz.length > 0 && (
        <div className="space-y-4 border-t pt-4">
          <h3 className="text-sm font-medium">Quiz — {quiz.length} questions</h3>
          {quiz.map((q) => (
            <div key={q.id} className="rounded-lg border p-4 space-y-2">
              <div className="flex items-start justify-between gap-2">
                <p className="text-sm">{q.question}</p>
                <Badge variant="outline" className="text-[10px] capitalize shrink-0">
                  {q.bloom_level}
                </Badge>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Cross-guide connections */}
      <RelatedChaptersCard chapterId={fullChapterId} />
    </div>
  );
}
