"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { toast } from "sonner";
import { ArrowLeft, CheckCircle } from "lucide-react";
import { useToken } from "@/hooks/useToken";
import { apiFetch } from "@/lib/api";
import { Button } from "@/components/ui/button";

import { ReviewCard } from "@/components/curriculum/ReviewCard";
import type { ReviewItem, ReviewSubmissionResult } from "@/types/curriculum";

function mergeReviewQueues(retryItems: ReviewItem[], dueItems: ReviewItem[]): ReviewItem[] {
  const merged = new Map<string, ReviewItem>();
  for (const item of [...retryItems, ...dueItems]) {
    if (!merged.has(item.id)) {
      merged.set(item.id, item);
    }
  }
  return Array.from(merged.values()).slice(0, 20);
}

export default function ReviewSessionPage() {
  const token = useToken();
  const [items, setItems] = useState<ReviewItem[]>([]);
  const [current, setCurrent] = useState(0);
  const [loading, setLoading] = useState(true);
  const [grades, setGrades] = useState<number[]>([]);
  const [done, setDone] = useState(false);

  useEffect(() => {
    if (!token) return;
    let cancelled = false;

    const loadItems = async () => {
      setLoading(true);
      setDone(false);
      setCurrent(0);
      setGrades([]);
      try {
        const [retryItems, dueItems] = await Promise.all([
          apiFetch<ReviewItem[]>("/api/v1/curriculum/review/retry?limit=20", {}, token).catch(
            () => [],
          ),
          apiFetch<ReviewItem[]>("/api/v1/curriculum/review/due?limit=20", {}, token).catch(
            () => [],
          ),
        ]);
        const data = mergeReviewQueues(retryItems, dueItems);
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
  }, [token]);

  const handleGrade = async (
    reviewId: string,
    answer: string,
    selfGrade?: number,
  ): Promise<ReviewSubmissionResult | null> => {
    if (!token) return null;
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
        token,
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
      ? (grades.reduce((left, right) => left + right, 0) / grades.length).toFixed(1)
      : "—";

  if (done) {
    return (
      <div className="max-w-2xl mx-auto space-y-4 py-12 text-center">
        <CheckCircle className="mx-auto h-12 w-12 text-green-500" />
        <h2 className="text-xl font-semibold">
          {grades.length > 0 ? "Review complete" : "No reviews due right now"}
        </h2>
        {grades.length > 0 ? (
          <div className="flex justify-center gap-6 text-sm text-muted-foreground">
            <span>Reviewed: {grades.length}</span>
            <span>Avg grade: {avgGrade}/5</span>
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">
            Finish another chapter and new review items will show up here.
          </p>
        )}
        <Link href="/learn">
          <Button className="mt-4">Back to Guide Library</Button>
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
          <h1 className="text-lg font-semibold">Review</h1>
        </div>
        <span className="text-sm text-muted-foreground">
          {current + 1} / {items.length}
        </span>
      </div>

      <div className="h-1.5 overflow-hidden rounded-full bg-muted">
        <div
          className="h-full rounded-full bg-primary transition-all"
          style={{ width: `${((current + 1) / items.length) * 100}%` }}
        />
      </div>

      {item ? (
        <ReviewCard
          key={item.id}
          item={item}
          onGrade={handleGrade}
          onNext={handleNext}
          nextLabel={current + 1 >= items.length ? "Finish session" : "Next item"}
          showAnswer
        />
      ) : null}
    </div>
  );
}
