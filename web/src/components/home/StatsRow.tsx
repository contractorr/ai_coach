"use client";

import Link from "next/link";
import { BookOpen, Flame, RotateCcw, Target } from "lucide-react";
import { useMemo } from "react";
import type { LearningStats } from "@/types/curriculum";

interface Props {
  journalEntries: Array<{ created: string | null }>;
  activeGoals: number;
  learningStats: LearningStats | null;
  loading: boolean;
}

function thisWeekCount(entries: Array<{ created: string | null }>): number {
  const now = new Date();
  const day = now.getDay();
  const mondayOffset = day === 0 ? 6 : day - 1;
  const monday = new Date(now.getFullYear(), now.getMonth(), now.getDate() - mondayOffset);
  const mondayTs = monday.getTime();
  return entries.filter((e) => e.created && new Date(e.created).getTime() >= mondayTs).length;
}

export function StatsRow({ journalEntries, activeGoals, learningStats, loading }: Props) {
  const weekCount = useMemo(() => thisWeekCount(journalEntries), [journalEntries]);
  const reviewsHref = (learningStats?.reviews_due ?? 0) > 0 ? "/learn/review" : "/learn";

  const pills = [
    { icon: BookOpen, label: `${weekCount} journaled this week`, key: "journal", href: "/journal" },
    { icon: Target, label: `${activeGoals} active goals`, key: "goals", href: "/goals" },
    {
      icon: Flame,
      label: `${learningStats?.current_streak_days ?? 0}d learning streak`,
      key: "learning_streak",
      href: "/learn",
    },
    {
      icon: RotateCcw,
      label: `${learningStats?.reviews_due ?? 0} reviews due`,
      key: "reviews_due",
      href: reviewsHref,
    },
  ];

  if (loading) {
    return (
      <div className="flex flex-wrap gap-2">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="h-7 w-24 animate-pulse rounded-full bg-muted/40" />
        ))}
      </div>
    );
  }

  return (
    <div className="flex flex-wrap gap-2">
      {pills.map(({ icon: Icon, label, key, href }) => (
        <Link
          key={key}
          href={href}
          className="inline-flex items-center gap-1.5 rounded-full border bg-card/70 px-3 py-1 text-xs backdrop-blur"
        >
          <Icon className="h-3 w-3 text-muted-foreground" />
          {label}
        </Link>
      ))}
    </div>
  );
}
