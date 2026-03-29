import { BookOpen, Brain, Newspaper, Target } from "lucide-react";
import type { LucideIcon } from "lucide-react";

export interface Feature {
  icon: LucideIcon;
  title: string;
  description: string;
}

export const FEATURES: Feature[] = [
  {
    icon: Newspaper,
    title: "Radar",
    description:
      "Follow the few changes worth your attention across the sources you care about.",
  },
  {
    icon: Brain,
    title: "Guidance",
    description:
      "Ask for grounded advice shaped by your notes, goals, and live signals.",
  },
  {
    icon: Target,
    title: "Goals",
    description:
      "Turn priorities into milestones and keep your next steps visible.",
  },
  {
    icon: BookOpen,
    title: "Guide Library",
    description:
      "Work through practical guides and return for reviews when you need them.",
  },
];
