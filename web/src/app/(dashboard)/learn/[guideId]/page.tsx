"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { toast } from "sonner";
import { ArrowLeft, BookOpen, Clock, GraduationCap, Play } from "lucide-react";
import { useToken } from "@/hooks/useToken";
import { apiFetch } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { ChapterList } from "@/components/curriculum/ChapterList";
import { DifficultyBadge } from "@/components/curriculum/DifficultyBadge";
import { ProgressRing } from "@/components/curriculum/ProgressRing";
import type { GuideDetail, PlacementQuestion, PlacementResult } from "@/types/curriculum";

function formatTime(minutes: number): string {
  if (minutes < 60) return `${minutes}m`;
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return m > 0 ? `${h}h ${m}m` : `${h}h`;
}

const assessmentStageLabels: Record<string, string> = {
  chapter_completion: "After chapter",
  review: "Review",
  scenario_practice: "Scenario",
  capstone: "Capstone",
};

export default function GuideDetailPage() {
  const token = useToken();
  const params = useParams();
  const guideId = params.guideId as string;

  const [guide, setGuide] = useState<GuideDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [enrolling, setEnrolling] = useState(false);

  // Placement state
  const [showPlacement, setShowPlacement] = useState(false);
  const [placementQuestions, setPlacementQuestions] = useState<PlacementQuestion[]>([]);
  const [placementAnswers, setPlacementAnswers] = useState<Record<string, string>>({});
  const [placementResult, setPlacementResult] = useState<PlacementResult | null>(null);
  const [placementLoading, setPlacementLoading] = useState(false);

  useEffect(() => {
    if (!token || !guideId) return;
    setLoading(true);
    apiFetch<GuideDetail>(`/api/v1/curriculum/guides/${guideId}`, {}, token)
      .then(setGuide)
      .catch((e) => toast.error((e as Error).message))
      .finally(() => setLoading(false));
  }, [token, guideId]);

  const handleEnroll = async () => {
    if (!token) return;
    setEnrolling(true);
    try {
      await apiFetch(`/api/v1/curriculum/guides/${guideId}/enroll`, { method: "POST" }, token);
      // Reload
      const updated = await apiFetch<GuideDetail>(`/api/v1/curriculum/guides/${guideId}`, {}, token);
      setGuide(updated);
      toast.success("Enrolled!");
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setEnrolling(false);
    }
  };

  const handleStartPlacement = async () => {
    if (!token) return;
    setPlacementLoading(true);
    setPlacementResult(null);
    setPlacementAnswers({});
    try {
      const data = await apiFetch<{ questions: PlacementQuestion[] }>(
        `/api/v1/curriculum/guides/${guideId}/placement/generate`,
        { method: "POST" },
        token,
      );
      setPlacementQuestions(data.questions);
      setShowPlacement(true);
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setPlacementLoading(false);
    }
  };

  const handleSubmitPlacement = async () => {
    if (!token) return;
    setPlacementLoading(true);
    try {
      const result = await apiFetch<PlacementResult>(
        `/api/v1/curriculum/guides/${guideId}/placement/submit`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ answers: placementAnswers }),
        },
        token,
      );
      setPlacementResult(result);
      if (result.passed) {
        toast.success("Placement passed — guide completed!");
        const updated = await apiFetch<GuideDetail>(
          `/api/v1/curriculum/guides/${guideId}`,
          {},
          token,
        );
        setGuide(updated);
      }
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setPlacementLoading(false);
    }
  };

  const isGuideCompleted = !!guide?.enrollment_completed_at;
  const firstUnread = guide?.chapters?.find((c) => c.status !== "completed");

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="h-8 w-48 animate-pulse rounded bg-muted" />
        <div className="h-40 animate-pulse rounded-lg bg-muted" />
      </div>
    );
  }

  if (!guide) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">Guide not found</p>
        <Link href="/learn">
          <Button variant="ghost" className="mt-2">Back to guides</Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-4 md:p-6">
      {/* Header */}
      <div className="flex items-center gap-2">
        <Link href="/learn">
          <Button variant="ghost" size="icon" className="h-8 w-8">
            <ArrowLeft className="h-4 w-4" />
          </Button>
        </Link>
        <h1 className="text-2xl font-semibold tracking-tight">{guide.title}</h1>
      </div>

      {/* Meta + actions */}
      <Card>
        <CardContent className="flex flex-wrap items-center justify-between gap-4 p-5">
          <div className="space-y-3">
            <div className="flex flex-wrap items-center gap-3">
              <DifficultyBadge level={guide.difficulty} />
              <span className="flex items-center gap-1 text-sm text-muted-foreground">
                <BookOpen className="h-3.5 w-3.5" />
                {guide.chapter_count} chapters
              </span>
              <span className="flex items-center gap-1 text-sm text-muted-foreground">
                <Clock className="h-3.5 w-3.5" />
                {formatTime(guide.total_reading_time_minutes)}
              </span>
              {guide.has_glossary && (
                <Badge variant="outline" className="text-[10px]">Glossary</Badge>
              )}
            </div>

            {(guide.learning_programs?.length ?? 0) > 0 && (
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-xs font-medium text-muted-foreground">Programs:</span>
                {guide.learning_programs?.map((program) => (
                  <Badge
                    key={program.id}
                    variant="outline"
                    className="text-[10px]"
                    style={{ borderColor: program.color, color: program.color }}
                    title={program.description}
                  >
                    {program.title}
                  </Badge>
                ))}
              </div>
            )}
          </div>
          <div className="flex items-center gap-3">
            {guide.enrolled && (
              <ProgressRing progress={guide.progress_pct ?? 0} size={44} strokeWidth={4} />
            )}
            {!guide.enrolled && (
              <Button onClick={handleEnroll} disabled={enrolling}>
                {enrolling ? "Enrolling..." : "Enroll"}
              </Button>
            )}
            {!isGuideCompleted && (
              <Button
                variant="outline"
                onClick={handleStartPlacement}
                disabled={placementLoading}
              >
                <GraduationCap className="mr-1.5 h-3.5 w-3.5" />
                {placementLoading ? "Generating..." : "Test out"}
              </Button>
            )}
            {firstUnread && (
              <Link href={`/learn/${guideId}/${firstUnread.id.split("/").pop()}`}>
                <Button>
                  <Play className="mr-1.5 h-3.5 w-3.5" />
                  {guide.chapters_completed ? "Continue" : "Start reading"}
                </Button>
              </Link>
            )}
          </div>
        </CardContent>
      </Card>

      {(guide.applied_assessments?.length ?? 0) > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Applied Assessment Pilot</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-3 lg:grid-cols-2">
            {guide.applied_assessments?.map((assessment) => (
              <div
                key={`${assessment.stage}-${assessment.type}`}
                className="space-y-2 rounded-lg border p-3"
              >
                <div className="flex flex-wrap items-center gap-2">
                  <Badge variant="outline" className="text-[10px]">
                    {assessmentStageLabels[assessment.stage] ?? assessment.stage}
                  </Badge>
                  <p className="text-sm font-medium">{assessment.title}</p>
                </div>
                <p className="text-sm text-muted-foreground">{assessment.summary}</p>
                <p className="text-xs text-muted-foreground">{assessment.deliverable}</p>
                <p className="text-xs">{assessment.prompt}</p>
                <p className="text-xs text-muted-foreground">
                  Evaluate on {assessment.evaluation_focus.join(", ").toLowerCase()}.
                </p>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Placement quiz */}
      {showPlacement && placementQuestions.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <GraduationCap className="h-4 w-4" />
              Placement Quiz
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {placementResult ? (
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <Badge variant={placementResult.passed ? "default" : "destructive"}>
                    {placementResult.passed ? "Passed" : "Not passed"}
                  </Badge>
                  <span className="text-sm text-muted-foreground">
                    Average: {placementResult.average_grade.toFixed(1)} / 5
                    (need {placementResult.threshold})
                  </span>
                </div>
                {placementResult.results.map((r, i) => (
                  <div key={r.question_id} className="rounded border p-3 text-sm space-y-1">
                    <p className="font-medium">Q{i + 1}: {placementQuestions[i]?.question}</p>
                    <p className="text-muted-foreground">
                      Grade: {r.grade}/5 — {r.feedback}
                    </p>
                  </div>
                ))}
                {!placementResult.passed && (
                  <div className="flex gap-2">
                    {firstUnread && (
                      <Link href={`/learn/${guideId}/${firstUnread.id.split("/").pop()}`}>
                        <Button>Start reading instead</Button>
                      </Link>
                    )}
                    <Button variant="ghost" onClick={() => setShowPlacement(false)}>
                      Dismiss
                    </Button>
                  </div>
                )}
              </div>
            ) : (
              <>
                {placementQuestions.map((q, i) => (
                  <div key={q.id} className="space-y-1.5">
                    <label className="text-sm font-medium">
                      {i + 1}. {q.question}
                    </label>
                    <Input
                      placeholder="Your answer..."
                      value={placementAnswers[q.id] ?? ""}
                      onChange={(e) =>
                        setPlacementAnswers((prev) => ({ ...prev, [q.id]: e.target.value }))
                      }
                    />
                  </div>
                ))}
                <div className="flex gap-2">
                  <Button
                    onClick={handleSubmitPlacement}
                    disabled={
                      placementLoading ||
                      Object.keys(placementAnswers).length < placementQuestions.length
                    }
                  >
                    {placementLoading ? "Grading..." : "Submit"}
                  </Button>
                  <Button variant="ghost" onClick={() => setShowPlacement(false)}>
                    Cancel
                  </Button>
                </div>
              </>
            )}
          </CardContent>
        </Card>
      )}

      {/* Chapter list */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Chapters</CardTitle>
        </CardHeader>
        <CardContent>
          <ChapterList guideId={guideId} chapters={guide.chapters ?? []} />
        </CardContent>
      </Card>
    </div>
  );
}
