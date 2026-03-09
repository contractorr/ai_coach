export interface WatchlistTopic {
  id: string;
  label: string;
  kind: string;
  priority: string;
  why: string;
  updated_at: string;
}

export interface ThreadInboxSummary {
  id: string;
  label: string;
  entry_count: number;
  first_date: string;
  last_date: string;
  status: string;
  inbox_state: string;
  linked_goal_path?: string | null;
  linked_dossier_id?: string | null;
  last_action: string;
  recent_snippets: string[];
}

export interface ResearchDossier {
  dossier_id: string;
  topic: string;
  title?: string;
  status?: string;
  scope?: string;
  created?: string;
  updated?: string;
  last_updated?: string;
  update_count?: number;
  latest_change_summary?: string;
  open_questions?: string[];
}

export interface SavedFollowUp {
  url: string;
  title: string;
  saved: boolean;
  note: string;
  watchlist_ids: string[];
  created_at: string;
  updated_at: string;
}
