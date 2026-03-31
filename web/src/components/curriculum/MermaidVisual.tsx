"use client";

import { useEffect, useId, useState } from "react";

let mermaidInitialized = false;

export function MermaidVisual({
  definition,
  ariaLabel,
}: {
  definition: string;
  ariaLabel: string;
}) {
  const [svg, setSvg] = useState<string>("");
  const [hasError, setHasError] = useState(false);
  const renderId = useId().replace(/:/g, "");

  useEffect(() => {
    let cancelled = false;

    async function renderDiagram() {
      try {
        const mermaid = (await import("mermaid")).default;

        if (!mermaidInitialized) {
          mermaid.initialize({
            startOnLoad: false,
            securityLevel: "strict",
            theme: "base",
            fontFamily: "inherit",
            flowchart: {
              useMaxWidth: true,
              htmlLabels: false,
              curve: "basis",
            },
            themeVariables: {
              primaryColor: "#eff6ff",
              primaryTextColor: "#0f172a",
              primaryBorderColor: "#2563eb",
              lineColor: "#94a3b8",
              secondaryColor: "#f8fafc",
              tertiaryColor: "#ffffff",
              fontSize: "14px",
            },
          });
          mermaidInitialized = true;
        }

        await mermaid.parse(definition);
        const { svg: renderedSvg } = await mermaid.render(`curriculum-mermaid-${renderId}`, definition);

        if (!cancelled) {
          setSvg(renderedSvg);
          setHasError(false);
        }
      } catch {
        if (!cancelled) {
          setHasError(true);
          setSvg("");
        }
      }
    }

    void renderDiagram();

    return () => {
      cancelled = true;
    };
  }, [definition, renderId]);

  if (hasError) {
    return (
      <div className="rounded-xl border border-dashed bg-muted/10 p-4 text-sm text-muted-foreground">
        This visual could not be rendered.
      </div>
    );
  }

  return (
    <div
      aria-label={ariaLabel}
      className="overflow-x-auto rounded-2xl border bg-background p-4 shadow-sm [&_.edgeLabel]:fill-foreground [&_.label]:text-foreground [&_.node_rect]:rounded-xl [&_svg]:h-auto [&_svg]:min-w-[640px] [&_svg]:w-full"
      dangerouslySetInnerHTML={svg ? { __html: svg } : undefined}
      role="img"
    />
  );
}
