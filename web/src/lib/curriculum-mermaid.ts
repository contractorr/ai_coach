import type {
  CurriculumDiagramBlock,
  CurriculumProcessFlowBlock,
  CurriculumTimelineBlock,
  CurriculumVisualNode,
} from "@/types/curriculum";

type MermaidBlock = CurriculumDiagramBlock | CurriculumProcessFlowBlock | CurriculumTimelineBlock;

export function toCurriculumMermaidDefinition(block: MermaidBlock): string {
  switch (block.type) {
    case "diagram":
      return buildDiagramDefinition(block);
    case "process-flow":
      return buildProcessFlowDefinition(block);
    case "timeline":
      return buildTimelineDefinition(block);
  }
}

export function getDiagramNodesInDisplayOrder(
  nodes: CurriculumVisualNode[],
): CurriculumVisualNode[] {
  return [...nodes].sort((left, right) => {
    const rowDelta = (left.row ?? Number.MAX_SAFE_INTEGER) - (right.row ?? Number.MAX_SAFE_INTEGER);
    if (rowDelta !== 0) return rowDelta;

    const columnDelta =
      (left.column ?? Number.MAX_SAFE_INTEGER) - (right.column ?? Number.MAX_SAFE_INTEGER);
    if (columnDelta !== 0) return columnDelta;

    return left.title.localeCompare(right.title);
  });
}

function buildDiagramDefinition(block: CurriculumDiagramBlock): string {
  const nodes = getDiagramNodesInDisplayOrder(block.nodes);
  const nodeIds = new Map(nodes.map((node) => [node.id, `node_${sanitizeId(node.id)}`]));
  const direction = inferDiagramDirection(nodes);
  const lines = [
    `flowchart ${direction}`,
    ...getFlowchartClassDefs(),
  ];

  for (const node of nodes) {
    const nodeId = nodeIds.get(node.id);
    if (!nodeId) continue;
    lines.push(`${nodeId}["${escapeFlowchartLabel(node.title)}"]`);
  }

  for (const edge of block.edges ?? []) {
    const fromId = nodeIds.get(edge.from);
    const toId = nodeIds.get(edge.to);
    if (!fromId || !toId) continue;

    const connector = edge.label
      ? ` -->|${escapeFlowchartLabel(edge.label)}| `
      : " --> ";
    lines.push(`${fromId}${connector}${toId}`);
  }

  for (const node of nodes) {
    const nodeId = nodeIds.get(node.id);
    if (!nodeId) continue;
    lines.push(`class ${nodeId} ${toMermaidTone(node.tone)};`);
  }

  return lines.join("\n");
}

function buildProcessFlowDefinition(block: CurriculumProcessFlowBlock): string {
  const lines = [
    "flowchart LR",
    ...getFlowchartClassDefs(),
  ];

  const stepIds = block.steps.map((step, index) => ({
    sourceId: step.id,
    mermaidId: `step_${sanitizeId(step.id || `step-${index + 1}`)}`,
    title: step.title,
  }));

  for (const [index, step] of stepIds.entries()) {
    lines.push(`${step.mermaidId}["${escapeFlowchartLabel(step.title)}"]`);
    lines.push(`class ${step.mermaidId} process;`);

    if (index < stepIds.length - 1) {
      lines.push(`${step.mermaidId} --> ${stepIds[index + 1]?.mermaidId}`);
    }
  }

  return lines.join("\n");
}

function buildTimelineDefinition(block: CurriculumTimelineBlock): string {
  const lines = ["timeline"];

  for (const entry of block.entries) {
    lines.push(`    ${escapeTimelineText(entry.period)} : ${escapeTimelineText(entry.title)}`);
    if (entry.emphasis) {
      lines.push(`         : ${escapeTimelineText(entry.emphasis)}`);
    }
  }

  return lines.join("\n");
}

function inferDiagramDirection(nodes: CurriculumVisualNode[]): "LR" | "TB" {
  const rows = new Set(nodes.map((node) => node.row).filter((value): value is number => value !== undefined));
  const columns = new Set(
    nodes.map((node) => node.column).filter((value): value is number => value !== undefined),
  );

  return columns.size >= rows.size ? "LR" : "TB";
}

function getFlowchartClassDefs(): string[] {
  return [
    "classDef default fill:#ffffff,stroke:#cbd5e1,color:#0f172a,stroke-width:1.2px;",
    "classDef accent fill:#dbeafe,stroke:#2563eb,color:#0f172a,stroke-width:1.6px;",
    "classDef muted fill:#f8fafc,stroke:#94a3b8,color:#334155,stroke-width:1.1px;",
    "classDef process fill:#eff6ff,stroke:#2563eb,color:#0f172a,stroke-width:1.4px;",
  ];
}

function toMermaidTone(tone: CurriculumVisualNode["tone"]): string {
  switch (tone) {
    case "accent":
      return "accent";
    case "muted":
      return "muted";
    default:
      return "default";
  }
}

function sanitizeId(value: string): string {
  return value
    .replace(/[^a-zA-Z0-9_-]+/g, "_")
    .replace(/^([^a-zA-Z_])/, "_$1");
}

function escapeFlowchartLabel(value: string): string {
  return value.replace(/\\/g, "\\\\").replace(/"/g, '\\"');
}

function escapeTimelineText(value: string): string {
  return value.replace(/:/g, " -").trim();
}
