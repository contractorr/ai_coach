export interface GreetingResponse {
  text: string;
  cached: boolean;
  stale: boolean;
  return_brief?: {
    active: boolean;
    absent_hours: number;
    summary: string;
    sections: Array<{ kind: string; items: Array<Record<string, unknown>> }>;
    next_steps: Array<{ kind: string; label: string; target: string }>;
    generated_at: string;
  } | null;
}
