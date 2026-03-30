"use client";

import { useId, type ReactNode } from "react";
import { ArrowDown, ArrowRight } from "lucide-react";
import { ChartOverlay } from "@/components/curriculum/ChartOverlay";
import type { ParsedChartData } from "@/lib/chart-parser";
import type {
  CurriculumChartBlock,
  CurriculumComparisonTableBlock,
  CurriculumDiagramBlock,
  CurriculumFrameworkBlock,
  CurriculumProcessFlowBlock,
  CurriculumTimelineBlock,
  CurriculumVisualBlock,
  CurriculumVisualNode,
} from "@/types/curriculum";

export function CurriculumVisualBlockRenderer({ block }: { block: CurriculumVisualBlock }) {
  switch (block.type) {
    case "diagram":
      return <DiagramVisual block={block} />;
    case "process-flow":
      return <ProcessFlowVisual block={block} />;
    case "framework":
      return <FrameworkVisual block={block} />;
    case "comparison-table":
      return <ComparisonTableVisual block={block} />;
    case "chart":
      return <ChartVisual block={block} />;
    case "timeline":
      return <TimelineVisual block={block} />;
    default:
      return null;
  }
}

function ChartVisual({ block }: { block: CurriculumChartBlock }) {
  const chartData = toParsedChartData(block);

  return (
    <VisualShell title={block.title} note={block.note}>
      <div className="rounded-xl border bg-background p-4 shadow-sm">
        <ChartOverlay data={chartData} />
      </div>
    </VisualShell>
  );
}

function ProcessFlowVisual({ block }: { block: CurriculumProcessFlowBlock }) {
  return (
    <VisualShell title={block.title} note={block.note}>
      <div className="space-y-3 md:hidden">
        {block.steps.map((step, index) => (
          <div key={step.id} className="space-y-3">
            <ProcessCard step={step} index={index} />
            {index < block.steps.length - 1 && (
              <div className="flex justify-center text-muted-foreground">
                <ArrowDown className="h-4 w-4" />
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="hidden items-stretch gap-3 md:flex md:overflow-x-auto md:pb-1">
        {block.steps.map((step, index) => (
          <div key={step.id} className="flex min-w-[220px] items-center gap-3">
            <ProcessCard step={step} index={index} />
            {index < block.steps.length - 1 && (
              <div className="flex shrink-0 items-center text-muted-foreground">
                <ArrowRight className="h-4 w-4" />
              </div>
            )}
          </div>
        ))}
      </div>
    </VisualShell>
  );
}

function ProcessCard({
  step,
  index,
}: {
  step: CurriculumProcessFlowBlock["steps"][number];
  index: number;
}) {
  return (
    <div className="flex-1 rounded-xl border bg-background p-4 shadow-sm">
      <div className="mb-2 flex items-center gap-2">
        <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-semibold text-primary">
          {index + 1}
        </span>
        <p className="text-sm font-semibold text-foreground">{step.title}</p>
      </div>
      {step.detail && <p className="text-sm text-muted-foreground">{step.detail}</p>}
      {step.emphasis && (
        <p className="mt-3 text-xs font-medium uppercase tracking-wide text-primary/80">
          {step.emphasis}
        </p>
      )}
    </div>
  );
}

function FrameworkVisual({ block }: { block: CurriculumFrameworkBlock }) {
  return (
    <VisualShell title={block.title} note={block.note}>
      <div className="grid gap-3 md:grid-cols-3">
        {block.pillars.map((pillar, index) => (
          <div
            key={`${pillar.title}-${index}`}
            className="rounded-xl border bg-background p-4 shadow-sm"
          >
            <div className="mb-3 flex items-center gap-2">
              <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-semibold text-primary">
                {index + 1}
              </span>
              <p className="text-sm font-semibold text-foreground">{pillar.title}</p>
            </div>
            {pillar.detail && <p className="text-sm text-muted-foreground">{pillar.detail}</p>}
            {pillar.bullets && pillar.bullets.length > 0 && (
              <ul className="mt-3 space-y-2 text-sm text-muted-foreground">
                {pillar.bullets.map((bullet) => (
                  <li key={bullet} className="flex gap-2">
                    <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-primary/60" />
                    <span>{bullet}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        ))}
      </div>
    </VisualShell>
  );
}

function ComparisonTableVisual({ block }: { block: CurriculumComparisonTableBlock }) {
  return (
    <VisualShell title={block.title} note={block.note}>
      <div className="overflow-x-auto rounded-xl border bg-background shadow-sm">
        <table className="w-full min-w-[560px] text-left text-sm">
          <thead className="bg-muted/40">
            <tr>
              {block.columns.map((column) => (
                <th
                  key={column.key}
                  className="px-4 py-3 text-xs font-semibold uppercase tracking-wide text-muted-foreground"
                >
                  {column.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {block.rows.map((row, index) => (
              <tr key={index} className="border-t align-top">
                {block.columns.map((column) => (
                  <td key={column.key} className="px-4 py-3 text-sm text-foreground/90">
                    {formatCellValue(row[column.key])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </VisualShell>
  );
}

function DiagramVisual({ block }: { block: CurriculumDiagramBlock }) {
  const nodes = normalizeDiagramNodes(block.nodes);
  const columns = Math.max(...nodes.map((node) => node.column ?? 1), 1);
  const rows = Math.max(...nodes.map((node) => node.row ?? 1), 1);
  const markerId = useId().replace(/:/g, "");

  return (
    <VisualShell title={block.title} note={block.note}>
      <div className="space-y-3 md:hidden">
        {nodes.map((node) => (
          <div
            key={node.id}
            className={`rounded-xl border p-4 shadow-sm ${getNodeToneClasses(node.tone)}`}
          >
            <p className="text-sm font-semibold text-foreground">{node.title}</p>
            {node.detail && <p className="mt-2 text-sm text-muted-foreground">{node.detail}</p>}
          </div>
        ))}
      </div>

      <div
        className="relative hidden overflow-x-auto rounded-2xl border bg-gradient-to-br from-background via-muted/10 to-background p-6 shadow-sm md:block"
        style={{ minHeight: `${Math.max(rows, 2) * 150}px` }}
      >
        <svg
          viewBox={`0 0 ${columns * 100} ${rows * 100}`}
          className="absolute inset-0 h-full w-full"
          aria-hidden="true"
        >
          <defs>
            <marker
              id={markerId}
              markerWidth="8"
              markerHeight="8"
              refX="7"
              refY="4"
              orient="auto"
            >
              <path d="M0,0 L8,4 L0,8 z" className="fill-primary/50" />
            </marker>
          </defs>

          {(block.edges ?? []).map((edge) => {
            const from = nodes.find((node) => node.id === edge.from);
            const to = nodes.find((node) => node.id === edge.to);
            if (!from || !to) return null;

            const startX = ((from.column ?? 1) - 0.5) * 100;
            const startY = ((from.row ?? 1) - 0.5) * 100;
            const endX = ((to.column ?? 1) - 0.5) * 100;
            const endY = ((to.row ?? 1) - 0.5) * 100;
            const midY = (startY + endY) / 2;

            return (
              <g key={`${edge.from}-${edge.to}`}>
                <path
                  d={`M ${startX} ${startY} C ${startX} ${midY}, ${endX} ${midY}, ${endX} ${endY}`}
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2.5"
                  className="text-primary/35"
                  markerEnd={`url(#${markerId})`}
                />
                {edge.label && (
                  <text
                    x={(startX + endX) / 2}
                    y={midY - 4}
                    textAnchor="middle"
                    className="fill-muted-foreground"
                    style={{ fontSize: 9 }}
                  >
                    {edge.label}
                  </text>
                )}
              </g>
            );
          })}
        </svg>

        <div
          className="relative z-10 grid gap-4"
          style={{
            gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))`,
            gridTemplateRows: `repeat(${rows}, minmax(0, 1fr))`,
          }}
        >
          {nodes.map((node) => (
            <div
              key={node.id}
              className={`rounded-xl border p-4 shadow-sm ${getNodeToneClasses(node.tone)}`}
              style={{
                gridColumn: `${node.column ?? 1} / span 1`,
                gridRow: `${node.row ?? 1} / span 1`,
              }}
            >
              <p className="text-sm font-semibold text-foreground">{node.title}</p>
              {node.detail && <p className="mt-2 text-sm text-muted-foreground">{node.detail}</p>}
            </div>
          ))}
        </div>
      </div>
    </VisualShell>
  );
}

function TimelineVisual({ block }: { block: CurriculumTimelineBlock }) {
  return (
    <VisualShell title={block.title} note={block.note}>
      <div className="space-y-4 md:hidden">
        {block.entries.map((entry) => (
          <div key={entry.id} className="flex gap-3">
            <div className="flex flex-col items-center">
              <span className="mt-1 h-3 w-3 rounded-full bg-primary/70" />
              <span className="mt-1 h-full w-px bg-border" />
            </div>
            <div className="flex-1 rounded-xl border bg-background p-4 shadow-sm">
              <p className="text-xs font-medium uppercase tracking-wide text-primary/80">
                {entry.period}
              </p>
              <p className="mt-1 text-sm font-semibold text-foreground">{entry.title}</p>
              {entry.detail && (
                <p className="mt-2 text-sm text-muted-foreground">{entry.detail}</p>
              )}
              {entry.emphasis && (
                <p className="mt-3 text-xs font-medium uppercase tracking-wide text-muted-foreground">
                  {entry.emphasis}
                </p>
              )}
            </div>
          </div>
        ))}
      </div>

      <div className="hidden overflow-x-auto rounded-2xl border bg-background p-5 shadow-sm md:block">
        <div className="flex min-w-[760px] items-start gap-4">
          {block.entries.map((entry, index) => (
            <div key={entry.id} className="flex min-w-[180px] flex-1 gap-4">
              <div className="pt-8 text-primary/70">
                <span className="block h-3 w-3 rounded-full bg-current" />
                {index < block.entries.length - 1 ? (
                  <span className="mt-3 block h-px w-20 bg-border" />
                ) : null}
              </div>
              <div className="rounded-xl border bg-muted/10 p-4">
                <p className="text-xs font-medium uppercase tracking-wide text-primary/80">
                  {entry.period}
                </p>
                <p className="mt-1 text-sm font-semibold text-foreground">{entry.title}</p>
                {entry.detail && (
                  <p className="mt-2 text-sm text-muted-foreground">{entry.detail}</p>
                )}
                {entry.emphasis && (
                  <p className="mt-3 text-xs font-medium uppercase tracking-wide text-muted-foreground">
                    {entry.emphasis}
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </VisualShell>
  );
}

function VisualShell({
  title,
  note,
  children,
}: {
  title?: string;
  note?: string;
  children: ReactNode;
}) {
  return (
    <section className="my-6 space-y-3">
      {(title || note) && (
        <div className="space-y-1">
          {title && <h3 className="text-sm font-semibold text-foreground">{title}</h3>}
          {note && <p className="text-xs text-muted-foreground">{note}</p>}
        </div>
      )}
      {children}
    </section>
  );
}

function normalizeDiagramNodes(nodes: CurriculumVisualNode[]): CurriculumVisualNode[] {
  return nodes.map((node, index) => ({
    ...node,
    column: node.column ?? ((index % 3) + 1),
    row: node.row ?? (Math.floor(index / 3) + 1),
    tone: node.tone ?? "default",
  }));
}

function getNodeToneClasses(tone: CurriculumVisualNode["tone"]): string {
  switch (tone) {
    case "accent":
      return "border-primary/40 bg-primary/5";
    case "muted":
      return "border-border/70 bg-muted/30";
    default:
      return "border-border bg-background";
  }
}

function formatCellValue(value: string | number | undefined): string {
  if (value === undefined) return "-";
  return typeof value === "number" ? value.toString() : value;
}

function toParsedChartData(block: CurriculumChartBlock): ParsedChartData {
  if (block.chartType !== "scatter") {
    return {
      chartType: block.chartType,
      title: block.title ?? "",
      xLabel: block.xLabel,
      yLabel: block.yLabel ?? "",
      data: block.data,
      series: block.series ?? [],
    };
  }

  const yKey = block.series?.[0] ?? block.yLabel ?? "y";
  return {
    chartType: "scatter",
    title: block.title ?? "",
    xLabel: block.xLabel,
    yLabel: block.yLabel ?? yKey,
    data: block.data.map((row) => ({
      x: coerceChartNumber(row[block.xLabel]),
      y: coerceChartNumber(row[yKey]),
    })),
    series: [yKey],
  };
}

function coerceChartNumber(value: string | number | undefined): number {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value === "string") {
    const parsed = Number(value);
    if (Number.isFinite(parsed)) return parsed;
  }
  return 0;
}
