"use client";

import { useMemo } from "react";

interface Props {
  entries: Array<{ created: string | null }>;
}

const DAY_MS = 86_400_000;
const DOW_LABELS = ["", "Mon", "", "Wed", "", "Fri", ""];
const MONTH_SHORT = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

function levelClass(count: number) {
  if (count === 0) return "bg-muted/40";
  if (count === 1) return "bg-primary/25";
  if (count === 2) return "bg-primary/55";
  return "bg-primary/90";
}

function startOfDay(d: Date) {
  return new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime();
}

export function ActivityHeatmap({ entries }: Props) {
  const { cells, streak, monthLabels } = useMemo(() => {
    const today = new Date();
    const todayTs = startOfDay(today);
    const totalDays = 84; // 12 weeks

    // Build counts per day
    const counts = new Map<number, number>();
    for (const e of entries) {
      if (!e.created) continue;
      const ts = startOfDay(new Date(e.created));
      counts.set(ts, (counts.get(ts) ?? 0) + 1);
    }

    const endTs = todayTs;
    const startTs = endTs - (totalDays - 1) * DAY_MS;

    // Adjust so first column starts on Monday
    const firstDate = new Date(startTs);
    const firstDow = firstDate.getDay();
    const adjustedStart = firstDow === 1 ? startTs : startTs - ((firstDow === 0 ? 6 : firstDow - 1)) * DAY_MS;

    const cellData: Array<{ date: Date; count: number; ts: number }> = [];
    let cursor = adjustedStart;
    while (cursor <= endTs) {
      const d = new Date(cursor);
      cellData.push({ date: d, count: counts.get(cursor) ?? 0, ts: cursor });
      cursor += DAY_MS;
    }

    // Streak: count consecutive days with entries ending today (or yesterday)
    let streakCount = 0;
    let checkTs = todayTs;
    // Allow today to not have entry yet — start from yesterday if today is empty
    if (!counts.has(checkTs)) {
      checkTs -= DAY_MS;
    }
    while (counts.has(checkTs)) {
      streakCount++;
      checkTs -= DAY_MS;
    }

    // Month labels for the top row
    const labels: Array<{ label: string; col: number }> = [];
    let lastMonth = -1;
    const numWeeks = Math.ceil(cellData.length / 7);
    for (let w = 0; w < numWeeks; w++) {
      const idx = w * 7;
      if (idx >= cellData.length) break;
      const m = cellData[idx].date.getMonth();
      if (m !== lastMonth) {
        labels.push({ label: MONTH_SHORT[m], col: w });
        lastMonth = m;
      }
    }

    return { cells: cellData, streak: streakCount, monthLabels: labels };
  }, [entries]);

  const numWeeks = Math.ceil(cells.length / 7);

  return (
    <div className="space-y-2">
      {/* Month labels */}
      <div className="flex pl-8">
        <div className="relative h-4 flex-1">
          {monthLabels.map(({ label, col }) => (
            <span
              key={`${label}-${col}`}
              className="absolute text-[10px] text-muted-foreground"
              style={{ left: `${(col / numWeeks) * 100}%` }}
            >
              {label}
            </span>
          ))}
        </div>
      </div>

      {/* Grid */}
      <div className="flex gap-1">
        {/* Day-of-week labels */}
        <div className="grid grid-rows-7 gap-1">
          {DOW_LABELS.map((label, i) => (
            <div key={i} className="flex h-3 w-6 items-center justify-end pr-1 text-[10px] text-muted-foreground">
              {label}
            </div>
          ))}
        </div>

        {/* Heatmap cells — hide early weeks on mobile */}
        <div className="grid grid-flow-col grid-rows-7 gap-1">
          {cells.map(({ date, count, ts }, i) => {
            const weekIdx = Math.floor(i / 7);
            const hideOnMobile = weekIdx < numWeeks - 8;
            return (
              <div
                key={ts}
                title={`${date.toLocaleDateString("en-US", { month: "short", day: "numeric" })}: ${count} ${count === 1 ? "entry" : "entries"}`}
                className={`h-3 w-3 rounded-sm ${levelClass(count)} ${hideOnMobile ? "hidden md:block" : ""}`}
              />
            );
          })}
        </div>
      </div>

      {/* Streak */}
      <p className="text-xs text-muted-foreground">
        {streak > 0
          ? `${streak}-day streak`
          : "Start your streak today"}
      </p>
    </div>
  );
}
