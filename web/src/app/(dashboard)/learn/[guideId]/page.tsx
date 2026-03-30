"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { toast } from "sonner";
import { ArrowLeft, BookOpen, Clock } from "lucide-react";

import { ChapterList } from "@/components/curriculum/ChapterList";
import { DifficultyBadge } from "@/components/curriculum/DifficultyBadge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useToken } from "@/hooks/useToken";
import { apiFetch } from "@/lib/api";
import type { Guide, GuideDetail } from "@/types/curriculum";

function formatTime(minutes: number): string {
  if (minutes < 60) return `${minutes}m`;
  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;
  return remainingMinutes > 0 ? `${hours}h ${remainingMinutes}m` : `${hours}h`;
}

function isGuideCompleted(guide: Pick<Guide, "enrollment_completed_at" | "chapters_total" | "chapters_completed" | "progress_pct">): boolean {
  if (guide.enrollment_completed_at) {
    return true;
  }
  if (
    typeof guide.chapters_total === "number" &&
    typeof guide.chapters_completed === "number" &&
    guide.chapters_total > 0 &&
    guide.chapters_completed >= guide.chapters_total
  ) {
    return true;
  }
  return (guide.progress_pct ?? 0) >= 100;
}

function formatGuideTitleFromId(id: string): string {
  return id
    .replace(/^\d+-/, "")
    .replace(/-guide$/, "")
    .replace(/-/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

export default function GuideDetailPage() {
  const token = useToken();
  const params = useParams();
  const router = useRouter();
  const guideId = params.guideId as string;

  const [guide, setGuide] = useState<GuideDetail | null>(null);
  const [allGuides, setAllGuides] = useState<Guide[]>([]);
  const [loading, setLoading] = useState(true);
  const [acting, setActing] = useState(false);

  useEffect(() => {
    if (!token || !guideId) return;
    setLoading(true);
    Promise.all([
      apiFetch<GuideDetail>(`/api/v1/curriculum/guides/${guideId}`, {}, token),
      apiFetch<Guide[]>("/api/v1/curriculum/guides", {}, token),
    ])
      .then(([guideData, guidesData]) => {
        setGuide(guideData);
        setAllGuides(guidesData);
      })
      .catch((e) => toast.error((e as Error).message))
      .finally(() => setLoading(false));
  }, [token, guideId]);

  const resolvedGuideId = guide?.id ?? guideId;
  const firstReadableChapter = useMemo(
    () =>
      guide?.chapters?.find(
        (chapter) => !chapter.is_glossary && chapter.status !== "completed",
      ) ??
      guide?.chapters?.find((chapter) => !chapter.is_glossary) ??
      null,
    [guide],
  );
  const guideLookup = useMemo(
    () => new Map(allGuides.map((item) => [item.id, item])),
    [allGuides],
  );
  const unmetPrerequisites = useMemo(
    () =>
      (guide?.prerequisites ?? [])
        .map((prereqId) => {
          const prereqGuide = guideLookup.get(prereqId);
          return {
            id: prereqId,
            title: prereqGuide?.title ?? formatGuideTitleFromId(prereqId),
            completed: prereqGuide ? isGuideCompleted(prereqGuide) : false,
          };
        })
        .filter((prereq) => !prereq.completed),
    [guide?.prerequisites, guideLookup],
  );
  const hasUnmetPrerequisites = unmetPrerequisites.length > 0;

  const primaryActionLabel = firstReadableChapter
    ? guide?.enrolled
      ? "Continue"
      : hasUnmetPrerequisites
        ? "Start anyway"
        : "Start"
    : "Review";

  const primaryActionDetail = firstReadableChapter
    ? hasUnmetPrerequisites && !guide?.enrolled
      ? `Recommended first: ${unmetPrerequisites
          .map((prereq) => prereq.title)
          .join(", ")}. You can still start this guide now.`
      : `Next chapter: ${firstReadableChapter.title}`
    : "You've finished the reading. Use review to keep it fresh.";
  const guideSummary =
    guide?.summary || "Move through this guide chapter by chapter in one focused sequence.";
  const whyNow = firstReadableChapter
    ? guide?.enrolled
      ? "Why now: continue from your current point instead of restarting."
      : hasUnmetPrerequisites
        ? `Why now: this guide builds on ${unmetPrerequisites.length} recommended prerequisite guide${
            unmetPrerequisites.length === 1 ? "" : "s"
          }, but you can ignore that advice if you want to start here.`
        : "Why now: this guide is ready to start and scoped for a clear first pass."
    : "Why now: the reading is complete, so recall is the highest-value next step.";

  const handlePrimaryAction = async () => {
    if (!guide || acting) return;
    setActing(true);
    try {
      if (firstReadableChapter) {
        if (!guide.enrolled && token) {
          await apiFetch(
            `/api/v1/curriculum/guides/${resolvedGuideId}/enroll`,
            { method: "POST" },
            token,
          );
        }
        router.push(`/learn/${resolvedGuideId}/${firstReadableChapter.id.split("/").pop()}`);
        return;
      }

      router.push("/learn/review");
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setActing(false);
    }
  };

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
      <div className="py-12 text-center">
        <p className="text-muted-foreground">Guide not found</p>
        <Link href="/learn">
          <Button variant="ghost" className="mt-2">
            Back to Guide Library
          </Button>
        </Link>
      </div>
    );
  }

  const chaptersCompleted = guide.chapters_completed ?? 0;
  const chaptersTotal = guide.chapters_total ?? guide.chapter_count;
  const showGuideSynthesis =
    Boolean(guide.guide_synthesis) && chaptersTotal > 0 && chaptersCompleted >= chaptersTotal;

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-4 md:p-6">
      <div className="flex items-center gap-2">
        <Link href="/learn">
          <Button variant="ghost" size="icon" className="h-8 w-8">
            <ArrowLeft className="h-4 w-4" />
          </Button>
        </Link>
        <h1 className="text-2xl font-semibold tracking-tight">{guide.title}</h1>
      </div>

      <Card>
        <CardHeader className="space-y-3">
          <div className="flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
            <DifficultyBadge level={guide.difficulty} />
            <span className="flex items-center gap-1">
              <BookOpen className="h-3.5 w-3.5" />
              {guide.chapter_count} chapters
            </span>
            <span className="flex items-center gap-1">
              <Clock className="h-3.5 w-3.5" />
              {formatTime(guide.total_reading_time_minutes)}
            </span>
          </div>
          <div className="space-y-1">
            <p className="text-sm leading-relaxed text-foreground/80">{guideSummary}</p>
            <CardTitle className="text-xl">{primaryActionLabel}</CardTitle>
            <CardDescription>
              {primaryActionDetail}
              {" "}
              {guide.enrolled
                ? `${chaptersCompleted} of ${chaptersTotal} chapters completed.`
                : hasUnmetPrerequisites
                  ? "You can still start here, but the recommended order is to complete the guides below first."
                  : "Start here and move through the guide chapter by chapter."}
            </CardDescription>
            <p className="text-xs font-medium uppercase tracking-[0.14em] text-muted-foreground">
              {whyNow}
            </p>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {hasUnmetPrerequisites && !guide.enrolled ? (
            <div className="space-y-2 rounded-lg border border-amber-200 bg-amber-50/60 p-3 text-sm dark:border-amber-900/60 dark:bg-amber-950/20">
              <p className="text-xs font-medium uppercase tracking-[0.14em] text-amber-900/80 dark:text-amber-200/90">
                Recommended first
              </p>
              <p className="text-foreground/80">
                These guides are recommended prerequisites. You can ignore this and start anyway.
              </p>
              <div className="flex flex-wrap gap-2">
                {unmetPrerequisites.map((prereq) => (
                  <Button key={prereq.id} variant="outline" size="sm" asChild>
                    <Link href={`/learn/${prereq.id}`}>{prereq.title}</Link>
                  </Button>
                ))}
              </div>
            </div>
          ) : null}
          <div className="flex flex-wrap gap-2">
          <Button onClick={() => void handlePrimaryAction()} disabled={acting}>
            {acting ? "Opening..." : primaryActionLabel}
          </Button>
          <Button variant="outline" asChild>
            <Link href="/learn">Back to Guide Library</Link>
          </Button>
          </div>
        </CardContent>
      </Card>

      {showGuideSynthesis && guide.guide_synthesis ? (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">What this guide changes</CardTitle>
            <CardDescription>
              A short synthesis to keep the model reusable after the reading is done.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-1">
              <p className="text-xs font-medium uppercase tracking-[0.14em] text-muted-foreground">
                What it explains
              </p>
              <p className="text-sm leading-relaxed text-foreground/85">
                {guide.guide_synthesis.what_this_explains}
              </p>
            </div>
            <div className="space-y-1">
              <p className="text-xs font-medium uppercase tracking-[0.14em] text-muted-foreground">
                Where it applies
              </p>
              <div className="flex flex-wrap gap-2">
                {guide.guide_synthesis.where_it_applies.map((item) => (
                  <span
                    key={item}
                    className="rounded-full border border-border/70 bg-muted/30 px-2.5 py-1 text-xs text-foreground/80"
                  >
                    {item}
                  </span>
                ))}
              </div>
            </div>
            <div className="space-y-1">
              <p className="text-xs font-medium uppercase tracking-[0.14em] text-muted-foreground">
                Where it breaks
              </p>
              <p className="text-sm leading-relaxed text-foreground/85">
                {guide.guide_synthesis.where_it_breaks}
              </p>
            </div>
          </CardContent>
        </Card>
      ) : null}

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Chapters</CardTitle>
          <CardDescription>
            Work through the guide one chapter at a time.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ChapterList guideId={resolvedGuideId} chapters={guide.chapters ?? []} />
        </CardContent>
      </Card>
    </div>
  );
}
