import type {
  CurriculumChartBlock,
  CurriculumComparisonTableBlock,
  CurriculumDiagramBlock,
  CurriculumFrameworkPillar,
  CurriculumFrameworkBlock,
  CurriculumProcessStep,
  CurriculumProcessFlowBlock,
  CurriculumVisualBlock,
  CurriculumVisualBlockType,
  CurriculumVisualEdge,
  CurriculumVisualNode,
} from "@/types/curriculum";

const VISUAL_LANGUAGES = new Set<CurriculumVisualBlockType>([
  "diagram",
  "process-flow",
  "framework",
  "comparison-table",
  "chart",
]);

export function getCurriculumVisualLanguage(className?: string): string | null {
  if (!className) return null;
  const match = className.match(/language-([a-z-]+)/i);
  return match?.[1]?.toLowerCase() ?? null;
}

export function parseCurriculumVisualBlock(
  language: string | null,
  rawText: string,
): CurriculumVisualBlock | null {
  if (!language) return null;
  if (language !== "visual" && !VISUAL_LANGUAGES.has(language as CurriculumVisualBlockType)) {
    return null;
  }

  let parsed: unknown;
  try {
    parsed = JSON.parse(rawText.trim());
  } catch {
    return null;
  }

  if (!isRecord(parsed)) return null;

  const type =
    language === "visual"
      ? asVisualType(parsed.type)
      : (language as CurriculumVisualBlockType);

  if (!type) return null;

  switch (type) {
    case "diagram":
      return parseDiagramBlock(parsed);
    case "process-flow":
      return parseProcessFlowBlock(parsed);
    case "framework":
      return parseFrameworkBlock(parsed);
    case "comparison-table":
      return parseComparisonTableBlock(parsed);
    case "chart":
      return parseChartBlock(parsed);
    default:
      return null;
  }
}

function parseDiagramBlock(input: Record<string, unknown>): CurriculumDiagramBlock | null {
  const nodes = asArray(input.nodes)
    ?.map(parseNode)
    .filter((node): node is CurriculumVisualNode => node !== null);
  if (!nodes || nodes.length === 0) return null;

  const edges = asArray(input.edges)
    ?.map(parseEdge)
    .filter((edge): edge is CurriculumVisualEdge => edge !== null);

  return {
    type: "diagram",
    title: asOptionalString(input.title),
    note: asOptionalString(input.note),
    nodes,
    edges,
  };
}

function parseProcessFlowBlock(input: Record<string, unknown>): CurriculumProcessFlowBlock | null {
  const rawSteps = asArray(input.steps);
  if (!rawSteps) return null;

  const steps: CurriculumProcessStep[] = [];
  for (const [index, step] of rawSteps.entries()) {
    if (!isRecord(step)) continue;
    const title = asOptionalString(step.title);
    if (!title) continue;
    steps.push({
      id: asOptionalString(step.id) ?? `step-${index + 1}`,
      title,
      detail: asOptionalString(step.detail),
      emphasis: asOptionalString(step.emphasis),
    });
  }

  if (!steps || steps.length === 0) return null;

  return {
    type: "process-flow",
    title: asOptionalString(input.title),
    note: asOptionalString(input.note),
    steps,
  };
}

function parseFrameworkBlock(input: Record<string, unknown>): CurriculumFrameworkBlock | null {
  const rawPillars = asArray(input.pillars);
  if (!rawPillars) return null;

  const pillars: CurriculumFrameworkPillar[] = [];
  for (const pillar of rawPillars) {
    if (!isRecord(pillar)) continue;
    const title = asOptionalString(pillar.title);
    if (!title) continue;
    pillars.push({
      title,
      detail: asOptionalString(pillar.detail),
      bullets: asStringArray(pillar.bullets),
    });
  }

  if (!pillars || pillars.length === 0) return null;

  return {
    type: "framework",
    title: asOptionalString(input.title),
    note: asOptionalString(input.note),
    pillars,
  };
}

function parseComparisonTableBlock(
  input: Record<string, unknown>,
): CurriculumComparisonTableBlock | null {
  const columns = asArray(input.columns)
    ?.map((column) => {
      if (!isRecord(column)) return null;
      const key = asOptionalString(column.key);
      const label = asOptionalString(column.label);
      if (!key || !label) return null;
      return { key, label };
    })
    .filter(
      (
        column,
      ): column is {
        key: string;
        label: string;
      } => column !== null,
    );
  const rows = asArray(input.rows)
    ?.map((row) => sanitizeDataRow(row))
    .filter((row): row is Record<string, string | number> => row !== null);

  if (!columns || columns.length === 0 || !rows || rows.length === 0) return null;

  return {
    type: "comparison-table",
    title: asOptionalString(input.title),
    note: asOptionalString(input.note),
    columns,
    rows,
  };
}

function parseChartBlock(input: Record<string, unknown>): CurriculumChartBlock | null {
  const chartType = asChartType(input.chartType);
  const xLabel = asOptionalString(input.xLabel);
  const data = asArray(input.data)
    ?.map((row) => sanitizeDataRow(row))
    .filter((row): row is Record<string, string | number> => row !== null);

  if (!chartType || !xLabel || !data || data.length === 0) return null;

  const inferredSeries = Array.from(
    new Set(data.flatMap((row) => Object.keys(row).filter((key) => key !== xLabel))),
  );
  const series = asStringArray(input.series) ?? inferredSeries;
  if (series.length === 0) return null;

  return {
    type: "chart",
    title: asOptionalString(input.title),
    note: asOptionalString(input.note),
    chartType,
    xLabel,
    yLabel: asOptionalString(input.yLabel),
    series,
    data,
  };
}

function parseNode(input: unknown): CurriculumVisualNode | null {
  if (!isRecord(input)) return null;
  const id = asOptionalString(input.id);
  const title = asOptionalString(input.title);
  if (!id || !title) return null;

  return {
    id,
    title,
    detail: asOptionalString(input.detail),
    column: asOptionalNumber(input.column),
    row: asOptionalNumber(input.row),
    tone: asNodeTone(input.tone),
  };
}

function parseEdge(input: unknown): CurriculumVisualEdge | null {
  if (!isRecord(input)) return null;
  const from = asOptionalString(input.from);
  const to = asOptionalString(input.to);
  if (!from || !to) return null;
  return {
    from,
    to,
    label: asOptionalString(input.label),
  };
}

function sanitizeDataRow(input: unknown): Record<string, string | number> | null {
  if (!isRecord(input)) return null;
  const row: Record<string, string | number> = {};
  for (const [key, value] of Object.entries(input)) {
    if (typeof value === "string" || typeof value === "number") {
      row[key] = value;
    }
  }
  return Object.keys(row).length > 0 ? row : null;
}

function asArray(value: unknown): unknown[] | null {
  return Array.isArray(value) ? value : null;
}

function asOptionalString(value: unknown): string | undefined {
  return typeof value === "string" && value.trim() ? value.trim() : undefined;
}

function asOptionalNumber(value: unknown): number | undefined {
  return typeof value === "number" && Number.isFinite(value) ? value : undefined;
}

function asStringArray(value: unknown): string[] | undefined {
  if (!Array.isArray(value)) return undefined;
  const items = value
    .map((item) => (typeof item === "string" && item.trim() ? item.trim() : null))
    .filter((item): item is string => item !== null);
  return items.length > 0 ? items : undefined;
}

function asVisualType(value: unknown): CurriculumVisualBlockType | null {
  return typeof value === "string" && VISUAL_LANGUAGES.has(value as CurriculumVisualBlockType)
    ? (value as CurriculumVisualBlockType)
    : null;
}

function asChartType(value: unknown): CurriculumChartBlock["chartType"] | null {
  return value === "line" || value === "bar" || value === "scatter" ? value : null;
}

function asNodeTone(value: unknown): CurriculumVisualNode["tone"] | undefined {
  return value === "default" || value === "accent" || value === "muted" ? value : undefined;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
