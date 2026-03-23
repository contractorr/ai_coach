"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { toast } from "sonner";
import { ArrowLeft, CheckCircle } from "lucide-react";
import { useToken } from "@/hooks/useToken";
import { apiFetch } from "@/lib/api";
import { Button } from "@/components/ui/button";

import { ReviewCard } from "@/components/curriculum/ReviewCard";
import type { ReviewItem } from "@/types/curriculum";

export default function ReviewSessionPage() {
  const token = useToken();
  const [items, setItems] = useState<ReviewItem[]>([]);
  const [current, setCurrent] = useState(0);
  const [loading, setLoading] = useState(true);
  const [grades, setGrades] = useState<number[]>([]);
  const [done, setDone] = useState(false);

  useEffect(() => {
    if (!token) return;
    setLoading(true);
    apiFetch<ReviewItem[]>("/api/curriculum/review/due?limit=20", {}, token)
      .then((data) => {
        setItems(data);
        if (data.length === 0) setDone(true);
      })
      .catch((e) => toast.error((e as Error).message))
      .finally(() => setLoading(false));
  }, [token]);

  const handleGrade = async (
    reviewId: string,
    answer: string,
    selfGrade?: number
  ) => {
    if (!token) return;
    try {
      const result = await apiFetch<{ grade: number }>(
        `/api/curriculum/review/${reviewId}/grade`,
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

      // Move to next or finish
      if (current + 1 >= items.length) {
        setDone(true);
      } else {
        setCurrent((prev) => prev + 1);
      }
    } catch (e) {
      toast.error((e as Error).message);
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
        <h2 className="text-xl font-semibold">Session complete!</h2>
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
          <h1 className="text-lg font-semibold">Review Session</h1>
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

      {item && <ReviewCard item={item} onGrade={handleGrade} showAnswer />}
    </div>
  );
}
