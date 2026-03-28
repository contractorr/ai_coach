"use client";

import Link from "next/link";
import { useMemo, useState, type ReactNode } from "react";
import ReactMarkdown, { type Components } from "react-markdown";
import remarkGfm from "remark-gfm";
import { BarChart3 } from "lucide-react";
import { parseChartData, type ParsedChartData } from "@/lib/chart-parser";
import { getCurriculumVisualLanguage, parseCurriculumVisualBlock } from "@/lib/curriculum-visuals";
import { ChartOverlay } from "./ChartOverlay";
import { CurriculumVisualBlockRenderer } from "./CurriculumVisualBlock";

/**
 * Detect if a code block contains an ASCII diagram.
 * Checks for box-drawing chars (U+2500-257F), ASCII art patterns,
 * tree structures, and axis labels.
 */
function isAsciiDiagram(text: string): boolean {
  // Box-drawing characters
  if (/[\u2500-\u257F]/.test(text)) return true;
  // ASCII art boxes: +---+, |...|
  if (/[+|]\-{3,}[+|]/.test(text)) return true;
  // Tree patterns: ├── or └──
  if (/[├└]──/.test(text)) return true;
  // Arrows and flow: -->, ==>, |, V, ^
  const lines = text.split("\n");
  let arrowCount = 0;
  let pipeCount = 0;
  for (const line of lines) {
    if (/-->|==>|<--|<==/.test(line)) arrowCount++;
    if (/^\s*\|/.test(line)) pipeCount++;
  }
  if (arrowCount >= 2 || pipeCount >= 4) return true;
  // Axis patterns: x-axis labels with numbers
  if (/\d+\s+\d+\s+\d+/.test(text) && /[|─\-]{5,}/.test(text)) return true;
  return false;
}

/**
 * Detect if text is a numeric/data table (aligned columns with separators).
 */
function isDataTable(text: string): boolean {
  const lines = text.split("\n").filter((l) => l.trim());
  if (lines.length < 3) return false;
  // Check for separator line with ─ or -
  const hasSep = lines.some((l) => /^[\s─\-|:+]+$/.test(l));
  // Check for aligned columns (multiple consecutive spaces)
  const hasColumns = lines.filter((l) => /\S\s{2,}\S/.test(l)).length >= 2;
  return hasSep && hasColumns;
}

function extractTextFromChildren(children: ReactNode): string {
  if (typeof children === "string") return children;
  if (Array.isArray(children)) return children.map(extractTextFromChildren).join("");
  if (children && typeof children === "object" && "props" in children) {
    return extractTextFromChildren((children as { props: { children?: ReactNode } }).props.children);
  }
  return "";
}

interface CurriculumRendererProps {
  content: string;
  guideId?: string;
}

function resolveCurriculumHref(href: string | undefined, guideId?: string): string | null {
  if (!href) return null;
  if (/^(https?:|mailto:|tel:)/i.test(href) || href.startsWith("#")) return null;

  const [rawPath, rawHash] = href.split("#", 2);
  const normalizedPath = rawPath.replace(/\\/g, "/").trim();
  const normalizedLower = normalizedPath.toLowerCase();
  if (!normalizedLower.endsWith(".md") && !normalizedLower.endsWith(".mdx")) return null;

  const segments = normalizedPath.split("/").filter(Boolean);
  if (segments.length === 0) return null;

  const chapterSegment = segments[segments.length - 1];
  const chapterId = chapterSegment.replace(/\.(md|mdx)$/i, "");
  if (!chapterId) return null;

  let resolvedGuideId: string | undefined;
  if (segments.length === 1 || normalizedPath.startsWith("./") || normalizedPath.startsWith("../")) {
    resolvedGuideId = guideId;
  } else {
    resolvedGuideId = segments[segments.length - 2];
  }

  if (!resolvedGuideId) return null;

  const hash = rawHash ? `#${rawHash}` : "";
  return `/learn/${resolvedGuideId}/${chapterId}${hash}`;
}

export function CurriculumRenderer({ content, guideId }: CurriculumRendererProps) {
  const components: Components = useMemo(
    () => ({
      // Enhanced code blocks: detect diagrams and style accordingly
      pre({ children }) {
        return <>{children}</>;
      },

      code({ children, className }) {
        const text = extractTextFromChildren(children);
        const visualLanguage = getCurriculumVisualLanguage(className);
        const visualBlock = parseCurriculumVisualBlock(visualLanguage, text);
        const isInline = !className && !text.includes("\n");

        if (isInline) {
          return (
            <code className="rounded bg-muted px-1.5 py-0.5 text-[13px] font-mono text-primary/90">
              {children}
            </code>
          );
        }

        if (visualBlock) {
          return <CurriculumVisualBlockRenderer block={visualBlock} />;
        }

        const isDiagram = isAsciiDiagram(text);
        const isTable = isDataTable(text);

        if (isDiagram || isTable) {
          return (
            <div className="my-4 overflow-x-auto rounded-lg border bg-slate-50 dark:bg-slate-900 p-4">
              <pre
                className="font-mono text-[13px] leading-[1.4] whitespace-pre"
                style={{ tabSize: 4 }}
              >
                {isDiagram ? (
                  <DiagramBlock text={text} />
                ) : (
                  <TableBlock text={text} />
                )}
              </pre>
            </div>
          );
        }

        // Regular code block
        return (
          <div className="my-3 overflow-x-auto rounded-lg border bg-muted/50 p-4">
            <pre className="font-mono text-[13px] leading-relaxed whitespace-pre">
              <code className={className}>{children}</code>
            </pre>
          </div>
        );
      },

      // Tables: enhanced with alternating rows
      table({ children }) {
        return (
          <div className="my-4 overflow-x-auto rounded-lg border">
            <table className="w-full text-sm">{children}</table>
          </div>
        );
      },
      thead({ children }) {
        return <thead className="bg-muted/60 border-b">{children}</thead>;
      },
      th({ children }) {
        return (
          <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            {children}
          </th>
        );
      },
      tr({ children }) {
        return <tr className="border-b last:border-0 even:bg-muted/30">{children}</tr>;
      },
      td({ children }) {
        return <td className="px-3 py-2 text-sm">{children}</td>;
      },

      // Headings: add scroll-margin for TOC linking
      h1({ children }) {
        return <h1 className="sr-only">{children}</h1>;
      },
      h2({ children }) {
        return (
          <h2 className="scroll-mt-20 flex items-center gap-2 text-base font-semibold mt-8 mb-3 pb-2 border-b border-border/60">
            <span className="inline-block w-1 h-5 rounded-full bg-primary/60 shrink-0" />
            {children}
          </h2>
        );
      },
      h3({ children }) {
        return <h3 className="scroll-mt-20 text-sm font-semibold mt-6 mb-2 text-foreground/80">{children}</h3>;
      },

      // Blockquotes: styled as callouts
      blockquote({ children }) {
        return (
          <blockquote className="my-4 border-l-4 border-primary/40 bg-primary/5 rounded-r-lg pl-4 pr-3 py-3 text-sm italic text-foreground/80">
            {children}
          </blockquote>
        );
      },

      // Paragraphs, lists, links, hr, inline styles
      p({ children }) {
        return <p className="my-3 text-sm leading-relaxed">{children}</p>;
      },
      ul({ children }) {
        return <ul className="my-3 ml-6 list-disc space-y-1.5 text-sm">{children}</ul>;
      },
      ol({ children }) {
        return <ol className="my-3 ml-6 list-decimal space-y-1.5 text-sm">{children}</ol>;
      },
      li({ children }) {
        return <li className="leading-relaxed">{children}</li>;
      },
      a({ children, href }) {
        const internalHref = resolveCurriculumHref(href, guideId);
        if (internalHref) {
          return (
            <Link
              href={internalHref}
              className="text-primary underline underline-offset-2 decoration-primary/40 hover:decoration-primary/80 transition-colors"
            >
              {children}
            </Link>
          );
        }

        return (
          <a href={href} className="text-primary underline underline-offset-2 decoration-primary/40 hover:decoration-primary/80 transition-colors">
            {children}
          </a>
        );
      },
      hr() {
        return <hr className="my-8 border-t border-border" />;
      },
      strong({ children }) {
        return <strong className="font-semibold text-foreground">{children}</strong>;
      },
      em({ children }) {
        return <em className="italic text-foreground/90">{children}</em>;
      },
    }),
    [guideId]
  );

  return (
    <ReactMarkdown components={components} remarkPlugins={[remarkGfm]}>
      {content}
    </ReactMarkdown>
  );
}

/** Chart toggle button shown when data is parseable */
function ChartToggle({
  chartData,
  showChart,
  onToggle,
}: {
  chartData: ParsedChartData;
  showChart: boolean;
  onToggle: () => void;
}) {
  if (chartData.chartType === "none") return null;
  return (
    <button
      onClick={onToggle}
      className="absolute top-2 right-2 p-1 rounded hover:bg-muted/80 text-muted-foreground hover:text-foreground transition-colors"
      title={showChart ? "Show ASCII" : "Show chart"}
    >
      <BarChart3 className="h-4 w-4" />
    </button>
  );
}

/** Render ASCII diagram with subtle styling + optional chart overlay */
function DiagramBlock({ text }: { text: string }) {
  const [showChart, setShowChart] = useState(false);
  const chartData = useMemo(() => parseChartData(text), [text]);

  if (showChart && chartData) {
    return (
      <div className="relative">
        <ChartToggle chartData={chartData} showChart={showChart} onToggle={() => setShowChart(false)} />
        <ChartOverlay data={chartData} />
      </div>
    );
  }

  return (
    <div className="relative">
      {chartData && <ChartToggle chartData={chartData} showChart={showChart} onToggle={() => setShowChart(true)} />}
      <code className="text-slate-700 dark:text-slate-300">{text}</code>
    </div>
  );
}

/** Render data table with alternating row backgrounds + optional chart overlay */
function TableBlock({ text }: { text: string }) {
  const [showChart, setShowChart] = useState(false);
  const chartData = useMemo(() => parseChartData(text), [text]);
  const lines = text.split("\n");

  if (showChart && chartData) {
    return (
      <div className="relative">
        <ChartToggle chartData={chartData} showChart={showChart} onToggle={() => setShowChart(false)} />
        <ChartOverlay data={chartData} />
      </div>
    );
  }

  return (
    <div className="relative">
      {chartData && <ChartToggle chartData={chartData} showChart={showChart} onToggle={() => setShowChart(true)} />}
      <code>
        {lines.map((line, i) => {
          const isSep = /^[\s─\-|:+]+$/.test(line);
          return (
            <span
              key={i}
              className={
                isSep
                  ? "text-muted-foreground/60"
                  : i % 2 === 0
                    ? ""
                    : "bg-muted/30"
              }
              style={{ display: "block" }}
            >
              {line}
              {"\n"}
            </span>
          );
        })}
      </code>
    </div>
  );
}
