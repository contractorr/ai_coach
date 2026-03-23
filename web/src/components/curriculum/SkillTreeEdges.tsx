"use client";

import { useEffect, useRef, useState } from "react";
import type { SkillTreeEdge } from "@/types/curriculum";

interface SkillTreeEdgesProps {
  edges: SkillTreeEdge[];
  nodePositions: Map<string, DOMRect>;
  containerRect: DOMRect | null;
  getTrackColor: (nodeId: string) => string;
}

interface EdgePath {
  key: string;
  d: string;
  color: string;
}

export function SkillTreeEdges({
  edges,
  nodePositions,
  containerRect,
  getTrackColor,
}: SkillTreeEdgesProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [paths, setPaths] = useState<EdgePath[]>([]);

  useEffect(() => {
    if (!containerRect || nodePositions.size === 0) return;

    const newPaths: EdgePath[] = [];
    for (const edge of edges) {
      const sourceRect = nodePositions.get(edge.source);
      const targetRect = nodePositions.get(edge.target);
      if (!sourceRect || !targetRect) continue;

      const sx = sourceRect.left - containerRect.left + sourceRect.width / 2;
      const sy = sourceRect.top - containerRect.top + sourceRect.height;
      const tx = targetRect.left - containerRect.left + targetRect.width / 2;
      const ty = targetRect.top - containerRect.top;
      const mid = (sy + ty) / 2;

      newPaths.push({
        key: `${edge.source}-${edge.target}`,
        d: `M ${sx},${sy} C ${sx},${mid} ${tx},${mid} ${tx},${ty}`,
        color: getTrackColor(edge.source),
      });
    }
    setPaths(newPaths);
  }, [edges, nodePositions, containerRect, getTrackColor]);

  if (!containerRect) return null;

  return (
    <svg
      ref={svgRef}
      className="pointer-events-none absolute inset-0"
      width={containerRect.width}
      height={containerRect.height}
      style={{ overflow: "visible" }}
    >
      {paths.map((p) => (
        <path
          key={p.key}
          d={p.d}
          fill="none"
          stroke={p.color}
          strokeWidth={1.5}
          strokeOpacity={0.6}
        />
      ))}
    </svg>
  );
}
