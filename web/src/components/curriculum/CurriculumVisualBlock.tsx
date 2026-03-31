"use client";

import { useId, useMemo, useState, type ReactNode } from "react";
import { ArrowDown, ArrowRight, Globe2, MapPin, Star } from "lucide-react";
import {
  ComposableMap,
  Geographies,
  Geography,
  Marker,
  Sphere,
  createCoordinates,
  getBestGeographyCoordinates,
} from "@vnedyalk0v/react19-simple-maps";
import { ChartOverlay } from "@/components/curriculum/ChartOverlay";
import type { ParsedChartData } from "@/lib/chart-parser";
import countryTopology from "world-atlas/countries-10m.json";
import {
  buildWorldGeographyRegionMapData,
  normalizeCountryKey,
} from "@/lib/world-geography-maps";
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
  const countriesByTopologyKey = useMemo(
    () => new Map((mapData?.countries ?? []).map((country) => [country.topologyKey, country])),
    [mapData],
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
  const activeCountry = hoveredCountry ?? selectedCountry;
  const selectedCountryColor = getSubregionColor(selectedCountry.subregion, mapData.countries);
  const selectedLandmarks =
    selectedCountry.landmarks.length > 0
      ? selectedCountry.landmarks
      : [];
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
              Anchor country
            </span>
            <span className="inline-flex items-center gap-1 rounded-full bg-muted/60 px-2.5 py-1">
              <Globe2 className="h-3.5 w-3.5" />
              {mapData.countries.length} countries
            </span>
          </div>

          <div className="relative overflow-hidden rounded-2xl border bg-[radial-gradient(circle_at_top,_rgba(59,130,246,0.16),_transparent_32%),linear-gradient(180deg,_rgba(255,255,255,0.04),_rgba(15,23,42,0.02))]">
            <ComposableMap
              projection="geoMercator"
              projectionConfig={{
                center: createCoordinates(mapData.center[0], mapData.center[1]),
                scale: mapData.scale,
              }}
              width={820}
              height={520}
              className="h-full w-full"
              aria-label={mapData.title}
            >
              <Sphere fill="#f8fafc" stroke="#93c5fd" strokeWidth={0.8} />
              <Geographies geography={countryTopology}>
                {({ geographies }) => (
                  <>
                    {geographies.map((geography) => {
                      const geographyName = getGeographyName(geography);
                      const country = countriesByTopologyKey.get(
                        normalizeCountryKey(geographyName),
                      );
                      const isSelected = country?.id === selectedCountry.id;
                      const isHovered = country?.id === hoveredCountry?.id;
                      const color = country
                        ? getSubregionColor(country.subregion, mapData.countries)
                        : "#cbd5e1";

                      return (
                        <Geography
                          key={geography.rsmKey}
                          geography={geography}
                          className={country ? "cursor-pointer" : undefined}
                          aria-label={country ? `Show ${country.name} details` : geographyName}
                          tabIndex={country ? 0 : -1}
                          onClick={
                            country ? () => setSelectedCountryId(country.id) : undefined
                          }
                          onMouseEnter={
                            country ? () => setHoveredCountryId(country.id) : undefined
                          }
                          onMouseLeave={
                            country
                              ? () =>
                                  setHoveredCountryId((current) =>
                                    current === country.id ? null : current,
                                  )
                              : undefined
                          }
                          onFocus={country ? () => setHoveredCountryId(country.id) : undefined}
                          onBlur={
                            country
                              ? () =>
                                  setHoveredCountryId((current) =>
                                    current === country.id ? null : current,
                                  )
                              : undefined
                          }
                          onKeyDown={
                            country
                              ? (event) => {
                                  if (event.key === "Enter" || event.key === " ") {
                                    event.preventDefault();
                                    setSelectedCountryId(country.id);
                                  }
                                }
                              : undefined
                          }
                          style={{
                            default: {
                              fill: country ? withAlpha(color, 0.34) : "#e2e8f0",
                              outline: "none",
                              stroke: country ? color : "#cbd5e1",
                              strokeWidth: country ? (isSelected ? 1.7 : 0.8) : 0.45,
                              opacity: country ? 1 : 0.55,
                            },
                            hover: {
                              fill: country ? withAlpha(color, 0.62) : "#e2e8f0",
                              outline: "none",
                              stroke: country ? color : "#cbd5e1",
                              strokeWidth: country ? 1.5 : 0.45,
                            },
                            pressed: {
                              fill: country ? withAlpha(color, 0.78) : "#e2e8f0",
                              outline: "none",
                              stroke: country ? color : "#cbd5e1",
                              strokeWidth: country ? 1.8 : 0.45,
                            },
                            focused: {
                              fill: country
                                ? withAlpha(color, isSelected || isHovered ? 0.72 : 0.54)
                                : "#e2e8f0",
                              outline: "none",
                              stroke: country ? color : "#cbd5e1",
                              strokeWidth: country ? 1.5 : 0.45,
                            },
                          }}
                        />
                      );
                    })}

                    {geographies.map((geography) => {
                      const geographyName = getGeographyName(geography);
                      const country = countriesByTopologyKey.get(
                        normalizeCountryKey(geographyName),
                      );
                      if (!country?.isAnchor) return null;

                      const coordinates = getBestGeographyCoordinates(geography);
                      if (!coordinates) return null;

                      return (
                        <Marker
                          key={`${country.id}-anchor`}
                          coordinates={coordinates}
                          pointerEvents="none"
                        >
                          <circle r="4.3" fill="#ffffff" opacity="0.9" />
                          <path
                            d="M0 -4.3 L1.3 -1.2 L4.6 -1.1 L2 0.9 L3 4.1 L0 2.4 L-3 4.1 L-2 0.9 L-4.6 -1.1 L-1.3 -1.2 Z"
                            fill="#f59e0b"
                            stroke="#78350f"
                            strokeWidth="0.4"
                          />
                        </Marker>
                      );
                    })}
                  </>
                )}
              </Geographies>
            </ComposableMap>

            <div className="pointer-events-none absolute inset-x-3 bottom-3 z-10 rounded-xl border bg-background/92 p-3 shadow-lg backdrop-blur">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-[11px] font-medium uppercase tracking-wide text-primary/80">
                    Map focus
                  </p>
                  <p className="mt-1 text-sm font-semibold text-foreground">{activeCountry.name}</p>
                </div>
                <span
                  className="rounded-full px-2 py-1 text-[11px] font-medium text-white"
                  style={{
                    backgroundColor: getSubregionColor(activeCountry.subregion, mapData.countries),
                  }}
                >
                  {activeCountry.subregion}
                </span>
              </div>
              <p className="mt-2 text-xs text-muted-foreground">
                {activeCountry.capital} / {activeCountry.geographyType}
              </p>
              <p className="mt-2 text-xs leading-relaxed text-foreground/85">
                {activeCountry.keyFact}
              </p>
            </div>
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

          <div className="mt-4 rounded-xl border bg-background/80 p-3">
            <p className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
              Country roster
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              {mapData.countries.map((country) => {
                const color = getSubregionColor(country.subregion, mapData.countries);
                const isSelected = country.id === selectedCountry.id;

                return (
                  <button
                    key={country.id}
                    type="button"
                    className="rounded-full border px-2.5 py-1 text-xs transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
                    style={{
                      borderColor: withAlpha(color, 0.65),
                      backgroundColor: isSelected ? withAlpha(color, 0.18) : "transparent",
                      color: isSelected ? color : "rgb(71 85 105)",
                    }}
                    onClick={() => setSelectedCountryId(country.id)}
                    onMouseEnter={() => setHoveredCountryId(country.id)}
                    onMouseLeave={() =>
                      setHoveredCountryId((current) =>
                        current === country.id ? null : current,
                      )
                    }
                  >
                    {country.name}
                  </button>
                );
              })}
            </div>
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

function getGeographyName(geography: { properties?: Record<string, unknown> | null }): string {
  const name = geography.properties?.name;
  return typeof name === "string" ? name : "";
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

function withAlpha(hexColor: string, alpha: number): string {
  const normalized = hexColor.replace("#", "");
  if (normalized.length !== 6) return hexColor;

  const red = Number.parseInt(normalized.slice(0, 2), 16);
  const green = Number.parseInt(normalized.slice(2, 4), 16);
  const blue = Number.parseInt(normalized.slice(4, 6), 16);

  return `rgba(${red}, ${green}, ${blue}, ${alpha})`;
}
