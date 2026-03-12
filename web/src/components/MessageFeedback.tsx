"use client";

import { useState } from "react";
import { Zap, ZapOff } from "lucide-react";
import { Button } from "@/components/ui/button";
import { logEngagement } from "@/lib/engagement";

interface MessageFeedbackProps {
  messageId: string;
  token: string;
}

export function MessageFeedback({ messageId, token }: MessageFeedbackProps) {
  const [selected, setSelected] = useState<"signal" | "noise" | null>(null);

  const handleClick = (choice: "signal" | "noise") => {
    if (selected) return;
    setSelected(choice);
    logEngagement(
      token,
      choice === "signal" ? "feedback_useful" : "feedback_irrelevant",
      "advisor",
      messageId,
    );
  };

  return (
    <div className="flex items-center gap-1">
      <Button
        variant="ghost"
        size="sm"
        className={`h-7 gap-1 px-2 text-xs ${
          selected === "signal"
            ? "text-primary"
            : selected === "noise"
              ? "opacity-30"
              : "text-muted-foreground"
        }`}
        disabled={selected !== null}
        onClick={() => handleClick("signal")}
      >
        <Zap className="h-3 w-3" />
        Signal
      </Button>
      <Button
        variant="ghost"
        size="sm"
        className={`h-7 gap-1 px-2 text-xs ${
          selected === "noise"
            ? "text-destructive"
            : selected === "signal"
              ? "opacity-30"
              : "text-muted-foreground"
        }`}
        disabled={selected !== null}
        onClick={() => handleClick("noise")}
      >
        <ZapOff className="h-3 w-3" />
        Noise
      </Button>
    </div>
  );
}
