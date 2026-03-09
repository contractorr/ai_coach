export interface LibraryReportListItem {
  id: string;
  title: string;
  report_type: string;
  status: "ready" | "archived";
  collection?: string | null;
  prompt: string;
  source_kind: string;
  created: string;
  updated: string;
  last_generated_at: string;
  preview: string;
  file_name?: string | null;
  file_size?: number | null;
  mime_type?: string | null;
  has_attachment: boolean;
  extraction_status?: string | null;
  has_extracted_text?: boolean;
  origin_surface?: string;
  visibility_state?: string;
  index_status?: string | null;
  extracted_chars?: number;
}

export interface LibraryReport extends LibraryReportListItem {
  content: string;
}

export interface ChatAttachmentUpload {
  attachment_id: string;
  file_name?: string | null;
  mime_type?: string | null;
  index_status: string;
  visibility_state: string;
  extracted_chars: number;
  warning?: string | null;
}
