"use client";

import Link from "next/link";
import {
  ArrowRight,
  BookOpen,
  Clock3,
  Flame,
  GraduationCap,
  RotateCcw,
  Route,
} from "lucide-react";

import { ProgressRing } from "@/components/curriculum/ProgressRing";
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
  formatLearningProgramSignals,
  formatLearningSeconds,
  learningProgramStatusLabels,
  learningTaskLabels,
  recommendationLabels,
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

  const progressPct =
    stats && stats.total_chapters > 0
      ? (stats.chapters_completed / stats.total_chapters) * 100
      : 0;
  const primaryTask = today?.tasks[0] ?? null;
  const remainingTasks = today?.tasks.slice(1, 3) ?? [];

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
      value: formatLearningSeconds(stats?.total_reading_time_seconds ?? 0),
    },
  ];

  return (
    <Card className="h-full border-primary/10 bg-card/70 shadow-sm backdrop-blur supports-[backdrop-filter]:bg-card/75">
      <CardHeader className="space-y-4">
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-1">
            <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
              Today in Learn
            </p>
            <CardTitle className="text-xl">
              {today?.headline ?? "Learning workflow"}
            </CardTitle>
            <CardDescription>
              {today?.summary ??
                "Structured learning now shows up as a daily workflow on Home, not a side workspace."}
            </CardDescription>
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
                <span className="text-[11px] font-medium uppercase tracking-[0.14em]">
                  {label}
                </span>
              </div>
              <p className="text-lg font-semibold">{value}</p>
            </div>
          ))}
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {primaryTask ? (
          <div className="rounded-2xl border bg-background/80 p-4">
            <div className="mb-3 flex flex-wrap items-center gap-2">
              <p className="text-sm font-medium">Primary block</p>
              <Badge variant="outline" className="text-[10px]">
                {learningTaskLabels[primaryTask.task_type]}
              </Badge>
              {primaryTask.recommendation_type ? (
                <Badge variant="secondary" className="text-[10px]">
                  {recommendationLabels[primaryTask.recommendation_type]}
                </Badge>
              ) : null}
              <Badge variant="outline" className="text-[10px]">
                {formatLearningMinutes(primaryTask.estimate_minutes)}
              </Badge>
            </div>

            <div className="space-y-3">
              <div className="space-y-1">
                <p className="text-base font-semibold">{primaryTask.title}</p>
                {primaryTask.guide_title ? (
                  <p className="text-xs text-muted-foreground">
                    {primaryTask.guide_title}
                  </p>
                ) : null}
                <p className="text-sm text-muted-foreground">
                  {primaryTask.detail}
                </p>
              </div>
              <div className="flex flex-wrap gap-2">
                <Button size="sm" asChild>
                  <Link href={buildLearningTaskHref(primaryTask)}>
                    {primaryTask.cta_label}
                    <ArrowRight className="ml-1.5 h-3.5 w-3.5" />
                  </Link>
                </Button>
                <Button size="sm" variant="outline" asChild>
                  <Link href="/learn">Open Learn</Link>
                </Button>
              </div>
            </div>
          </div>
        ) : (
          <div className="rounded-2xl border bg-background/80 p-4">
            <p className="text-sm text-muted-foreground">
              No learning block is queued yet. Open Learn to start a guide or
              choose a program path.
            </p>
            <Button size="sm" className="mt-3" asChild>
              <Link href="/learn">
                Open Learn
                <ArrowRight className="ml-1.5 h-3.5 w-3.5" />
              </Link>
            </Button>
          </div>
        )}

        {remainingTasks.length > 0 ? (
          <div className="space-y-2">
            <p className="text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground">
              Queue
            </p>
            <div className="space-y-2">
              {remainingTasks.map((task) => (
                <div
                  key={task.id}
                  className="flex items-center justify-between gap-3 rounded-xl border bg-background/60 px-3 py-3"
                >
                  <div className="min-w-0 space-y-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <p className="text-sm font-medium">{task.title}</p>
                      <Badge variant="outline" className="text-[10px]">
                        {learningTaskLabels[task.task_type]}
                      </Badge>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {task.detail}
                    </p>
                  </div>
                  <Button size="sm" variant="ghost" asChild>
                    <Link href={buildLearningTaskHref(task)}>
                      {task.cta_label}
                    </Link>
                  </Button>
                </div>
              ))}
            </div>
          </div>
        ) : null}

        {today?.focus_programs?.length ? (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground">
              <Route className="h-3.5 w-3.5" />
              Program paths
            </div>
            <div className="flex flex-wrap gap-2">
              {today.focus_programs.slice(0, 2).map((program) => {
                const programSignals = formatLearningProgramSignals(
                  program,
                ).slice(0, 2);

                return (
                  <Link
                    key={program.id}
                    href={`/learn?view=tree&program=${program.id}`}
                  >
                    <div
                      className="rounded-xl border px-3 py-2 text-sm transition-colors hover:border-primary/40"
                      style={{ borderColor: `${program.color}55` }}
                    >
                      <p className="font-medium">{program.title}</p>
                      <p className="text-xs text-muted-foreground">
                        {learningProgramStatusLabels[program.status]} •{" "}
                        {program.completed_guide_count}/
                        {program.total_guide_count} complete
                      </p>
                      {programSignals.length > 0 ? (
                        <div className="mt-2 flex flex-wrap gap-1">
                          {programSignals.map((signal) => (
                            <Badge
                              key={signal}
                              variant="outline"
                              className="text-[10px]"
                            >
                              {signal}
                            </Badge>
                          ))}
                        </div>
                      ) : null}
                    </div>
                  </Link>
                );
              })}
            </div>
          </div>
        ) : null}

        <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
          <BookOpen className="h-3.5 w-3.5" />
          <span>
            {stats?.guides_completed ?? 0} guide
            {stats?.guides_completed === 1 ? "" : "s"} completed so far
          </span>
        </div>
      </CardContent>
    </Card>
  );
}
