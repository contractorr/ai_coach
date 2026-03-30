"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { toast } from "sonner";
import { ArrowRight, Check, ChevronLeft, Clock, PenLine } from "lucide-react";
import { useToken } from "@/hooks/useToken";
import { apiFetch } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { CurriculumRenderer } from "@/components/curriculum/CurriculumRenderer";
import type { ChapterDetail, ChapterStatus, LearningToday } from "@/types/curriculum";

function getScrollPosition(): number {
  if (typeof window === "undefined") {
    return 0;
  }

  const scrollableHeight = document.documentElement.scrollHeight - window.innerHeight;
  if (scrollableHeight <= 0) {
    return 0;
  }

  return Math.min(Math.max(window.scrollY / scrollableHeight, 0), 1);
}

function restoreScrollPosition(scrollPosition: number): void {
  if (typeof window === "undefined") {
    return;
  }

  const scrollableHeight = document.documentElement.scrollHeight - window.innerHeight;
  const top = scrollableHeight > 0 ? scrollableHeight * scrollPosition : 0;
  window.scrollTo({ top, behavior: "auto" });
}

export default function ChapterReaderPage() {
  const token = useToken();
  const params = useParams();
  const guideId = params.guideId as string;
  const chapterId = params.chapterId as string;
  const requestedChapterId = `${guideId}/${chapterId}`;

  const [chapter, setChapter] = useState<ChapterDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [completing, setCompleting] = useState(false);
  const [reflectionPrompt, setReflectionPrompt] = useState<string | null>(null);
  const [reflectionDraft, setReflectionDraft] = useState("");
  const [savingReflection, setSavingReflection] = useState(false);
  const [reviewsDue, setReviewsDue] = useState<number | null>(null);
  const [loadingNextStep, setLoadingNextStep] = useState(false);
  const resolvedGuideId = chapter?.guide_id ?? guideId;
  const resolvedChapterId = chapter?.id ?? requestedChapterId;

  const lastSync = useRef(Date.now());
  const restoredChapterId = useRef<string | null>(null);

  const syncProgress = useCallback(
    async (
      status?: ChapterStatus,
      ids?: { chapterId?: string; guideId?: string },
      options?: { keepalive?: boolean; elapsedSeconds?: number; scrollPosition?: number },
    ) => {
      if (!token) return;
      const elapsed =
        options?.elapsedSeconds ?? Math.round((Date.now() - lastSync.current) / 1000);
      lastSync.current = Date.now();
      const activeChapterId = ids?.chapterId ?? resolvedChapterId;
      const activeGuideId = ids?.guideId ?? resolvedGuideId;
      try {
        await apiFetch(
          "/api/v1/curriculum/progress",
          {
            method: "POST",
            keepalive: options?.keepalive,
            body: JSON.stringify({
              chapter_id: activeChapterId,
              guide_id: activeGuideId,
              ...(status ? { status } : {}),
              reading_time_seconds: elapsed > 0 ? elapsed : undefined,
              scroll_position: options?.scrollPosition ?? getScrollPosition(),
            }),
          },
          token,
        );
      } catch {
        // Keep reading responsive even if background sync fails.
      }
    },
    [resolvedChapterId, resolvedGuideId, token],
  );

  useEffect(() => {
    if (!token || !guideId || !chapterId) return;
    setLoading(true);
    lastSync.current = Date.now();
    apiFetch<ChapterDetail>(
      `/api/v1/curriculum/guides/${guideId}/chapters/${chapterId}`,
      {},
      token,
    )
      .then((data) => {
        restoredChapterId.current = null;
        setChapter(data);
        if (!data.progress || data.progress.status === "not_started") {
          void syncProgress("in_progress", {
            chapterId: data.id,
            guideId: data.guide_id,
          }, {
            scrollPosition: 0,
          });
        }
      })
      .catch((e) => toast.error((e as Error).message))
      .finally(() => setLoading(false));
  }, [chapterId, guideId, syncProgress, token]);

  useEffect(() => {
    if (loading || !chapter) {
      return;
    }

    if (restoredChapterId.current === chapter.id) {
      return;
    }

    restoredChapterId.current = chapter.id;
    const savedScrollPosition =
      chapter.progress && chapter.progress.status !== "completed"
        ? chapter.progress.scroll_position
        : 0;

    let frameOne = 0;
    let frameTwo = 0;
    frameOne = window.requestAnimationFrame(() => {
      frameTwo = window.requestAnimationFrame(() => {
        restoreScrollPosition(savedScrollPosition);
      });
    });

    return () => {
      window.cancelAnimationFrame(frameOne);
      window.cancelAnimationFrame(frameTwo);
    };
  }, [chapter, loading]);

  useEffect(() => {
    const interval = setInterval(() => {
      void syncProgress();
    }, 30000);

    const flushProgress = () => {
      void syncProgress(undefined, undefined, { keepalive: true, elapsedSeconds: 0 });
    };

    const handleVisibilityChange = () => {
      if (document.visibilityState === "hidden") {
        flushProgress();
      }
    };

    window.addEventListener("pagehide", flushProgress);
    document.addEventListener("visibilitychange", handleVisibilityChange);

    return () => {
      clearInterval(interval);
      window.removeEventListener("pagehide", flushProgress);
      document.removeEventListener("visibilitychange", handleVisibilityChange);
      void syncProgress();
    };
  }, [syncProgress]);

  const handleComplete = async () => {
    if (!token) return;
    setCompleting(true);
    try {
      const elapsed = Math.round((Date.now() - lastSync.current) / 1000);
      lastSync.current = Date.now();
      const progressResult = await apiFetch<{
        reflection_prompt?: string;
      }>(
        "/api/v1/curriculum/progress",
        {
          method: "POST",
          body: JSON.stringify({
            chapter_id: resolvedChapterId,
            guide_id: resolvedGuideId,
            status: "completed",
            reading_time_seconds: elapsed > 0 ? elapsed : undefined,
            scroll_position: getScrollPosition(),
          }),
        },
        token,
      );
      toast.success("Chapter completed");
      if (progressResult.reflection_prompt) {
        setReflectionPrompt(progressResult.reflection_prompt);
        setReflectionDraft("");
      }
      const data = await apiFetch<ChapterDetail>(
        `/api/v1/curriculum/guides/${resolvedGuideId}/chapters/${chapterId}`,
        {},
        token,
      );
      setChapter(data);
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setCompleting(false);
    }
  };

  const handleSaveReflection = async () => {
    if (!token || !reflectionPrompt || !reflectionDraft.trim()) return;
    setSavingReflection(true);
    try {
      await apiFetch(
        "/api/v1/journal",
        {
          method: "POST",
          body: JSON.stringify({
            content: reflectionDraft.trim(),
            entry_type: "reflection",
            title: `Reflection: ${chapter?.title ?? chapterId}`,
            tags: ["curriculum", resolvedGuideId, "reflection"],
          }),
        },
        token,
      );
      toast.success("Reflection saved");
      setReflectionPrompt(null);
      setReflectionDraft("");
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setSavingReflection(false);
    }
  };

  const isCompleted = chapter?.progress?.status === "completed";

  useEffect(() => {
    if (!token || !isCompleted) {
      setReviewsDue(null);
      setLoadingNextStep(false);
      return;
    }

    let cancelled = false;
    setLoadingNextStep(true);

    apiFetch<LearningToday>("/api/v1/curriculum/today", {}, token)
      .then((today) => {
        if (!cancelled) {
          const reviewTask =
            today.tasks.find(
              (task) => task.task_type === "due_reviews" || task.task_type === "retry_reviews",
            ) ?? null;
          setReviewsDue(reviewTask?.review_count ?? today.reviews_due ?? 0);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setReviewsDue(0);
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoadingNextStep(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [isCompleted, token, resolvedChapterId]);

  if (loading) {
    return (
      <div className="mx-auto max-w-5xl space-y-4">
        <div className="h-6 w-48 animate-pulse rounded bg-muted" />
        <div className="h-96 animate-pulse rounded-lg bg-muted" />
      </div>
    );
  }

  if (!chapter) {
    return (
      <div className="py-12 text-center">
        <p className="text-muted-foreground">Chapter not found</p>
      </div>
    );
  }
  const guideHref = `/learn/${resolvedGuideId}`;
  const nextChapterHref = chapter.next_chapter
    ? `/learn/${resolvedGuideId}/${chapter.next_chapter.split("/").pop()}`
    : null;
  const reviewLabel =
    reviewsDue && reviewsDue > 0
      ? `Start ${reviewsDue} review${reviewsDue === 1 ? "" : "s"}`
      : "Start review";
  const primaryCompletedAction = loadingNextStep
    ? null
    : reviewsDue && reviewsDue > 0
      ? {
          href: "/learn/review",
          label: reviewLabel,
          description: "Use one short review session before moving on.",
        }
      : nextChapterHref
        ? {
            href: nextChapterHref,
            label: "Next chapter",
            description: "Keep your momentum and move straight into the next lesson.",
          }
        : {
            href: guideHref,
            label: "Back to guide",
            description: "You finished this chapter. Return to the guide for the next step.",
          };

  return (
    <div className="mx-auto max-w-5xl space-y-4 pb-28 md:pb-32">
      <div className="sticky top-0 z-10 -mx-4 flex items-center justify-between gap-2 border-b bg-background/95 px-4 py-2.5 backdrop-blur supports-[backdrop-filter]:bg-background/80">
        <div className="flex min-w-0 items-center gap-2">
          <Link href={guideHref}>
            <Button variant="ghost" size="icon" className="h-7 w-7 shrink-0">
              <ChevronLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div className="truncate">
            <p className="truncate text-xs text-muted-foreground">
              {resolvedGuideId.replace(/-/g, " ")}
            </p>
            <p className="truncate text-sm font-medium">{chapter.title}</p>
          </div>
        </div>
        <div className="flex shrink-0 items-center gap-1.5">
          <Badge variant="outline" className="text-[10px]">
            <Clock className="mr-1 h-2.5 w-2.5" />
            {chapter.reading_time_minutes}m
          </Badge>
          {isCompleted ? <Badge className="text-[10px]">Done</Badge> : null}
        </div>
      </div>

      <article className="rounded-xl border bg-card p-6 shadow-sm">
        <CurriculumRenderer content={chapter.content} guideId={resolvedGuideId} />
      </article>

      <div className="sticky bottom-4 z-20">
        <div className="rounded-xl border bg-background/95 p-4 shadow-lg backdrop-blur supports-[backdrop-filter]:bg-background/85">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="space-y-1">
              <p className="text-sm font-medium">
                {isCompleted ? "Chapter complete" : "Finish this chapter"}
              </p>
              <p className="text-sm text-muted-foreground">
                {isCompleted
                  ? loadingNextStep
                    ? "Choosing the clearest next step for you."
                    : primaryCompletedAction?.description
                  : "Mark the chapter complete when you're done reading."}
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              {!isCompleted ? (
                <Button onClick={handleComplete} disabled={completing}>
                  <Check className="mr-1.5 h-3.5 w-3.5" />
                  {completing ? "Completing..." : "Mark complete"}
                </Button>
              ) : (
                <>
                  {primaryCompletedAction ? (
                    <Button asChild>
                      <Link href={primaryCompletedAction.href}>
                        {primaryCompletedAction.label}
                      </Link>
                    </Button>
                  ) : (
                    <Button disabled>Choosing next step...</Button>
                  )}
                  {primaryCompletedAction?.href !== guideHref ? (
                    <Button variant="outline" asChild>
                      <Link href={guideHref}>Back to guide</Link>
                    </Button>
                  ) : null}
                </>
              )}
            </div>
          </div>
        </div>
      </div>

      {reflectionPrompt ? (
        <div className="space-y-3 rounded-lg border border-primary/20 bg-primary/5 p-4">
          <div className="space-y-2">
            <p className="text-xs font-medium uppercase tracking-wide text-primary/80">
              Optional reflection
            </p>
            <p className="text-sm">{reflectionPrompt}</p>
          </div>
          <Textarea
            value={reflectionDraft}
            onChange={(e) => setReflectionDraft(e.target.value)}
            placeholder="Write a short note about what clicked, what still feels fuzzy, or how you would use this."
            rows={5}
          />
          <div className="flex gap-2">
            <Button
              size="sm"
              onClick={handleSaveReflection}
              disabled={savingReflection || !reflectionDraft.trim()}
            >
              <PenLine className="mr-1.5 h-3.5 w-3.5" />
              {savingReflection ? "Saving..." : "Save reflection"}
            </Button>
            <Button
              size="sm"
              variant="ghost"
              onClick={() => {
                setReflectionPrompt(null);
                setReflectionDraft("");
              }}
            >
              Dismiss
            </Button>
          </div>
        </div>
      ) : null}

      {!isCompleted ? (
        <div className="flex flex-wrap items-center justify-between gap-3 border-t pt-4">
          <div />
          <div className="flex gap-2">
            {chapter.prev_chapter ? (
              <Button variant="ghost" size="sm" asChild>
                <Link href={`/learn/${resolvedGuideId}/${chapter.prev_chapter.split("/").pop()}`}>
                  Previous
                </Link>
              </Button>
            ) : null}
            {chapter.next_chapter ? (
              <Button variant="ghost" size="sm" asChild>
                <Link href={nextChapterHref ?? guideHref}>
                  Next
                  <ArrowRight className="ml-1 h-3.5 w-3.5" />
                </Link>
              </Button>
            ) : null}
          </div>
        </div>
      ) : null}
    </div>
  );
}
