import type { ReactNode } from "react";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface WorkspacePageHeaderProps {
  title: string;
  description: string;
  eyebrow?: string;
  badge?: string;
  actions?: ReactNode;
  className?: string;
}

export function WorkspacePageHeader({
  title,
  description,
  eyebrow,
  badge,
  actions,
  className,
}: WorkspacePageHeaderProps) {
  return (
    <div
      className={cn(
        "flex flex-col gap-4 rounded-2xl border bg-card/60 p-5 shadow-sm backdrop-blur supports-[backdrop-filter]:bg-card/70 sm:p-6",
        className
      )}
    >
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            {eyebrow ? (
              <span className="text-[11px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                {eyebrow}
              </span>
            ) : null}
            {badge ? <Badge variant="secondary">{badge}</Badge> : null}
          </div>
          <div className="space-y-1">
            <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">{title}</h1>
            <p className="max-w-3xl text-sm leading-6 text-muted-foreground sm:text-[15px]">
              {description}
            </p>
          </div>
        </div>

        {actions ? (
          <div className="flex shrink-0 flex-wrap items-center gap-2 lg:justify-end">{actions}</div>
        ) : null}
      </div>
    </div>
  );
}
