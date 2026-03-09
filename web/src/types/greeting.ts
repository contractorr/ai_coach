export interface ReturnBriefSection {
  kind: string;
  items: Array<Record<string, unknown>>;
}

export interface ReturnBriefNextStep {
  kind: string;
  label: string;
  target: string;
}

export interface ReturnBrief {
  active: boolean;
  absent_hours: number;
  summary: string;
  sections: ReturnBriefSection[];
  next_steps: ReturnBriefNextStep[];
  generated_at: string;
}

export interface GreetingResponse {
  text: string;
  cached: boolean;
  stale: boolean;
  return_brief?: ReturnBrief | null;
}
