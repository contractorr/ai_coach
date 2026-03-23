"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { toast } from "sonner";
import { Loader2, Route } from "lucide-react";
import { useToken } from "@/hooks/useToken";
import { apiFetch } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import type {
  SkillTreeResponse,
  SkillTreeNode,
  SkillTreeEdge,
  Track,
} from "@/types/curriculum";
import { SkillTreeNodeCard } from "./SkillTreeNode";
import { SkillTreeEdges } from "./SkillTreeEdges";

interface LearningPath {
  id: string;
  name: string;
  description: string;
  guideIds: string[];
  color: string;
}

const LEARNING_PATHS: LearningPath[] = [
  {
    id: "cognitive-science",
    name: "🧠 Cognitive Science",
    description: "Philosophy → Neuroscience → Psychology → Sociology",
    guideIds: [
      "01-philosophy-guide",
      "16-cognitive-neuroscience-guide",
      "18-behavioral-psychology-guide",
      "23-sociology-institutional-design-guide",
    ],
    color: "#f59e0b",
  },
  {
    id: "business-analytics",
    name: "💼 Business Analytics",
    description: "Math → Stats → Economics → MBA → Financial Services",
    guideIds: [
      "03-mathematics-pure-applied-guide",
      "04-statistics-probability-guide",
      "26-economics-guide",
      "30-mba-curriculum",
      "industry-financialservices",
    ],
    color: "#3b82f6",
  },
  {
    id: "ai-ml",
    name: "🤖 AI & Machine Learning",
    description: "Math → Stats → Computer Science → AI/ML",
    guideIds: [
      "03-mathematics-pure-applied-guide",
      "04-statistics-probability-guide",
      "36-computer-science-algorithms-guide",
      "37-ai-ml-fundamentals-guide",
    ],
    color: "#8b5cf6",
  },
  {
    id: "policy-governance",
    name: "🌍 Policy & Governance",
    description: "Philosophy → Sociology → Government → Geopolitics",
    guideIds: [
      "01-philosophy-guide",
      "18-behavioral-psychology-guide",
      "23-sociology-institutional-design-guide",
      "24-government-politics-guide",
      "35-geopolitics-guide",
    ],
    color: "#ef4444",
  },
  {
    id: "healthcare",
    name: "🏥 Healthcare",
    description: "Chemistry → Biology → Medicine → Healthcare Industry",
    guideIds: [
      "07-chemistry-biochemistry-guide",
      "13-evolutionary-biology-guide",
      "17-medicine-human-physiology-guide",
      "industry-healthcare",
    ],
    color: "#10b981",
  },
  {
    id: "data-science",
    name: "📊 Data Science",
    description: "Math → Stats → Info Theory → CS → AI/ML",
    guideIds: [
      "03-mathematics-pure-applied-guide",
      "04-statistics-probability-guide",
      "08-information-theory-complex-systems-guide",
      "36-computer-science-algorithms-guide",
      "37-ai-ml-fundamentals-guide",
    ],
    color: "#6366f1",
  },
];

export function SkillTree() {
  const token = useToken();
  const [data, setData] = useState<SkillTreeResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedTracks, setSelectedTracks] = useState<Set<string>>(new Set());
  const [selectedPath, setSelectedPath] = useState<string | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const nodeRefs = useRef<Map<string, HTMLDivElement>>(new Map());
  const [nodePositions, setNodePositions] = useState<Map<string, DOMRect>>(new Map());
  const [containerRect, setContainerRect] = useState<DOMRect | null>(null);
  const [measureTick, setMeasureTick] = useState(0);

  useEffect(() => {
    if (!token) return;
    setLoading(true);
    apiFetch<SkillTreeResponse>("/api/curriculum/tree", {}, token)
      .then(setData)
      .catch((e) => toast.error((e as Error).message))
      .finally(() => setLoading(false));
  }, [token]);

  // Measure node positions after render
  useEffect(() => {
    if (!data || !containerRef.current) return;
    const cRect = containerRef.current.getBoundingClientRect();
    const positions = new Map<string, DOMRect>();
    nodeRefs.current.forEach((el, id) => {
      positions.set(id, el.getBoundingClientRect());
    });
    setContainerRect(cRect);
    setNodePositions(positions);
  }, [data, selectedTracks, measureTick]);

  // ResizeObserver for re-measurement
  useEffect(() => {
    if (!containerRef.current) return;
    const observer = new ResizeObserver(() => setMeasureTick((t) => t + 1));
    observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, [data]);

  const toggleTrack = (trackId: string) => {
    setSelectedTracks((prev) => {
      const next = new Set(prev);
      if (next.has(trackId)) next.delete(trackId);
      else next.add(trackId);
      return next;
    });
  };

  // Split into core curriculum vs industry applications
  const { coreNodes, industryNodes } = useMemo(() => {
    if (!data) return { coreNodes: [], industryNodes: [] };
    const core: SkillTreeNode[] = [];
    const industry: SkillTreeNode[] = [];
    for (const node of data.nodes) {
      if (node.id.startsWith("industry-")) {
        industry.push(node);
      } else {
        core.push(node);
      }
    }
    return { coreNodes: core, industryNodes: industry };
  }, [data]);

  // Get active learning path guide IDs
  const pathGuideIds = useMemo(() => {
    if (!selectedPath) return null;
    const path = LEARNING_PATHS.find((p) => p.id === selectedPath);
    return path ? new Set(path.guideIds) : null;
  }, [selectedPath]);

  const filteredNodes = useMemo((): SkillTreeNode[] => {
    let nodes = coreNodes;

    // Filter by track if tracks are selected
    if (selectedTracks.size > 0) {
      nodes = nodes.filter((n) => selectedTracks.has(n.track));
    }

    // Filter by learning path if path is selected
    if (pathGuideIds) {
      nodes = nodes.filter((n) => pathGuideIds.has(n.id));
    }

    return nodes;
  }, [coreNodes, selectedTracks, pathGuideIds]);

  const filteredEdges = useMemo((): SkillTreeEdge[] => {
    if (!data) return [];
    const nodeIds = new Set(filteredNodes.map((n) => n.id));
    return data.edges.filter((e) => nodeIds.has(e.source) && nodeIds.has(e.target));
  }, [data, filteredNodes]);

  const depthRows = useMemo(() => {
    const groups = new Map<number, SkillTreeNode[]>();
    for (const node of filteredNodes) {
      const d = node.position.depth;
      if (!groups.has(d)) groups.set(d, []);
      groups.get(d)!.push(node);
    }
    // Sort within each row by x position
    for (const row of groups.values()) {
      row.sort((a, b) => a.position.x - b.position.x);
    }
    return Array.from(groups.entries()).sort(([a], [b]) => a - b);
  }, [filteredNodes]);

  const getTrackColor = useCallback(
    (nodeId: string): string => {
      if (!data) return "#888";
      const node = data.nodes.find((n) => n.id === nodeId);
      if (!node) return "#888";
      return data.tracks[node.track]?.color ?? "#888";
    },
    [data],
  );

  const setNodeRef = useCallback((id: string, el: HTMLDivElement | null) => {
    if (el) nodeRefs.current.set(id, el);
    else nodeRefs.current.delete(id);
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!data || data.nodes.length === 0) {
    return (
      <div className="rounded-lg border border-dashed p-8 text-center">
        <p className="text-sm text-muted-foreground">No skill tree data available</p>
      </div>
    );
  }

  // Filter tracks to exclude industry track from main tree filters
  const coreTrackIds = Object.keys(data.tracks).filter((tid) => tid !== "industry");
  const coreTracks = coreTrackIds.map((tid) => data.tracks[tid] as Track);

  return (
    <div className="space-y-6">
      {/* Core Curriculum Section */}
      <div className="space-y-4">
        <div>
          <h3 className="text-sm font-semibold text-foreground">Core Curriculum</h3>
          <p className="text-xs text-muted-foreground">
            Foundational knowledge organized as prerequisite pathways
          </p>
        </div>

        {/* Learning Path Selector */}
        <div className="flex flex-wrap items-center gap-2">
          <div className="flex items-center gap-2">
            <Route className="h-3.5 w-3.5 text-muted-foreground" />
            <span className="text-xs font-medium text-muted-foreground">Learning Path:</span>
          </div>
          <select
            value={selectedPath ?? ""}
            onChange={(e) => {
              const val = e.target.value;
              setSelectedPath(val === "" ? null : val);
              if (val) setSelectedTracks(new Set()); // Clear track filters when path selected
            }}
            className="h-8 rounded-md border bg-background px-2 text-xs"
          >
            <option value="">All guides (no path)</option>
            {LEARNING_PATHS.map((path) => (
              <option key={path.id} value={path.id}>
                {path.name}
              </option>
            ))}
          </select>
          {selectedPath && (
            <Badge variant="outline" className="text-xs">
              {LEARNING_PATHS.find((p) => p.id === selectedPath)?.guideIds.length ?? 0} guides
            </Badge>
          )}
        </div>

        {selectedPath && (
          <div className="rounded-lg border bg-muted/30 p-3">
            <p className="text-xs text-muted-foreground">
              {LEARNING_PATHS.find((p) => p.id === selectedPath)?.description}
            </p>
          </div>
        )}

        {/* Track filter bar */}
        <div className="flex flex-wrap gap-1.5 px-1">
          {coreTracks.map((track) => (
            <Badge
              key={track.id}
              variant={
                selectedTracks.size === 0 || selectedTracks.has(track.id)
                  ? "default"
                  : "outline"
              }
              className="cursor-pointer text-xs"
              style={
                selectedTracks.size === 0 || selectedTracks.has(track.id)
                  ? { backgroundColor: track.color, borderColor: track.color }
                  : { color: track.color, borderColor: track.color }
              }
              onClick={() => toggleTrack(track.id)}
            >
              {track.title}
            </Badge>
          ))}
          {selectedTracks.size > 0 && (
            <Badge
              key="clear-filter"
              variant="outline"
              className="cursor-pointer text-xs"
              onClick={() => setSelectedTracks(new Set())}
            >
              Clear
            </Badge>
          )}
        </div>

        {/* Tree container */}
        <div ref={containerRef} className="relative overflow-x-auto pb-4">
          {filteredNodes.length === 0 ? (
            <div className="rounded-lg border border-dashed p-8 text-center">
              <p className="text-sm text-muted-foreground">
                No guides match the selected filters
              </p>
              <Badge
                variant="outline"
                className="cursor-pointer text-xs mt-3"
                onClick={() => setSelectedTracks(new Set())}
              >
                Clear filters
              </Badge>
            </div>
          ) : (
            <>
              <SkillTreeEdges
                edges={filteredEdges}
                nodePositions={nodePositions}
                containerRect={containerRect}
                getTrackColor={getTrackColor}
              />

              <div className="relative z-10 flex flex-col gap-8">
                {depthRows.map(([depth, nodes]) => (
                  <div key={depth} className="flex flex-wrap justify-center gap-3">
                    {nodes.map((node) => (
                      <SkillTreeNodeCard
                        key={node.id}
                        ref={(el) => setNodeRef(node.id, el)}
                        node={node}
                        trackColor={data.tracks[node.track]?.color ?? "#888"}
                      />
                    ))}
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      </div>

      {/* Industry Applications Section */}
      {industryNodes.length > 0 && (
        <div className="space-y-4">
          <div>
            <h3 className="text-sm font-semibold text-foreground">Industry Applications</h3>
            <p className="text-xs text-muted-foreground">
              Sector-specific guides for practitioners — {industryNodes.length} industries
            </p>
          </div>

          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {industryNodes.map((node) => (
              <SkillTreeNodeCard
                key={node.id}
                node={node}
                trackColor={data.tracks[node.track]?.color ?? "#888"}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
