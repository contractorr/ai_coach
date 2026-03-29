"use client";

import Link from "next/link";
import { ArrowRight, RotateCcw } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  buildLearningTaskHref,
  formatLearningMinutes,
  learningTaskLabels,
} from "@/lib/curriculum";
import type { LearningStats, LearningToday } from "@/types/curriculum";

interface Props {
  stats: LearningStats | null;
  today: LearningToday | null;
  loading: boolean;
}

export function LearningSnapshotCard({ stats, today, loading }: Props) {
  if (loading && !stats && !today) {
    return (
      <div className="h-full min-h-72 animate-pulse rounded-2xl border bg-muted/30" />
    );
  }

  const reviewTask =
    today?.tasks.find(
      (task) => task.task_type === "due_reviews" || task.task_type === "retry_reviews",
    ) ?? null;
  const primaryTask =
    today?.tasks.find(
      (task) => task.task_type === "continue_chapter" || task.task_type === "start_guide",
    ) ??
    reviewTask ??
    today?.tasks[0] ??
    null;
  const reviewCount =
    reviewTask?.review_count ?? reviewTask?.retry_count ?? stats?.reviews_due ?? today?.reviews_due ?? 0;

  return (
    <Card className="h-full border-primary/10 bg-card/70 shadow-sm backdrop-blur supports-[backdrop-filter]:bg-card/75">
      <CardHeader className="space-y-3">
        <div className="space-y-1">
          <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
            Learning
          </p>
          <CardTitle className="text-xl">
            {primaryTask?.title ?? "Choose a guide to start learning"}
          </CardTitle>
          <CardDescription>
            {primaryTask?.detail ??
              "Pick one guide, continue your next chapter, and return for short reviews when they are due."}
          </CardDescription>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {primaryTask ? (
          <div className="rounded-2xl border bg-background/80 p-4">
            <div className="mb-3 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
              <Badge variant="outline" className="text-[10px]">
                {learningTaskLabels[primaryTask.task_type]}
              </Badge>
              <span>{formatLearningMinutes(primaryTask.estimate_minutes)}</span>
              {primaryTask.guide_title ? <span>{primaryTask.guide_title}</span> : null}
            </div>

            <div className="flex flex-wrap gap-2">
              <Button size="sm" asChild>
                <Link href={buildLearningTaskHref(primaryTask)}>
                  {primaryTask.cta_label}
                  <ArrowRight className="ml-1.5 h-3.5 w-3.5" />
                </Link>
              </Button>
              <Button size="sm" variant="outline" asChild>
                <Link href="/learn">Open Guide Library</Link>
              </Button>
            </div>
          </div>
        ) : (
          <div className="rounded-2xl border bg-background/80 p-4">
            <p className="text-sm text-muted-foreground">
              Nothing is in progress yet. Open your Guide Library and pick one guide to start.
            </p>
            <Button size="sm" className="mt-3" asChild>
              <Link href="/learn">
                Open Guide Library
                <ArrowRight className="ml-1.5 h-3.5 w-3.5" />
              </Link>
            </Button>
          </div>
        )}

        <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
          <RotateCcw className="h-3.5 w-3.5" />
          <span>
            {reviewCount > 0
              ? `${reviewCount} review${reviewCount === 1 ? "" : "s"} waiting.`
              : "No reviews waiting right now."}
          </span>
        </div>
      </CardContent>
    </Card>
  );
}
