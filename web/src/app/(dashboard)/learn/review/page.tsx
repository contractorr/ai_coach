"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { toast } from "sonner";
import { ArrowLeft, CheckCircle } from "lucide-react";
import { useToken } from "@/hooks/useToken";
import { apiFetch } from "@/lib/api";
import { Button } from "@/components/ui/button";

import { ReviewCard } from "@/components/curriculum/ReviewCard";
import type { ReviewItem, ReviewSubmissionResult } from "@/types/curriculum";

export default function ReviewSessionPage() {
  const token = useToken();
  const searchParams = useSearchParams();
  const [items, setItems] = useState<ReviewItem[]>([]);
  const [current, setCurrent] = useState(0);
  const [loading, setLoading] = useState(true);
  const [grades, setGrades] = useState<number[]>([]);
  const [done, setDone] = useState(false);
  const mode = searchParams.get("mode") === "retry" ? "retry" : "due";
  const endpoint =
    mode === "retry"
      ? "/api/v1/curriculum/review/retry?limit=20"
      : "/api/v1/curriculum/review/due?limit=20";
  const pageTitle = mode === "retry" ? "Weak Item Retry" : "Review Session";
  const emptyTitle =
    mode === "retry" ? "No weak items to retry right now." : "Session complete!";

  useEffect(() => {
    if (!token) return;
    let cancelled = false;

    const loadItems = async () => {
      setLoading(true);
      setDone(false);
      setCurrent(0);
      setGrades([]);
      try {
        const data = await apiFetch<ReviewItem[]>(endpoint, {}, token);
        if (cancelled) return;
        setItems(data);
        if (data.length === 0) setDone(true);
      } catch (e) {
        if (!cancelled) toast.error((e as Error).message);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    void loadItems();
    return () => {
      cancelled = true;
    };
  }, [endpoint, token]);

  const handleGrade = async (
    reviewId: string,
    answer: string,
    selfGrade?: number
  ): Promise<ReviewSubmissionResult | null> => {
    if (!token) return;
    try {
      const result = await apiFetch<ReviewSubmissionResult>(
        `/api/v1/curriculum/review/${reviewId}/grade`,
        {
          method: "POST",
          body: JSON.stringify({
            answer,
            self_grade: selfGrade ?? null,
          }),
        },
        token
      );
      setGrades((prev) => [...prev, result.grade]);
      return result;
    } catch (e) {
      toast.error((e as Error).message);
      return null;
    }
  };

  const handleNext = () => {
    if (current + 1 >= items.length) {
      setDone(true);
    } else {
      setCurrent((prev) => prev + 1);
    }
  };

  if (loading) {
    return (
      <div className="max-w-2xl mx-auto space-y-4">
        <div className="h-6 w-32 animate-pulse rounded bg-muted" />
        <div className="h-64 animate-pulse rounded-lg bg-muted" />
      </div>
    );
  }

  const avgGrade =
    grades.length > 0
      ? (grades.reduce((a, b) => a + b, 0) / grades.length).toFixed(1)
      : "—";

  if (done) {
    return (
      <div className="max-w-2xl mx-auto text-center py-12 space-y-4">
        <CheckCircle className="mx-auto h-12 w-12 text-green-500" />
        <h2 className="text-xl font-semibold">{emptyTitle}</h2>
        <div className="flex justify-center gap-6 text-sm text-muted-foreground">
          <span>Reviewed: {grades.length}</span>
          <span>Avg grade: {avgGrade}/5</span>
        </div>
        <Link href="/learn">
          <Button className="mt-4">Back to Learn</Button>
        </Link>
      </div>
    );
  }

  const item = items[current];

  return (
    <div className="max-w-2xl mx-auto space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Link href="/learn">
            <Button variant="ghost" size="icon" className="h-8 w-8">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <h1 className="text-lg font-semibold">{pageTitle}</h1>
        </div>
        <span className="text-sm text-muted-foreground">
          {current + 1} / {items.length}
        </span>
      </div>

      {/* Progress bar */}
      <div className="h-1.5 rounded-full bg-muted overflow-hidden">
        <div
          className="h-full rounded-full bg-primary transition-all"
          style={{ width: `${((current + 1) / items.length) * 100}%` }}
        />
      </div>

      {item && (
        <ReviewCard
          key={item.id}
          item={item}
          onGrade={handleGrade}
          onNext={handleNext}
          nextLabel={current + 1 >= items.length ? "Finish session" : "Next item"}
          showAnswer
        />
      )}
    </div>
  );
}
