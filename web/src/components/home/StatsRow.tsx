"use client";

import { BookOpen, MessageSquare, Target } from "lucide-react";
import { useMemo } from "react";

interface Props {
  journalEntries: Array<{ created: string | null }>;
  activeGoals: number;
  threadCount: number;
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

export function StatsRow({ journalEntries, activeGoals, threadCount, loading }: Props) {
  const weekCount = useMemo(() => thisWeekCount(journalEntries), [journalEntries]);

  const pills = [
    { icon: BookOpen, label: `${weekCount} this week`, key: "journal" },
    { icon: Target, label: `${activeGoals} active`, key: "goals" },
    { icon: MessageSquare, label: `${threadCount} threads`, key: "threads" },
  ];

  if (loading) {
    return (
      <div className="flex flex-wrap gap-2">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="h-7 w-24 animate-pulse rounded-full bg-muted/40" />
        ))}
      </div>
    );
  }

  return (
    <div className="flex flex-wrap gap-2">
      {pills.map(({ icon: Icon, label, key }) => (
        <span
          key={key}
          className="inline-flex items-center gap-1.5 rounded-full border bg-card/70 px-3 py-1 text-xs backdrop-blur"
        >
          <Icon className="h-3 w-3 text-muted-foreground" />
          {label}
        </span>
      ))}
    </div>
  );
}
