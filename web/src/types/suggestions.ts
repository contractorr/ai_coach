export interface SuggestionItem {
  source: string;
  kind: string;
  title: string;
  description: string;
  action: string;
  priority: number;
  score: number;
  why_now?: Array<{
    code: string;
    label: string;
    severity: string;
    detail?: Record<string, unknown>;
  }> | null;
  payload?: Record<string, unknown> | null;
}
