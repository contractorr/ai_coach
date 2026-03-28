"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useParams } from "next/navigation";
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
import { Textarea } from "@/components/ui/textarea";
import { CurriculumRenderer } from "@/components/curriculum/CurriculumRenderer";
import { PreReadingCard } from "@/components/curriculum/PreReadingCard";
import { TeachBackCard } from "@/components/curriculum/TeachBackCard";
import { RelatedChaptersCard } from "@/components/curriculum/RelatedChaptersCard";
import type { ChapterDetail, ChapterStatus, QuizResult, ReviewItem } from "@/types/curriculum";

export default function ChapterReaderPage() {
  const token = useToken();
  const params = useParams();
  const guideId = params.guideId as string;
  const chapterId = params.chapterId as string;
  const fullChapterId = `${guideId}/${chapterId}`;

  const [chapter, setChapter] = useState<ChapterDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [completing, setCompleting] = useState(false);
  const [quiz, setQuiz] = useState<ReviewItem[] | null>(null);
  const [quizAnswers, setQuizAnswers] = useState<Record<string, string>>({});
  const [quizResults, setQuizResults] = useState<QuizResult[] | null>(null);
  const [quizLoading, setQuizLoading] = useState(false);
  const [quizSubmitting, setQuizSubmitting] = useState(false);
  const [reflectionPrompt, setReflectionPrompt] = useState<string | null>(null);
  const [reflectionDraft, setReflectionDraft] = useState("");
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
          "/api/v1/curriculum/progress",
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
      `/api/v1/curriculum/guides/${guideId}/chapters/${chapterId}`,
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
        "/api/v1/curriculum/progress",
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
        setReflectionDraft("");
      }
      // Refresh to get updated status
      const data = await apiFetch<ChapterDetail>(
        `/api/v1/curriculum/guides/${guideId}/chapters/${chapterId}`,
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
            tags: ["curriculum", guideId, "reflection"],
          }),
        },
        token
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

  const handleStartQuiz = async () => {
    if (!token) return;
    setQuizLoading(true);
    try {
      const data = await apiFetch<{ questions: ReviewItem[] }>(
        `/api/v1/curriculum/quiz/${fullChapterId}/generate`,
        { method: "POST" },
        token
      );
      setQuiz(data.questions);
      setQuizResults(null);
      setQuizAnswers(
        Object.fromEntries(
          data.questions.map((question) => [question.id, quizAnswers[question.id] ?? ""])
        )
      );
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setQuizLoading(false);
    }
  };

  const handleQuizAnswerChange = (questionId: string, value: string) => {
    setQuizAnswers((prev) => ({ ...prev, [questionId]: value }));
  };

  const handleSubmitQuiz = async () => {
    if (!token || !quiz || quiz.length === 0) return;

    setQuizSubmitting(true);
    try {
      const answers = Object.fromEntries(
        quiz.map((question) => [question.id, quizAnswers[question.id]?.trim() ?? ""])
      );
      const data = await apiFetch<{ results: QuizResult[] }>(
        `/api/v1/curriculum/quiz/${fullChapterId}/submit`,
        {
          method: "POST",
          body: JSON.stringify({ answers }),
        },
        token
      );
      setQuizResults(data.results);
      toast.success("Quiz graded");
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setQuizSubmitting(false);
    }
  };

  const quizResultsById = useMemo(
    () => new Map((quizResults ?? []).map((result) => [result.question_id, result])),
    [quizResults]
  );
  const quizAverageGrade =
    quizResults && quizResults.length > 0
      ? quizResults.reduce((sum, result) => sum + result.grade, 0) / quizResults.length
      : null;
  const canSubmitQuiz =
    !!quiz &&
    quiz.length > 0 &&
    quiz.every((question) => (quizAnswers[question.id] ?? "").trim().length > 0);

  if (loading) {
    return (
      <div className="space-y-4 max-w-7xl mx-auto">
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
    <div className="max-w-7xl mx-auto space-y-4 pb-12">
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
      <article className="max-w-none rounded-xl border bg-card p-6 shadow-sm">
        <CurriculumRenderer content={chapter.content} guideId={guideId} />
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
          <div className="space-y-2">
            <p className="text-xs font-medium uppercase tracking-wide text-primary/80">
              Reflection prompt
            </p>
            <p className="text-sm">{reflectionPrompt}</p>
          </div>
          <Textarea
            value={reflectionDraft}
            onChange={(e) => setReflectionDraft(e.target.value)}
            placeholder="Write your own reflection on what changed in your understanding, what still feels unclear, or how this applies to your work."
            rows={6}
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
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h3 className="text-sm font-medium">Quiz — {quiz.length} questions</h3>
            {quizAverageGrade !== null && (
              <Badge variant="outline" className="text-xs">
                Average grade: {quizAverageGrade.toFixed(1)} / 5
              </Badge>
            )}
          </div>

          {quizResults && quizResults.length > 0 && (
            <div className="rounded-lg border bg-muted/30 p-4 space-y-3">
              <div className="flex flex-wrap items-center gap-2">
                <Badge className="text-xs">
                  Quiz graded
                </Badge>
                <p className="text-sm text-muted-foreground">
                  Review the feedback below, revise any weak answers, and try again if needed.
                </p>
              </div>
              <div className="flex flex-wrap gap-2">
                <Button size="sm" variant="outline" onClick={() => setQuizResults(null)}>
                  Try again
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => {
                    setQuiz(null);
                    setQuizResults(null);
                  }}
                >
                  Close quiz
                </Button>
              </div>
            </div>
          )}

          {quiz.map((q, index) => {
            const result = quizResultsById.get(q.id);
            return (
            <div key={q.id} className="rounded-lg border p-4 space-y-3">
              <div className="flex items-start justify-between gap-2">
                <p className="text-sm">
                  <span className="font-medium">Q{index + 1}.</span> {q.question}
                </p>
                <Badge variant="outline" className="text-[10px] capitalize shrink-0">
                  {q.bloom_level}
                </Badge>
              </div>
              <Textarea
                value={quizAnswers[q.id] ?? ""}
                onChange={(e) => handleQuizAnswerChange(q.id, e.target.value)}
                placeholder="Write your answer..."
                rows={4}
                className="text-sm"
              />

              {result && (
                <div className="rounded-lg border bg-muted/30 p-3 space-y-3">
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge variant={result.grade >= 4 ? "default" : "outline"} className="text-xs">
                      Grade: {result.grade} / 5
                    </Badge>
                    <p className="text-sm text-muted-foreground">{result.feedback}</p>
                  </div>

                  {result.correct_points.length > 0 && (
                    <div className="space-y-1">
                      <p className="text-xs font-medium uppercase tracking-wide text-foreground/80">
                        Strong points
                      </p>
                      <ul className="ml-5 list-disc space-y-1 text-sm text-muted-foreground">
                        {result.correct_points.map((point) => (
                          <li key={point}>{point}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {result.missing_points.length > 0 && (
                    <div className="space-y-1">
                      <p className="text-xs font-medium uppercase tracking-wide text-foreground/80">
                        Missing points
                      </p>
                      <ul className="ml-5 list-disc space-y-1 text-sm text-muted-foreground">
                        {result.missing_points.map((point) => (
                          <li key={point}>{point}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {q.expected_answer && (
                    <div className="space-y-1">
                      <p className="text-xs font-medium uppercase tracking-wide text-foreground/80">
                        Reference answer
                      </p>
                      <p className="text-sm text-muted-foreground">{q.expected_answer}</p>
                    </div>
                  )}
                </div>
              )}
            </div>
            );
          })}

          <div className="flex flex-wrap gap-2">
            <Button onClick={handleSubmitQuiz} disabled={!canSubmitQuiz || quizSubmitting}>
              <ClipboardList className="mr-1.5 h-3.5 w-3.5" />
              {quizSubmitting ? "Submitting..." : quizResults ? "Re-submit quiz" : "Submit quiz"}
            </Button>
            <Button
              variant="ghost"
              onClick={() => {
                setQuiz(null);
                setQuizResults(null);
              }}
            >
              Hide quiz
            </Button>
          </div>
        </div>
      )}

      {/* Cross-guide connections */}
      <RelatedChaptersCard chapterId={fullChapterId} />
    </div>
  );
}
