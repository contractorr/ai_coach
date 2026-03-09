export interface ChatAttachment {
  library_item_id: string;
  file_name?: string | null;
  mime_type?: string | null;
  index_status?: string | null;
  visibility_state?: string | null;
  warning?: string | null;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  advice_type?: string;
  attachments?: ChatAttachment[];
}
