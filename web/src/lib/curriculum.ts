import type {
  LearningProgramFocus,
  LearningProgramFocusStatus,
  LearningTodayTask,
  RecommendationType,
} from "@/types/curriculum";

export const recommendationLabels: Record<
  RecommendationType | "fallback",
  string
> = {
  continue: "Continue",
  enrolled: "Enrolled",
  ready: "Unlocked",
  entry: "Entry point",
  fallback: "Next step",
};

export const learningTaskLabels: Record<
  LearningTodayTask["task_type"],
  string
> = {
  continue_chapter: "Continue",
  due_reviews: "Review",
  retry_reviews: "Retry",
  start_guide: "Start",
  applied_practice: "Apply",
};

export const learningProgramStatusLabels: Record<
  LearningProgramFocusStatus,
  string
> = {
  active: "Active path",
  recommended: "Recommended path",
  available: "Available path",
};

export function formatLearningMinutes(minutes: number): string {
  if (minutes <= 0) {
    return "5m";
  }
  if (minutes < 60) {
    return `${minutes}m`;
  }
  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;
  return remainingMinutes > 0 ? `${hours}h ${remainingMinutes}m` : `${hours}h`;
}

export function formatLearningSeconds(seconds: number): string {
  return formatLearningMinutes(Math.max(0, Math.round(seconds / 60)));
}

export function buildLearningTaskHref(task: LearningTodayTask): string {
  if (task.entry_path) {
    return `/journal?open=${encodeURIComponent(task.entry_path)}`;
  }
  if (task.task_type === "retry_reviews") {
    return "/learn/review?mode=retry";
  }
  if (task.task_type === "due_reviews") {
    return "/learn/review";
  }
  if (task.guide_id && task.chapter_id) {
    return `/learn/${task.guide_id}/${task.chapter_id.split("/").pop()}`;
  }
  if (task.guide_id) {
    return `/learn/${task.guide_id}`;
  }
  return "/learn";
}

export function formatLearningProgramSignals(
  program: LearningProgramFocus,
): string[] {
  const signals: string[] = [];

  if ((program.revision_backlog_count ?? 0) > 0) {
    signals.push(
      `${program.revision_backlog_count} revision${
        program.revision_backlog_count === 1 ? "" : "s"
      }`,
    );
  }

  if ((program.weak_review_count ?? 0) > 0) {
    signals.push(
      `${program.weak_review_count} weak item${program.weak_review_count === 1 ? "" : "s"}`,
    );
  }

  if (typeof program.average_assessment_grade === "number") {
    signals.push(`Avg ${program.average_assessment_grade.toFixed(1)}/5`);
  } else if ((program.submitted_assessment_count ?? 0) > 0) {
    signals.push(
      `${program.submitted_assessment_count} submitted assessment${
        program.submitted_assessment_count === 1 ? "" : "s"
      }`,
    );
  }

  return signals;
}
