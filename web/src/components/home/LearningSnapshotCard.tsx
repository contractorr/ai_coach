"use client";

import Link from "next/link";
import { ArrowRight, BookOpen, Clock3, Flame, GraduationCap, RotateCcw } from "lucide-react";

import { ProgressRing } from "@/components/curriculum/ProgressRing";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { LearningStats, NextRecommendation } from "@/types/curriculum";

interface Props {
  stats: LearningStats | null;
  nextStep: NextRecommendation | null;
  loading: boolean;
}

const recommendationLabels: Record<string, string> = {
  continue: "Continue",
  enrolled: "Current guide",
  ready: "Unlocked",
  entry: "Recommended start",
  fallback: "Next step",
};

function formatTime(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);

  if (hours <= 0) {
    return `${minutes}m`;
  }

  return minutes > 0 ? `${hours}h ${minutes}m` : `${hours}h`;
}

function buildNextHref(nextStep: NextRecommendation | null): string {
  if (!nextStep?.guide_id) {
    return "/learn";
  }

  if (nextStep.chapter?.id) {
    return `/learn/${nextStep.guide_id}/${nextStep.chapter.id.split("/").pop()}`;
  }

  return `/learn/${nextStep.guide_id}`;
}

export function LearningSnapshotCard({ stats, nextStep, loading }: Props) {
  if (loading && !stats && !nextStep) {
    return <div className="h-full min-h-72 animate-pulse rounded-2xl border bg-muted/30" />;
  }

  const progressPct =
    stats && stats.total_chapters > 0
      ? (stats.chapters_completed / stats.total_chapters) * 100
      : 0;
  const nextHref = buildNextHref(nextStep);
  const nextCta =
    nextStep?.chapter ? "Resume lesson" : nextStep?.action === "enroll" ? "Open guide" : "Open Learn";
  const title =
    stats?.guides_enrolled && stats.guides_enrolled > 0
      ? `${stats.chapters_completed}/${stats.total_chapters} chapters completed`
      : nextStep?.guide_id
        ? "Recommended place to start"
        : "Learning space is ready";
  const description =
    stats?.guides_enrolled && stats.guides_enrolled > 0
      ? "Progress from your enrolled curriculum now shows up on Home."
      : "Structured learning is now part of your default dashboard, not a separate silo.";

  const metrics = [
    {
      icon: GraduationCap,
      label: "Guides",
      value: stats?.guides_enrolled ?? 0,
    },
    {
      icon: Flame,
      label: "Streak",
      value: `${stats?.current_streak_days ?? 0}d`,
    },
    {
      icon: RotateCcw,
      label: "Due",
      value: stats?.reviews_due ?? 0,
    },
    {
      icon: Clock3,
      label: "Reading",
      value: formatTime(stats?.total_reading_time_seconds ?? 0),
    },
  ];

  return (
    <Card className="h-full border-primary/10 bg-card/70 shadow-sm backdrop-blur supports-[backdrop-filter]:bg-card/75">
      <CardHeader className="space-y-4">
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-1">
            <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
              Learning progress
            </p>
            <CardTitle className="text-xl">{title}</CardTitle>
            <CardDescription>{description}</CardDescription>
          </div>
          <div className="hidden sm:block">
            <ProgressRing progress={progressPct} size={68} strokeWidth={5} />
          </div>
        </div>

        <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
          {metrics.map(({ icon: Icon, label, value }) => (
            <div key={label} className="rounded-xl border bg-background/70 p-3">
              <div className="mb-2 flex items-center gap-2 text-muted-foreground">
                <Icon className="h-3.5 w-3.5" />
                <span className="text-[11px] font-medium uppercase tracking-[0.14em]">{label}</span>
              </div>
              <p className="text-lg font-semibold">{value}</p>
            </div>
          ))}
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        <div className="rounded-2xl border bg-background/80 p-4">
          <div className="mb-3 flex flex-wrap items-center gap-2">
            <p className="text-sm font-medium">Next study block</p>
            <Badge variant="outline" className="text-[10px]">
              {recommendationLabels[nextStep?.recommendation_type ?? "fallback"] ?? "Next step"}
            </Badge>
            {stats && stats.reviews_due > 0 ? (
              <Badge variant="secondary" className="text-[10px]">
                {stats.reviews_due} review{stats.reviews_due === 1 ? "" : "s"} due
              </Badge>
            ) : null}
          </div>

          {nextStep?.guide_id ? (
            <div className="space-y-3">
              <div className="space-y-1">
                <p className="text-base font-semibold">
                  {nextStep.chapter?.title ?? nextStep.guide_title ?? "Open your learning dashboard"}
                </p>
                {nextStep.chapter && nextStep.guide_title ? (
                  <p className="text-xs text-muted-foreground">{nextStep.guide_title}</p>
                ) : null}
                <p className="text-sm text-muted-foreground">{nextStep.reason}</p>
              </div>
              <div className="flex flex-wrap gap-2">
                <Button size="sm" asChild>
                  <Link href={nextHref}>
                    {nextCta}
                    <ArrowRight className="ml-1.5 h-3.5 w-3.5" />
                  </Link>
                </Button>
                <Button size="sm" variant="outline" asChild>
                  <Link href={stats && stats.reviews_due > 0 ? "/learn/review" : "/learn"}>
                    {stats && stats.reviews_due > 0 ? "Start reviews" : "View guides"}
                  </Link>
                </Button>
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              <p className="text-sm text-muted-foreground">
                No current recommendation yet. Open Learn to sync guides, enroll, or pick a new track.
              </p>
              <Button size="sm" asChild>
                <Link href="/learn">
                  Open Learn
                  <ArrowRight className="ml-1.5 h-3.5 w-3.5" />
                </Link>
              </Button>
            </div>
          )}
        </div>

        <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
          <BookOpen className="h-3.5 w-3.5" />
          <span>
            {stats?.guides_completed ?? 0} guide{stats?.guides_completed === 1 ? "" : "s"} completed so far
          </span>
        </div>
      </CardContent>
    </Card>
  );
}
