import { apiFetch } from "./api";

export type EngagementEventType =
  | "opened"
  | "saved"
  | "dismissed"
  | "acted_on"
  | "feedback_useful"
  | "feedback_irrelevant";

export type TargetType =
  | "recommendation"
  | "intel"
  | "journal"
  | "research"
  | "insight"
  | "suggestion";

export function logEngagement(
  token: string,
  eventType: EngagementEventType,
  targetType: TargetType,
  targetId: string,
  metadata?: Record<string, unknown>
): void {
  // Fire-and-forget — don't block UI
  apiFetch(
    "/api/engagement",
    {
      method: "POST",
      body: JSON.stringify({
        event_type: eventType,
        target_type: targetType,
        target_id: targetId,
        metadata: metadata ?? null,
      }),
    },
    token
  ).catch(() => {}); // silent on failure
}
