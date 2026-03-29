"use client";

import { useEffect, useState } from "react";
import { apiFetch } from "@/lib/api";
import { useToken } from "@/hooks/useToken";
import type { LearningStats, LearningToday } from "@/types/curriculum";

export interface HomeStats {
  learningStats: LearningStats | null;
  learningToday: LearningToday | null;
  loading: boolean;
}

export function useHomeStats(): HomeStats {
  const token = useToken();
  const [learningStats, setLearningStats] = useState<LearningStats | null>(null);
  const [learningToday, setLearningToday] = useState<LearningToday | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;

    const fetchAll = async () => {
      try {
        const [curriculumStats, curriculumToday] = await Promise.all([
          apiFetch<LearningStats>("/api/v1/curriculum/stats", {}, token).catch(() => null),
          apiFetch<LearningToday>("/api/v1/curriculum/today", {}, token).catch(() => null),
        ]);
        if (cancelled) return;
        setLearningStats(curriculumStats);
        setLearningToday(curriculumToday);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    void fetchAll();
    return () => { cancelled = true; };
  }, [token]);

  return { learningStats, learningToday, loading };
}
