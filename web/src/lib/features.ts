import { BookOpen, GraduationCap, Newspaper, Sparkles, Target } from "lucide-react";
import type { LucideIcon } from "lucide-react";

export interface Feature {
  icon: LucideIcon;
  title: string;
  description: string;
}

export const FEATURES: Feature[] = [
  {
    icon: Newspaper,
    title: "Intelligence Radar",
    description:
      "Scans HN, GitHub, arXiv, Reddit & RSS — surfaces what matters, skips the noise.",
  },
  {
    icon: GraduationCap,
    title: "Personal Tutor",
    description:
      "50+ structured guides with spaced repetition, teach-back prompts, and Bloom's taxonomy quizzes.",
  },
  {
    icon: Sparkles,
    title: "AI Steward",
    description:
      "Personalized guidance grounded in your journal, learning progress, goals, and real-time intel.",
  },
  {
    icon: Target,
    title: "Goal Tracking",
    description:
      "Track objectives with milestones. Get nudged when priorities should shift.",
  },
  {
    icon: BookOpen,
    title: "Journal",
    description:
      "Capture reflections and decisions. Every entry sharpens your tutor's guidance.",
  },
];
