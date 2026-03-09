import { ExternalLink } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { WhyNowReason } from "@/types/briefing";

interface WhyNowChipProps {
  chip: WhyNowReason;
}

function hasVisibleValue(value: unknown): boolean {
  if (Array.isArray(value)) return value.length > 0;
  if (value && typeof value === "object") return Object.keys(value as Record<string, unknown>).length > 0;
  return value !== null && value !== undefined && String(value).trim().length > 0;
}

function humanizeKey(key: string): string {
  return key
    .replaceAll("_", " ")
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

function badgeTone(severity: string): string {
  if (severity === "success") {
    return "border-emerald-300/70 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300";
  }
  if (severity === "warning") {
    return "border-amber-300/70 bg-amber-500/10 text-amber-700 dark:text-amber-300";
  }
  return "border-sky-300/70 bg-sky-500/10 text-sky-700 dark:text-sky-300";
}

function renderDetailValue(key: string, value: unknown) {
  if (!hasVisibleValue(value)) {
    return null;
  }

  if (key === "source_urls" && Array.isArray(value)) {
    return (
      <ul className="space-y-1">
        {value.map((url, index) => (
          <li key={`${String(url)}-${index}`}>
            <a
              href={String(url)}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1 text-primary hover:underline"
            >
              Source {index + 1}
              <ExternalLink className="h-3 w-3" />
            </a>
          </li>
        ))}
      </ul>
    );
  }

  if (Array.isArray(value)) {
    return (
      <ul className="space-y-1">
        {value.map((entry, index) => (
          <li key={`${key}-${index}`} className="leading-relaxed text-foreground/90">
            {typeof entry === "string" ? entry : JSON.stringify(entry)}
          </li>
        ))}
      </ul>
    );
  }

  if (value && typeof value === "object") {
    const entries = Object.entries(value as Record<string, unknown>).filter(([, nestedValue]) =>
      hasVisibleValue(nestedValue)
    );

    if (!entries.length) {
      return null;
    }

    return (
      <div className="space-y-1.5">
        {entries.map(([nestedKey, nestedValue]) => (
          <div key={nestedKey}>
            <div className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
              {humanizeKey(nestedKey)}
            </div>
            <div className="text-foreground/90">{String(nestedValue)}</div>
          </div>
        ))}
      </div>
    );
  }

  return <div className="text-foreground/90">{String(value)}</div>;
}

export function WhyNowChip({ chip }: WhyNowChipProps) {
  const detail = chip.detail ?? {};
  const detailEntries = Object.entries(detail).filter(([, value]) => hasVisibleValue(value));
  const chipLabel = (
    <Badge variant="outline" className={cn("cursor-pointer border text-[11px]", badgeTone(chip.severity))}>
      {chip.label}
    </Badge>
  );

  if (!detailEntries.length) {
    return chipLabel;
  }

  return (
    <details className="group relative">
      <summary className="list-none [&::-webkit-details-marker]:hidden">{chipLabel}</summary>
      <div className="absolute left-0 top-full z-20 mt-2 w-80 max-w-[min(20rem,calc(100vw-4rem))] rounded-lg border bg-background p-3 text-xs shadow-lg">
        <div className="mb-2 font-medium text-foreground">{chip.label}</div>
        <div className="space-y-2">
          {detailEntries.map(([key, value]) => (
            <div key={key} className="space-y-1">
              <div className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
                {humanizeKey(key)}
              </div>
              {renderDetailValue(key, value)}
            </div>
          ))}
        </div>
      </div>
    </details>
  );
}
