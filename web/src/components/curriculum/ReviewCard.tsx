"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import type {
  ReviewItem,
  ReviewItemType,
  ReviewSubmissionResult,
} from "@/types/curriculum";

const gradeLabels = ["Blackout", "Incorrect", "Hard", "Okay", "Good", "Perfect"];

const gradeColors = [
  "bg-red-500",
  "bg-red-400",
  "bg-orange-400",
  "bg-yellow-400",
  "bg-green-400",
  "bg-green-500",
];

interface ReviewCardProps {
  item: ReviewItem;
  onGrade: (
    reviewId: string,
    answer: string,
    selfGrade?: number
  ) => Promise<ReviewSubmissionResult | null>;
  onNext: () => void;
  nextLabel: string;
  showAnswer?: boolean;
}

export function ReviewCard({
  item,
  onGrade,
  onNext,
  nextLabel,
  showAnswer = false,
}: ReviewCardProps) {
  const isTeachback =
    (item as ReviewItem & { item_type?: ReviewItemType }).item_type === "teachback";
  const isQuickRecall = !isTeachback && ["remember", "understand"].includes(item.bloom_level);
  const [answer, setAnswer] = useState("");
  const [grading, setGrading] = useState(false);
  const [showSelfGrade, setShowSelfGrade] = useState(false);
  const [revealed, setRevealed] = useState(false);
  const [useWrittenAnswer, setUseWrittenAnswer] = useState(false);
  const [result, setResult] = useState<ReviewSubmissionResult | null>(null);

  const handleSubmit = async () => {
    setGrading(true);
    try {
      const gradeResult = await onGrade(item.id, answer);
      setResult(gradeResult);
    } finally {
      setGrading(false);
    }
  };

  const handleSelfGrade = async (grade: number) => {
    setGrading(true);
    try {
      const gradeResult = await onGrade(item.id, answer, grade);
      setResult(gradeResult);
    } finally {
      setGrading(false);
    }
  };

  const correctPoints = result?.correct_points ?? [];
  const missingPoints = result?.missing_points ?? [];
  const hasStructuredFeedback =
    Boolean(result?.feedback) || correctPoints.length > 0 || missingPoints.length > 0;

  return (
    <div className="space-y-4 rounded-lg border bg-card p-4">
      <div className="flex items-start justify-between gap-2">
        <p className="text-sm font-medium leading-relaxed">{item.question}</p>
        <div className="flex shrink-0 gap-1">
          {isTeachback && (
            <Badge className="bg-violet-100 text-[10px] text-violet-800 dark:bg-violet-900/40 dark:text-violet-300">
              Teach-back
            </Badge>
          )}
          <Badge variant="outline" className="text-[10px] capitalize">
            {item.bloom_level}
          </Badge>
        </div>
      </div>
      {isTeachback && <p className="text-xs text-muted-foreground">Explain in your own words</p>}

      {!result ? (
        <div className="space-y-3">
          {isQuickRecall && !useWrittenAnswer ? (
            <>
              <div className="rounded-md border bg-muted/30 p-3">
                <p className="text-sm text-muted-foreground">
                  Try to recall the answer before revealing it, then grade how well you remembered it.
                </p>
              </div>
              {!revealed ? (
                <div className="flex flex-wrap items-center gap-2">
                  <Button size="sm" onClick={() => setRevealed(true)}>
                    Reveal answer
                  </Button>
                  <Button size="sm" variant="ghost" onClick={() => setUseWrittenAnswer(true)}>
                    Type instead
                  </Button>
                </div>
              ) : (
                <div className="space-y-3">
                  <div className="rounded-md border-l-2 border-primary/40 bg-primary/5 p-3">
                    <p className="mb-1 text-xs font-medium text-muted-foreground">
                      Expected answer:
                    </p>
                    <p className="text-sm">{item.expected_answer}</p>
                  </div>
                  <div className="space-y-2">
                    <p className="text-xs font-medium uppercase tracking-wide text-foreground/80">
                      How well did you recall it?
                    </p>
                    <div className="flex flex-wrap gap-1.5">
                      {gradeLabels.map((label, i) => (
                        <Button
                          key={i}
                          size="sm"
                          variant="outline"
                          className="text-xs"
                          onClick={() => handleSelfGrade(i)}
                          disabled={grading}
                        >
                          <span className={`mr-1.5 h-2 w-2 rounded-full ${gradeColors[i]}`} />
                          {i} - {label}
                        </Button>
                      ))}
                    </div>
                  </div>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => {
                      setUseWrittenAnswer(true);
                      setShowSelfGrade(false);
                    }}
                  >
                    Type an answer instead
                  </Button>
                </div>
              )}
            </>
          ) : (
            <>
              <Textarea
                value={answer}
                onChange={(e) => setAnswer(e.target.value)}
                placeholder={isTeachback ? "Explain in your own words..." : "Type your answer..."}
                rows={isTeachback ? 6 : 3}
                className="text-sm"
              />
              <div className="flex items-center gap-2">
                <Button size="sm" onClick={handleSubmit} disabled={!answer.trim() || grading}>
                  {grading ? "Grading..." : "Submit"}
                </Button>
                {!isQuickRecall ? (
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => setShowSelfGrade(!showSelfGrade)}
                  >
                    Self-grade
                  </Button>
                ) : (
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => {
                      setUseWrittenAnswer(false);
                      setRevealed(false);
                    }}
                  >
                    Switch to reveal
                  </Button>
                )}
              </div>
              {showSelfGrade && (
                <div className="flex flex-wrap gap-1.5">
                  {gradeLabels.map((label, i) => (
                    <Button
                      key={i}
                      size="sm"
                      variant="outline"
                      className="text-xs"
                      onClick={() => handleSelfGrade(i)}
                      disabled={grading}
                    >
                      <span className={`mr-1.5 h-2 w-2 rounded-full ${gradeColors[i]}`} />
                      {i} - {label}
                    </Button>
                  ))}
                </div>
              )}
            </>
          )}
        </div>
      ) : (
        <div className="space-y-3 rounded-md border bg-muted/40 p-3">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant={result.grade >= 4 ? "default" : "outline"} className="text-xs">
              Grade: {result.grade} / 5
            </Badge>
            {result.feedback && <p className="text-sm text-muted-foreground">{result.feedback}</p>}
          </div>
          {!hasStructuredFeedback ? (
            <p className="text-sm text-muted-foreground">
              Saved to your review schedule. Keep moving while the answer is still fresh.
            </p>
          ) : null}
          {correctPoints.length > 0 && (
            <div className="space-y-1">
              <p className="text-xs font-medium uppercase tracking-wide text-foreground/80">
                Strong points
              </p>
              <ul className="ml-5 list-disc space-y-1 text-sm text-muted-foreground">
                {correctPoints.map((point) => (
                  <li key={point}>{point}</li>
                ))}
              </ul>
            </div>
          )}
          {missingPoints.length > 0 && (
            <div className="space-y-1">
              <p className="text-xs font-medium uppercase tracking-wide text-foreground/80">
                Missing points
              </p>
              <ul className="ml-5 list-disc space-y-1 text-sm text-muted-foreground">
                {missingPoints.map((point) => (
                  <li key={point}>{point}</li>
                ))}
              </ul>
            </div>
          )}
          <div className="flex items-center gap-2">
            <Button size="sm" onClick={onNext}>
              {nextLabel}
            </Button>
          </div>
        </div>
      )}

      {showAnswer && result && (
        <div className="rounded-md border-l-2 border-primary/40 bg-primary/5 p-3">
          <p className="mb-1 text-xs font-medium text-muted-foreground">Expected answer:</p>
          <p className="text-sm">{item.expected_answer}</p>
        </div>
      )}
    </div>
  );
}
