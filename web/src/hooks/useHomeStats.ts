"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import { useToken } from "@/hooks/useToken";

interface JournalEntryStub {
  path: string;
  created: string | null;
}

interface GoalStub {
  path: string;
  status: string;
}

interface ThreadStub {
  id: string;
}

export interface HomeStats {
  journalEntries: JournalEntryStub[];
  activeGoals: number;
  threadCount: number;
  loading: boolean;
}

export function useHomeStats(): HomeStats {
  const token = useToken();
  const [journalEntries, setJournalEntries] = useState<JournalEntryStub[]>([]);
  const [activeGoals, setActiveGoals] = useState(0);
  const [threadCount, setThreadCount] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;

    const fetchAll = async () => {
      try {
        const [entries, goals, threads] = await Promise.all([
          apiFetch<JournalEntryStub[]>("/api/journal?limit=200", {}, token).catch(() => []),
          apiFetch<GoalStub[]>("/api/goals", {}, token).catch(() => []),
          apiFetch<ThreadStub[]>("/api/threads/inbox?limit=50", {}, token).catch(() => []),
        ]);
        if (cancelled) return;
        setJournalEntries(entries);
        setActiveGoals(goals.filter((g) => g.status === "active").length);
        setThreadCount(threads.length);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    void fetchAll();
    return () => { cancelled = true; };
  }, [token]);

  return { journalEntries, activeGoals, threadCount, loading };
}
