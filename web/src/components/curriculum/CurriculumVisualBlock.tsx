"use client";

import { useId, useMemo, useState, type ReactNode } from "react";
import { ArrowDown, ArrowRight, Globe2, MapPin, Star } from "lucide-react";
import { ChartOverlay } from "@/components/curriculum/ChartOverlay";
import type { ParsedChartData } from "@/lib/chart-parser";
import { buildWorldGeographyRegionMapData } from "@/lib/world-geography-maps";
import type {
  CurriculumChartBlock,
  CurriculumComparisonTableBlock,
  CurriculumDiagramBlock,
  CurriculumFrameworkBlock,
  CurriculumMapBlock,
  CurriculumProcessFlowBlock,
  CurriculumTimelineBlock,
  CurriculumVisualBlock,
  CurriculumVisualNode,
} from "@/types/curriculum";

const MAP_SUBREGION_COLORS = [
  "#2563eb",
  "#0f766e",
  "#b45309",
  "#7c3aed",
  "#be185d",
  "#0891b2",
  "#059669",
];

export function CurriculumVisualBlockRenderer({
  block,
  chapterContent,
}: {
  block: CurriculumVisualBlock;
  chapterContent?: string;
}) {
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
    case "map":
      return <MapVisual block={block} chapterContent={chapterContent} />;
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

function MapVisual({
  block,
  chapterContent,
}: {
  block: CurriculumMapBlock;
  chapterContent?: string;
}) {
  const mapData = useMemo(
    () => buildWorldGeographyRegionMapData(block, chapterContent),
    [block, chapterContent],
  );
  const [selectedCountryId, setSelectedCountryId] = useState<string>("");
  const [hoveredCountryId, setHoveredCountryId] = useState<string | null>(null);

  if (!mapData) return null;

  const effectiveSelectedCountryId = mapData.countries.some(
    (country) => country.id === selectedCountryId,
  )
    ? selectedCountryId
    : mapData.defaultCountryId;
  const selectedCountry =
    mapData.countries.find((country) => country.id === effectiveSelectedCountryId) ??
    mapData.countries[0];
  const hoveredCountry = hoveredCountryId
    ? mapData.countries.find((country) => country.id === hoveredCountryId) ?? null
    : null;
  const hoveredCountryColor = hoveredCountry
    ? getSubregionColor(hoveredCountry.subregion, mapData.countries)
    : null;
  const selectedCountryColor = getSubregionColor(selectedCountry.subregion, mapData.countries);
  const selectedLandmarks =
    selectedCountry.landmarks.length > 0
      ? selectedCountry.landmarks
      : mapData.landmarks
          .filter((landmark) => landmark.countryId === selectedCountry.id)
          .map((landmark) => landmark.label);
  const orderedSubregions = Array.from(
    new Set(mapData.countries.map((country) => country.subregion)),
  );

  return (
    <VisualShell title={block.title} note={block.note}>
      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.6fr)_minmax(280px,0.95fr)]">
        <div className="rounded-2xl border bg-gradient-to-br from-background via-muted/10 to-background p-4 shadow-sm">
          <div className="mb-4 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
            <span className="inline-flex items-center gap-1 rounded-full bg-muted/60 px-2.5 py-1">
              <MapPin className="h-3.5 w-3.5" />
              Hover or tap a country
            </span>
            <span className="inline-flex items-center gap-1 rounded-full bg-muted/60 px-2.5 py-1">
              <Star className="h-3.5 w-3.5 text-amber-500" />
              Landmark cue
            </span>
            <span className="inline-flex items-center gap-1 rounded-full bg-muted/60 px-2.5 py-1">
              <Globe2 className="h-3.5 w-3.5" />
              {mapData.countries.length} countries
            </span>
          </div>

          <div className="relative aspect-square overflow-hidden rounded-2xl border bg-[radial-gradient(circle_at_top,_rgba(59,130,246,0.16),_transparent_32%),linear-gradient(180deg,_rgba(255,255,255,0.04),_rgba(15,23,42,0.02))]">
            <svg
              viewBox={`0 0 ${mapData.width} ${mapData.height}`}
              className="absolute inset-0 h-full w-full"
              aria-label={mapData.title}
              role="img"
            >
              <rect x="0" y="0" width={mapData.width} height={mapData.height} fill="#f8fafc" />
              <g opacity="0.16">
                <path
                  d={`M 0 ${mapData.height / 2} L ${mapData.width} ${mapData.height / 2}`}
                  stroke="#64748b"
                  strokeDasharray="3 4"
                  strokeWidth="0.4"
                />
                <path
                  d={`M ${mapData.width / 2} 0 L ${mapData.width / 2} ${mapData.height}`}
                  stroke="#64748b"
                  strokeDasharray="3 4"
                  strokeWidth="0.4"
                />
              </g>
              {mapData.backgroundPaths.map((path, index) => (
                <path
                  key={index}
                  d={path}
                  fill="#dbeafe"
                  stroke="#93c5fd"
                  strokeWidth="0.7"
                  opacity="0.95"
                />
              ))}

              {mapData.landmarks.map((landmark) => (
                <g key={landmark.id} transform={`translate(${landmark.x}, ${landmark.y})`}>
                  <circle r="1.85" fill="#f59e0b" stroke="#ffffff" strokeWidth="0.8" />
                  <circle r="0.65" fill="#78350f" />
                </g>
              ))}

              {mapData.countries.map((country) => {
                const isSelected = country.id === selectedCountry.id;
                const isHovered = country.id === hoveredCountry?.id;
                const color = getSubregionColor(country.subregion, mapData.countries);

                return (
                  <g key={country.id} transform={`translate(${country.x}, ${country.y})`}>
                    {(isSelected || isHovered) && (
                      <circle
                        r="3.5"
                        fill="none"
                        stroke={color}
                        strokeWidth="1.2"
                        opacity={isSelected ? 0.95 : 0.7}
                      />
                    )}
                    <circle
                      r={country.isAnchor ? "2.45" : "2.1"}
                      fill={color}
                      stroke="#ffffff"
                      strokeWidth={isSelected ? "1.15" : "0.8"}
                    />
                  </g>
                );
              })}
            </svg>

            <div className="absolute inset-0">
              {mapData.countries.map((country) => (
                <button
                  key={country.id}
                  type="button"
                  className="absolute -translate-x-1/2 -translate-y-1/2 rounded-full focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
                  style={{
                    left: `${country.x}%`,
                    top: `${country.y}%`,
                    width: "28px",
                    height: "28px",
                  }}
                  onMouseEnter={() => setHoveredCountryId(country.id)}
                  onMouseLeave={() =>
                    setHoveredCountryId((current) =>
                      current === country.id ? null : current,
                    )
                  }
                  onFocus={() => setHoveredCountryId(country.id)}
                  onBlur={() =>
                    setHoveredCountryId((current) =>
                      current === country.id ? null : current,
                    )
                  }
                  onClick={() => setSelectedCountryId(country.id)}
                  aria-label={`Show ${country.name} details`}
                />
              ))}
            </div>

            {hoveredCountry && hoveredCountryColor ? (
              <div
                className="pointer-events-none absolute z-10 hidden w-56 -translate-x-1/2 -translate-y-[110%] rounded-xl border bg-background/95 p-3 shadow-xl backdrop-blur md:block"
                style={{ left: `${hoveredCountry.x}%`, top: `${hoveredCountry.y}%` }}
              >
                <div className="mb-2 flex items-center gap-2">
                  <span
                    className="h-2.5 w-2.5 rounded-full"
                    style={{ backgroundColor: hoveredCountryColor }}
                  />
                  <p className="text-sm font-semibold text-foreground">{hoveredCountry.name}</p>
                </div>
                <p className="text-xs text-muted-foreground">
                  {hoveredCountry.capital} / {hoveredCountry.subregion}
                </p>
                <p className="mt-2 text-xs leading-relaxed text-foreground/85">
                  {hoveredCountry.keyFact}
                </p>
                {hoveredCountry.landmarks.length > 0 ? (
                  <p className="mt-2 text-[11px] text-muted-foreground">
                    Landmark cues: {hoveredCountry.landmarks.slice(0, 2).join(", ")}
                  </p>
                ) : null}
              </div>
            ) : null}
          </div>

          <div className="mt-4 flex flex-wrap gap-2">
            {orderedSubregions.map((subregion) => (
              <span
                key={subregion}
                className="inline-flex items-center gap-2 rounded-full border bg-background/80 px-2.5 py-1 text-xs text-muted-foreground"
              >
                <span
                  className="h-2.5 w-2.5 rounded-full"
                  style={{ backgroundColor: getSubregionColor(subregion, mapData.countries) }}
                />
                {subregion}
              </span>
            ))}
          </div>
        </div>

        <aside className="rounded-2xl border bg-background p-4 shadow-sm">
          <div className="mb-4 flex items-start justify-between gap-3">
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-primary/80">
                Selected country
              </p>
              <h4 className="mt-1 text-lg font-semibold text-foreground">
                {selectedCountry.name}
              </h4>
            </div>
            <span
              className="rounded-full px-2.5 py-1 text-xs font-medium text-white"
              style={{ backgroundColor: selectedCountryColor }}
            >
              {selectedCountry.subregion}
            </span>
          </div>

          <dl className="grid gap-3 sm:grid-cols-2 xl:grid-cols-1">
            <div className="rounded-xl border bg-muted/20 p-3">
              <dt className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
                Capital
              </dt>
              <dd className="mt-1 text-sm font-medium text-foreground">
                {selectedCountry.capital}
              </dd>
            </div>
            <div className="rounded-xl border bg-muted/20 p-3">
              <dt className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
                Geography type
              </dt>
              <dd className="mt-1 text-sm font-medium text-foreground">
                {selectedCountry.geographyType}
              </dd>
            </div>
          </dl>

          <div className="mt-4 rounded-xl border bg-muted/20 p-3">
            <p className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
              Why this country matters
            </p>
            <p className="mt-2 text-sm leading-relaxed text-foreground/85">
              {selectedCountry.keyFact}
            </p>
            <p className="mt-3 text-xs leading-relaxed text-muted-foreground">
              {selectedCountry.compactProfile}
            </p>
          </div>

          <div className="mt-4 rounded-xl border bg-muted/20 p-3">
            <p className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
              Landmark cues
            </p>
            {selectedLandmarks.length > 0 ? (
              <ul className="mt-2 space-y-2 text-sm text-foreground/85">
                {selectedLandmarks.map((landmark) => (
                  <li key={landmark} className="flex gap-2">
                    <Star className="mt-0.5 h-3.5 w-3.5 shrink-0 text-amber-500" />
                    <span>{landmark}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="mt-2 text-sm text-muted-foreground">
                This chapter does not call out a specific landmark for{" "}
                {selectedCountry.name}, but the map still places the country within its regional
                context.
              </p>
            )}
          </div>
        </aside>
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

function getSubregionColor(
  subregion: string,
  countries: Array<{
    subregion: string;
  }>,
): string {
  const orderedSubregions = Array.from(new Set(countries.map((country) => country.subregion)));
  const index = orderedSubregions.findIndex((candidate) => candidate === subregion);
  return MAP_SUBREGION_COLORS[index % MAP_SUBREGION_COLORS.length] ?? MAP_SUBREGION_COLORS[0];
}
