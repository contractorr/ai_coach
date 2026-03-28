"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { toast } from "sonner";
import { Loader2, Route } from "lucide-react";
import { useToken } from "@/hooks/useToken";
import { apiFetch } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import type {
  LearningProgram,
  SkillTreeEdge,
  SkillTreeNode,
  SkillTreeResponse,
  Track,
} from "@/types/curriculum";
import { SkillTreeNodeCard } from "./SkillTreeNode";
import { SkillTreeEdges } from "./SkillTreeEdges";

export function SkillTree() {
  const token = useToken();
  const [data, setData] = useState<SkillTreeResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedTracks, setSelectedTracks] = useState<Set<string>>(new Set());
  const [selectedProgramId, setSelectedProgramId] = useState<string | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const nodeRefs = useRef<Map<string, HTMLDivElement>>(new Map());
  const [nodePositions, setNodePositions] = useState<Map<string, DOMRect>>(new Map());
  const [containerRect, setContainerRect] = useState<DOMRect | null>(null);
  const [measureTick, setMeasureTick] = useState(0);

  useEffect(() => {
    if (!token) return;
    setLoading(true);
    apiFetch<SkillTreeResponse>("/api/v1/curriculum/tree", {}, token)
      .then(setData)
      .catch((e) => toast.error((e as Error).message))
      .finally(() => setLoading(false));
  }, [token]);

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

  const { coreNodes, industryNodes } = useMemo(() => {
    if (!data) return { coreNodes: [], industryNodes: [] };
    const core: SkillTreeNode[] = [];
    const industry: SkillTreeNode[] = [];
    for (const node of data.nodes) {
      if (node.id.startsWith("industry-")) industry.push(node);
      else core.push(node);
    }
    return { coreNodes: core, industryNodes: industry };
  }, [data]);

  const programs = useMemo(() => data?.programs ?? [], [data]);

  const selectedProgram = useMemo<LearningProgram | null>(() => {
    if (!selectedProgramId) return null;
    return programs.find((program) => program.id === selectedProgramId) ?? null;
  }, [programs, selectedProgramId]);

  const selectedProgramGuideIds = useMemo(() => {
    if (!selectedProgram) return null;
    return new Set(selectedProgram.guide_ids);
  }, [selectedProgram]);

  const filteredNodes = useMemo((): SkillTreeNode[] => {
    let nodes = coreNodes;

    if (selectedTracks.size > 0) {
      nodes = nodes.filter((node) => selectedTracks.has(node.track));
    }

    if (selectedProgramGuideIds) {
      nodes = nodes.filter((node) => selectedProgramGuideIds.has(node.id));
    }

    return nodes;
  }, [coreNodes, selectedProgramGuideIds, selectedTracks]);

  const filteredEdges = useMemo((): SkillTreeEdge[] => {
    if (!data) return [];
    const nodeIds = new Set(filteredNodes.map((node) => node.id));
    return data.edges.filter((edge) => nodeIds.has(edge.source) && nodeIds.has(edge.target));
  }, [data, filteredNodes]);

  const filteredIndustryNodes = useMemo(() => {
    if (!selectedProgramGuideIds) return industryNodes;
    return industryNodes.filter((node) => selectedProgramGuideIds.has(node.id));
  }, [industryNodes, selectedProgramGuideIds]);

  const depthRows = useMemo(() => {
    const groups = new Map<number, SkillTreeNode[]>();
    for (const node of filteredNodes) {
      const depth = node.position.depth;
      if (!groups.has(depth)) groups.set(depth, []);
      groups.get(depth)!.push(node);
    }
    for (const row of groups.values()) {
      row.sort((a, b) => a.position.x - b.position.x);
    }
    return Array.from(groups.entries()).sort(([a], [b]) => a - b);
  }, [filteredNodes]);

  const getTrackColor = useCallback(
    (nodeId: string): string => {
      if (!data) return "#888";
      const node = data.nodes.find((entry) => entry.id === nodeId);
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

  const coreTrackIds = Object.keys(data.tracks).filter((trackId) => trackId !== "industry");
  const coreTracks = coreTrackIds.map((trackId) => data.tracks[trackId] as Track);

  return (
    <div className="space-y-6">
      <div className="space-y-4">
        <div>
          <h3 className="text-sm font-semibold text-foreground">Core Curriculum</h3>
          <p className="text-xs text-muted-foreground">
            Foundational knowledge organized as prerequisite pathways
          </p>
        </div>

        {programs.length > 0 && (
          <>
            <div className="flex flex-wrap items-center gap-2">
              <div className="flex items-center gap-2">
                <Route className="h-3.5 w-3.5 text-muted-foreground" />
                <span className="text-xs font-medium text-muted-foreground">Learning Path:</span>
              </div>
              <select
                value={selectedProgramId ?? ""}
                onChange={(e) => {
                  const nextProgramId = e.target.value;
                  setSelectedProgramId(nextProgramId === "" ? null : nextProgramId);
                  if (nextProgramId) setSelectedTracks(new Set());
                }}
                className="h-8 rounded-md border bg-background px-2 text-xs"
              >
                <option value="">All guides</option>
                {programs.map((program) => (
                  <option key={program.id} value={program.id}>
                    {program.title}
                  </option>
                ))}
              </select>
              {selectedProgram && (
                <Badge variant="outline" className="text-xs">
                  {selectedProgram.guide_ids.length} guides
                </Badge>
              )}
            </div>

            {selectedProgram && (
              <div className="rounded-lg border bg-muted/30 p-3">
                <p className="text-xs text-muted-foreground">{selectedProgram.description}</p>
              </div>
            )}
          </>
        )}

        <div className="flex flex-wrap gap-1.5 px-1">
          {coreTracks.map((track) => (
            <Badge
              key={track.id}
              variant={
                selectedTracks.size === 0 || selectedTracks.has(track.id) ? "default" : "outline"
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

        <div ref={containerRef} className="relative overflow-x-auto pb-4 pt-8">
          {filteredNodes.length === 0 ? (
            <div className="rounded-lg border border-dashed p-8 text-center">
              <p className="text-sm text-muted-foreground">No guides match the selected filters</p>
              <Badge
                variant="outline"
                className="mt-3 cursor-pointer text-xs"
                onClick={() => {
                  setSelectedProgramId(null);
                  setSelectedTracks(new Set());
                }}
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

      {filteredIndustryNodes.length > 0 && (
        <div className="space-y-4">
          <div>
            <h3 className="text-sm font-semibold text-foreground">Industry Applications</h3>
            <p className="text-xs text-muted-foreground">
              Sector-specific guides for practitioners - {filteredIndustryNodes.length} industries
            </p>
          </div>

          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {filteredIndustryNodes.map((node) => (
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
