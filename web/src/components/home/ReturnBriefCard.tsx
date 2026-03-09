import { ChevronDown, Clock3, X } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { ReturnBrief } from "@/types/greeting";

interface ReturnBriefCardProps {
  brief: ReturnBrief;
  onDismiss?: () => void;
}

const SECTION_LABELS: Record<string, string> = {
  intel: "Intel",
  company_movements: "Company Movements",
  hiring_signals: "Hiring Signals",
  regulatory_alerts: "Regulatory Alerts",
  threads: "Threads",
  dossiers: "Dossiers",
  goals: "Goals",
  assumptions: "Assumptions",
  summary: "Summary",
};

function formatAbsence(absentHours: number): string {
  if (absentHours >= 48) {
    const daysAway = Math.floor(absentHours / 24);
    return `${daysAway} day${daysAway === 1 ? "" : "s"} away`;
  }

  return `${absentHours} hour${absentHours === 1 ? "" : "s"} away`;
}

function readItemTitle(item: Record<string, unknown>): string {
  const candidates = [item.title, item.label, item.name, item.path, item.id];
  const matched = candidates.find((value) => typeof value === "string" && value.trim().length > 0);
  return typeof matched === "string" ? matched : "Update available";
}

function readItemDetail(item: Record<string, unknown>): string | null {
  const candidates = [item.detail, item.summary, item.description, item.reason];
  const matched = candidates.find((value) => typeof value === "string" && value.trim().length > 0);
  return typeof matched === "string" ? matched : null;
}

export function ReturnBriefCard({ brief, onDismiss }: ReturnBriefCardProps) {
  return (
    <Card className="gap-4 border-primary/20 bg-primary/5 py-4 shadow-none hover:shadow-none">
      <CardHeader className="gap-3 px-4 pb-0">
        <div className="flex items-start justify-between gap-3">
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="secondary">Since you were away</Badge>
              <Badge variant="outline" className="gap-1">
                <Clock3 className="h-3 w-3" />
                {formatAbsence(brief.absent_hours)}
              </Badge>
            </div>
            <div className="space-y-1">
              <CardTitle className="text-base">Welcome back</CardTitle>
              <CardDescription className="max-w-2xl text-sm text-foreground/80">
                {brief.summary}
              </CardDescription>
            </div>
          </div>
          {onDismiss ? (
            <Button
              type="button"
              size="icon-xs"
              variant="ghost"
              className="mt-0.5"
              onClick={onDismiss}
              aria-label="Dismiss return brief"
            >
              <X className="h-3.5 w-3.5" />
            </Button>
          ) : null}
        </div>
      </CardHeader>

      <CardContent className="space-y-3 px-4">
        <details className="group rounded-lg border bg-background/80 p-3">
          <summary className="flex cursor-pointer list-none items-center justify-between gap-3 text-sm font-medium [&::-webkit-details-marker]:hidden">
            <span>What changed</span>
            <ChevronDown className="h-4 w-4 text-muted-foreground transition-transform group-open:rotate-180" />
          </summary>

          <div className="mt-3 grid gap-3 md:grid-cols-2">
            {brief.sections.map((section) => (
              <div key={`${brief.generated_at}-${section.kind}`} className="space-y-2 rounded-lg border bg-card p-3">
                <div className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                  {SECTION_LABELS[section.kind] ?? section.kind}
                </div>
                <ul className="space-y-2 text-sm">
                  {section.items.map((item, index) => {
                    const title = readItemTitle(item);
                    const detail = readItemDetail(item);

                    return (
                      <li key={`${section.kind}-${index}`} className="leading-relaxed">
                        <div className="font-medium text-foreground">{title}</div>
                        {detail ? <div className="text-muted-foreground">{detail}</div> : null}
                      </li>
                    );
                  })}
                </ul>
              </div>
            ))}
          </div>
        </details>

        {brief.next_steps.length > 0 ? (
          <div className="space-y-2">
            <div className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
              Suggested next steps
            </div>
            <div className="flex flex-wrap gap-2">
              {brief.next_steps.map((step, index) => (
                <Badge
                  key={`${step.kind}-${step.target || index}`}
                  variant="outline"
                  className={cn("max-w-full px-2.5 py-1 text-xs", !step.target && "opacity-80")}
                >
                  {step.label}
                </Badge>
              ))}
            </div>
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}
