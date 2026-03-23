/**
 * Heuristic parser that extracts structured chart data from ASCII text.
 * No LLM calls — pure pattern matching.
 */

export type ChartType = "line" | "bar" | "scatter" | "none";

export interface ParsedChartData {
  chartType: ChartType;
  title: string;
  xLabel: string;
  yLabel: string;
  data: Array<Record<string, string | number>>;
  series: string[]; // numeric series keys in data objects
}

/**
 * Try to extract chart data from ASCII text.
 * Returns null if no parseable data detected.
 */
export function parseChartData(text: string): ParsedChartData | null {
  return parseTableData(text) ?? parseAxisDiagram(text);
}

// ---------------------------------------------------------------------------
// Strategy 1: Tables with numeric columns → bar or line chart
// ---------------------------------------------------------------------------

const SEP_RE = /^[\s|─\-:=+]+$/;

function parseTableData(text: string): ParsedChartData | null {
  const lines = text.split("\n").filter((l) => l.trim());
  if (lines.length < 3) return null;

  // Find header + separator pair
  let headerIdx = -1;
  for (let i = 0; i < lines.length - 1; i++) {
    if (SEP_RE.test(lines[i + 1])) {
      headerIdx = i;
      break;
    }
  }
  if (headerIdx < 0) return null;

  const headerLine = lines[headerIdx];
  const headers = splitRow(headerLine);
  if (headers.length < 2) return null;

  // Collect data rows (skip header + separator)
  const dataRows: string[][] = [];
  for (let i = headerIdx + 2; i < lines.length; i++) {
    if (SEP_RE.test(lines[i])) continue; // skip trailing separators
    const cells = splitRow(lines[i]);
    if (cells.length >= headers.length) {
      dataRows.push(cells.slice(0, headers.length));
    }
  }

  if (dataRows.length < 3) return null;

  // Identify numeric columns (≥70% numeric values)
  const numericCols: number[] = [];
  const nonNumericCols: number[] = [];
  for (let col = 0; col < headers.length; col++) {
    let numCount = 0;
    for (const row of dataRows) {
      if (isNumericCell(row[col])) numCount++;
    }
    if (numCount / dataRows.length >= 0.7) {
      numericCols.push(col);
    } else {
      nonNumericCols.push(col);
    }
  }

  if (numericCols.length === 0) return null;

  // First non-numeric column = X axis; if none, use row index
  const xCol = nonNumericCols.length > 0 ? nonNumericCols[0] : -1;
  const xLabel = xCol >= 0 ? headers[xCol] : "Index";
  const series = numericCols.map((c) => headers[c]);

  const data: Array<Record<string, string | number>> = dataRows.map((row, idx) => {
    const record: Record<string, string | number> = {};
    record[xLabel] = xCol >= 0 ? row[xCol] : idx + 1;
    for (const col of numericCols) {
      record[headers[col]] = parseNumericCell(row[col]);
    }
    return record;
  });

  // Determine chart type: temporal X → line, else bar
  const chartType = isTemporal(dataRows.map((r) => (xCol >= 0 ? r[xCol] : "")))
    ? "line"
    : "bar";

  return {
    chartType,
    title: "",
    xLabel,
    yLabel: series.length === 1 ? series[0] : "",
    data,
    series,
  };
}

/** Split a row by pipes or 2+ spaces. */
function splitRow(line: string): string[] {
  // Pipe-delimited
  if (line.includes("|")) {
    return line
      .split("|")
      .map((s) => s.trim())
      .filter(Boolean);
  }
  // Multi-space delimited
  return line
    .trim()
    .split(/\s{2,}/)
    .map((s) => s.trim())
    .filter(Boolean);
}

function isNumericCell(s: string): boolean {
  const cleaned = s.replace(/[$%,]/g, "").trim();
  return cleaned !== "" && !isNaN(Number(cleaned));
}

function parseNumericCell(s: string): number {
  return Number(s.replace(/[$%,]/g, "").trim()) || 0;
}

function isTemporal(values: string[]): boolean {
  const yearRe = /^(19|20)\d{2}$/;
  const dateRe = /^\d{1,4}[-/]\d{1,2}([-/]\d{1,4})?$/;
  const matches = values.filter((v) => yearRe.test(v.trim()) || dateRe.test(v.trim()));
  return matches.length / values.length >= 0.5;
}

// ---------------------------------------------------------------------------
// Strategy 2: Axis-labeled diagrams → line or scatter chart
// ---------------------------------------------------------------------------

const Y_AXIS_RE = /^\s*([+-]?\d+[%$]?)\s*[┤│|]/;
const X_BOTTOM_RE = /[└└+][\s─\-]+/;

function parseAxisDiagram(text: string): ParsedChartData | null {
  const lines = text.split("\n");

  // Extract Y-axis values and their line indices
  const yEntries: { value: number; lineIdx: number }[] = [];
  let axisCol = -1;
  for (let i = 0; i < lines.length; i++) {
    const m = lines[i].match(Y_AXIS_RE);
    if (m) {
      yEntries.push({ value: parseNumericCell(m[1]), lineIdx: i });
      // axis column = position of the separator char
      const sepIdx = lines[i].search(/[┤│|]/);
      if (sepIdx > axisCol) axisCol = sepIdx;
    }
  }

  if (yEntries.length < 2 || axisCol < 0) return null;

  // Find X-axis line (bottom border)
  let xAxisLineIdx = -1;
  for (let i = lines.length - 1; i >= 0; i--) {
    if (X_BOTTOM_RE.test(lines[i])) {
      xAxisLineIdx = i;
      break;
    }
  }

  // Extract X labels from line after x-axis
  let xLabels: string[] = [];
  if (xAxisLineIdx >= 0 && xAxisLineIdx + 1 < lines.length) {
    xLabels = lines[xAxisLineIdx + 1]
      .trim()
      .split(/\s{2,}/)
      .map((s) => s.trim())
      .filter(Boolean);
  }

  // Scan plot area for markers
  const markers = /[●○•*xX▪▫■□◆◇#@]/;
  const dataPoints: { x: number; y: number }[] = [];

  const yMin = Math.min(...yEntries.map((e) => e.value));
  const yMax = Math.max(...yEntries.map((e) => e.value));
  const yLineMin = Math.min(...yEntries.map((e) => e.lineIdx));
  const yLineMax = Math.max(...yEntries.map((e) => e.lineIdx));

  if (yLineMax === yLineMin) return null;

  for (let i = yLineMin; i <= yLineMax; i++) {
    const line = lines[i];
    if (!line) continue;
    for (let j = axisCol + 1; j < line.length; j++) {
      if (markers.test(line[j])) {
        // Interpolate Y value from line position
        const yFrac = (i - yLineMin) / (yLineMax - yLineMin);
        const yVal = yMax - yFrac * (yMax - yMin);
        // X position = column offset from axis
        const xPos = j - axisCol - 1;
        dataPoints.push({ x: xPos, y: Math.round(yVal * 100) / 100 });
      }
    }
  }

  if (dataPoints.length < 3) return null;

  // Sort by x position
  dataPoints.sort((a, b) => a.x - b.x);

  // Map x positions to labels if available
  const data: Array<Record<string, string | number>> = dataPoints.map((pt, idx) => ({
    x: xLabels[idx] ?? pt.x,
    y: pt.y,
  }));

  // Determine type: scatter if data points are irregularly spaced, else line
  const xPositions = dataPoints.map((p) => p.x);
  const gaps = xPositions.slice(1).map((x, i) => x - xPositions[i]);
  const avgGap = gaps.reduce((a, b) => a + b, 0) / gaps.length;
  const variance = gaps.reduce((a, b) => a + (b - avgGap) ** 2, 0) / gaps.length;
  const chartType: ChartType = variance > avgGap * avgGap * 0.5 ? "scatter" : "line";

  return {
    chartType,
    title: "",
    xLabel: "x",
    yLabel: "y",
    data,
    series: ["y"],
  };
}
