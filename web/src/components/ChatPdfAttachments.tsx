"use client";

import { useCallback, useRef, useState } from "react";
import { toast } from "sonner";
import { CheckCircle2, FileText, LoaderCircle, Paperclip, Save, TriangleAlert, X } from "lucide-react";
import { apiFetch } from "@/lib/api";
import type { ChatAttachmentUpload } from "@/types/library";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { PendingChatPdfAttachment } from "@/hooks/useChatPdfAttachments";
import type { ChatAttachment } from "@/types/chat";

function statusTone(status?: string | null): "secondary" | "outline" | "destructive" {
  if (status === "limited_text") return "outline";
  if (status === "failed") return "destructive";
  return "secondary";
}

function statusLabel(status?: string | null): string | null {
  switch (status) {
    case "pending":
      return "Ready when sent";
    case "uploading":
      return "Uploading";
    case "ready":
      return "Ready to use";
    case "limited_text":
      return "Limited text extracted";
    case "failed":
      return "Upload failed";
    default:
      return null;
  }
}

function AttachmentStatusIcon({ status }: { status?: string | null }) {
  if (status === "uploading") return <LoaderCircle className="h-3 w-3 animate-spin" />;
  if (status === "limited_text" || status === "failed") {
    return <TriangleAlert className="h-3 w-3" />;
  }
  if (status === "ready") return <CheckCircle2 className="h-3 w-3" />;
  return <FileText className="h-3 w-3" />;
}

export function ChatAttachmentBadges({
  attachments,
  className = "mb-2",
  token,
}: {
  attachments?: ChatAttachment[];
  className?: string;
  token?: string;
}) {
  const [savingId, setSavingId] = useState<string | null>(null);
  const [savedIds, setSavedIds] = useState<Record<string, boolean>>({});

  const handleSave = useCallback(
    async (attachment: ChatAttachment) => {
      if (!token) {
        toast.error("You need to be signed in to save attachments.");
        return;
      }
      setSavingId(attachment.library_item_id);
      try {
        await apiFetch<ChatAttachmentUpload>(
          `/api/v1/advisor/attachments/${encodeURIComponent(attachment.library_item_id)}/save`,
          { method: "POST" },
          token,
        );
        setSavedIds((current) => ({ ...current, [attachment.library_item_id]: true }));
        toast.success("Saved to Research");
      } catch (error) {
        toast.error(error instanceof Error ? error.message : "Failed to save attachment.");
      } finally {
        setSavingId(null);
      }
    },
    [token],
  );

  if (!attachments?.length) return null;

  return (
    <div className={`${className} space-y-2`}>
      {attachments.map((attachment) => {
        const saved = savedIds[attachment.library_item_id] || attachment.visibility_state === "saved";
        const label = statusLabel(attachment.index_status);
        return (
          <div
            key={`${attachment.library_item_id}-${attachment.file_name || "pdf"}`}
            className="flex flex-wrap items-center gap-2 rounded-lg border bg-background/70 px-2.5 py-2"
          >
            <Badge variant="outline" className="max-w-full gap-1.5">
              <FileText className="h-3 w-3" />
              <span className="truncate">{attachment.file_name || "PDF document"}</span>
            </Badge>
            {label && (
              <Badge variant={statusTone(attachment.index_status)} className="gap-1.5 text-[11px]">
                <AttachmentStatusIcon status={attachment.index_status} />
                {label}
              </Badge>
            )}
            {attachment.warning && (
              <span className="text-xs text-muted-foreground">{attachment.warning}</span>
            )}
            {saved ? (
              <Badge variant="secondary" className="text-[11px]">
                Saved to Research
              </Badge>
            ) : (
              <Button
                type="button"
                size="sm"
                variant="outline"
                className="h-7 gap-1 px-2 text-xs"
                disabled={!token || savingId === attachment.library_item_id}
                onClick={() => handleSave(attachment)}
              >
                {savingId === attachment.library_item_id ? (
                  <LoaderCircle className="h-3 w-3 animate-spin" />
                ) : (
                  <Save className="h-3 w-3" />
                )}
                Save to Research
              </Button>
            )}
          </div>
        );
      })}
    </div>
  );
}

export function ChatPdfAttachmentPicker({
  attachments,
  disabled,
  onAddFiles,
  onRemove,
}: {
  attachments: PendingChatPdfAttachment[];
  disabled?: boolean;
  onAddFiles: (files: FileList | File[] | null | undefined) => void;
  onRemove: (key: string) => void;
}) {
  const inputRef = useRef<HTMLInputElement>(null);

  return (
    <div className="space-y-2">
      {attachments.length > 0 && (
        <div className="space-y-2">
          {attachments.map((attachment) => {
            const label = statusLabel(attachment.status);
            const helperText = attachment.error || attachment.uploaded?.warning;
            return (
              <div
                key={attachment.key}
                className="flex flex-wrap items-center gap-2 rounded-lg border bg-background/70 px-2.5 py-2"
              >
                <Badge variant="secondary" className="max-w-full gap-1.5">
                  <FileText className="h-3 w-3" />
                  <span className="max-w-[180px] truncate">{attachment.file.name}</span>
                </Badge>
                {label && (
                  <Badge variant={statusTone(attachment.status)} className="gap-1.5 text-[11px]">
                    <AttachmentStatusIcon status={attachment.status} />
                    {label}
                  </Badge>
                )}
                {helperText && <span className="text-xs text-muted-foreground">{helperText}</span>}
                <button
                  type="button"
                  aria-label={`Remove ${attachment.file.name}`}
                  className="rounded-full p-0.5 hover:bg-black/10"
                  onClick={() => onRemove(attachment.key)}
                  disabled={disabled}
                >
                  <X className="h-3 w-3" />
                </button>
              </div>
            );
          })}
        </div>
      )}
      <div className="flex flex-wrap items-center gap-2">
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf"
          multiple
          className="hidden"
          onChange={(event) => {
            onAddFiles(event.target.files);
            event.currentTarget.value = "";
          }}
          disabled={disabled}
        />
        <Button
          type="button"
          variant="outline"
          size="sm"
          className="gap-2"
          onClick={() => inputRef.current?.click()}
          disabled={disabled}
        >
          <Paperclip className="h-3.5 w-3.5" />
          Attach PDF
        </Button>
        <span className="text-xs text-muted-foreground">
          Uploads privately for this chat. Save it to Research later if it proves useful.
        </span>
      </div>
    </div>
  );
}
