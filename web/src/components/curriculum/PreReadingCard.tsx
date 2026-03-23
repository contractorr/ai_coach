"use client";

import { useEffect, useState } from "react";
import { ChevronDown, ChevronRight, Lightbulb } from "lucide-react";
import { useToken } from "@/hooks/useToken";
import { apiFetch } from "@/lib/api";

interface PreReadingQuestion {
  id: string;
  question: string;
}

interface PreReadingCardProps {
  chapterId: string;
  isCompleted: boolean;
}

export function PreReadingCard({ chapterId, isCompleted }: PreReadingCardProps) {
  const token = useToken();
  const [questions, setQuestions] = useState<PreReadingQuestion[]>([]);
  const [open, setOpen] = useState(false);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    if (!token || !chapterId) return;
    apiFetch<{ questions: PreReadingQuestion[] }>(
      `/api/curriculum/chapters/${chapterId}/pre-reading`,
      {},
      token
    )
      .then((data) => {
        setQuestions(data.questions ?? []);
        setLoaded(true);
      })
      .catch(() => setLoaded(true));
  }, [token, chapterId]);

  if (!loaded || questions.length === 0) return null;

  return (
    <div className="rounded-lg border bg-amber-50/50 dark:bg-amber-950/20">
      <button
        className="flex w-full items-center gap-2 px-4 py-3 text-left text-sm font-medium"
        onClick={() => setOpen(!open)}
      >
        {open ? (
          <ChevronDown className="h-3.5 w-3.5 text-amber-600" />
        ) : (
          <ChevronRight className="h-3.5 w-3.5 text-amber-600" />
        )}
        <Lightbulb className="h-3.5 w-3.5 text-amber-600" />
        {isCompleted ? "Check your understanding" : "Before you read"}
      </button>
      {open && (
        <ul className="space-y-2 px-4 pb-4 pl-11">
          {questions.map((q) => (
            <li
              key={q.id}
              className="text-sm text-muted-foreground leading-relaxed"
            >
              {q.question}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
