"use client";

import { useEffect, useState } from "react";
import { GraduationCap, Send, X } from "lucide-react";
import { toast } from "sonner";
import { useToken } from "@/hooks/useToken";
import { apiFetch } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";

interface TeachBackData {
  concept: string;
  prompt: string;
  review_item_id: string;
}

interface GradeResult {
  grade: number;
  feedback: string;
  correct_points: string[];
  missing_points: string[];
}

interface TeachBackCardProps {
  chapterId: string;
}

export function TeachBackCard({ chapterId }: TeachBackCardProps) {
  const token = useToken();
  const [data, setData] = useState<TeachBackData | null>(null);
  const [loading, setLoading] = useState(true);
  const [answer, setAnswer] = useState("");
  const [grading, setGrading] = useState(false);
  const [result, setResult] = useState<GradeResult | null>(null);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    if (!token || !chapterId) return;
    apiFetch<TeachBackData>(
      `/api/curriculum/teachback/${chapterId}/generate`,
      { method: "POST" },
      token
    )
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [token, chapterId]);

  const handleSubmit = async () => {
    if (!token || !data || !answer.trim()) return;
    setGrading(true);
    try {
      const res = await apiFetch<GradeResult>(
        `/api/curriculum/teachback/${data.review_item_id}/grade`,
        {
          method: "POST",
          body: JSON.stringify({ answer }),
        },
        token
      );
      setResult(res);
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setGrading(false);
    }
  };

  if (dismissed || loading || !data) return null;

  return (
    <div className="rounded-lg border border-violet-200 bg-violet-50/50 dark:border-violet-800 dark:bg-violet-950/20 p-4 space-y-3">
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <GraduationCap className="h-4 w-4 text-violet-600 shrink-0" />
          <p className="text-sm font-medium">Teach-back</p>
        </div>
        <Button
          variant="ghost"
          size="icon"
          className="h-6 w-6"
          onClick={() => setDismissed(true)}
        >
          <X className="h-3.5 w-3.5" />
        </Button>
      </div>

      <p className="text-sm leading-relaxed">{data.prompt}</p>

      {!result ? (
        <div className="space-y-3">
          <Textarea
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            placeholder="Explain in your own words..."
            rows={6}
            className="text-sm"
          />
          <Button
            size="sm"
            onClick={handleSubmit}
            disabled={!answer.trim() || grading}
          >
            <Send className="mr-1.5 h-3.5 w-3.5" />
            {grading ? "Grading..." : "Submit explanation"}
          </Button>
        </div>
      ) : (
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <Badge
              variant="outline"
              className={
                result.grade >= 4
                  ? "border-green-500 text-green-700"
                  : result.grade >= 2
                    ? "border-yellow-500 text-yellow-700"
                    : "border-red-500 text-red-700"
              }
            >
              Grade: {result.grade}/5
            </Badge>
          </div>
          {result.feedback && (
            <p className="text-sm text-muted-foreground">{result.feedback}</p>
          )}
          {result.correct_points.length > 0 && (
            <div>
              <p className="text-xs font-medium text-green-700 mb-1">Got right:</p>
              <ul className="text-xs text-muted-foreground space-y-0.5">
                {result.correct_points.map((p, i) => (
                  <li key={i}>+ {p}</li>
                ))}
              </ul>
            </div>
          )}
          {result.missing_points.length > 0 && (
            <div>
              <p className="text-xs font-medium text-amber-700 mb-1">Could improve:</p>
              <ul className="text-xs text-muted-foreground space-y-0.5">
                {result.missing_points.map((p, i) => (
                  <li key={i}>- {p}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
