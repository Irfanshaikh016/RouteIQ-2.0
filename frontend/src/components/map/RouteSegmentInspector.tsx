"use client";

import React, { useState } from "react";
import { RouteEdgeItem } from "@/lib/api";

interface RouteSegmentInspectorProps {
  edges: RouteEdgeItem[];
  selectedEdgeIndex: number | null;
  onSelectEdge: (index: number | null) => void;
}

export default function RouteSegmentInspector({
  edges,
  selectedEdgeIndex,
  onSelectEdge,
}: RouteSegmentInspectorProps) {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(selectedEdgeIndex);

  if (!edges || edges.length === 0) {
    return (
      <div className="p-4 rounded-xl border border-slate-800 bg-slate-950/40 text-center text-xs text-slate-400">
        No active route segments to inspect. Plan a route to see explainable edge costs.
      </div>
    );
  }

  const toggleExpand = (idx: number) => {
    const next = expandedIndex === idx ? null : idx;
    setExpandedIndex(next);
    onSelectEdge(next);
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between pb-1">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-300">
          Segment Explainability ({edges.length} segments)
        </span>
        <span className="text-[10px] text-slate-400">Click to inspect</span>
      </div>

      <div className="max-h-72 overflow-y-auto space-y-1.5 pr-1 text-xs">
        {edges.map((edge, idx) => {
          const isExpanded = expandedIndex === idx;
          const roadName = edge.road_name || `Segment ${edge.sequence}`;

          return (
            <div
              key={edge.edge_id || idx}
              className={`rounded-xl border transition-all ${
                isExpanded
                  ? "border-indigo-500/50 bg-slate-900/90 shadow-lg"
                  : "border-slate-800 bg-slate-950/50 hover:border-slate-700 hover:bg-slate-900/40"
              }`}
            >
              <button
                onClick={() => toggleExpand(idx)}
                className="w-full p-2.5 flex items-center justify-between text-left"
              >
                <div className="flex items-center gap-2">
                  <span className="h-5 w-5 rounded-full bg-slate-800 text-[10px] font-bold text-slate-300 flex items-center justify-center shrink-0">
                    {edge.sequence}
                  </span>
                  <div>
                    <span className="font-medium text-white block truncate max-w-[180px]">
                      {roadName}
                    </span>
                    <span className="text-[10px] text-slate-400 uppercase font-mono">
                      {edge.road_type} · {(edge.length_meters / 1000).toFixed(2)} km
                    </span>
                  </div>
                </div>

                <div className="text-right">
                  <span className="text-[11px] font-semibold text-cyan-400 block">
                    {(edge.estimated_time_seconds / 60).toFixed(1)}m
                  </span>
                  <span className="text-[9px] text-slate-400">
                    Cost: {edge.cost_breakdown.total_cost.toFixed(2)}
                  </span>
                </div>
              </button>

              {/* Detailed Cost and Risk Breakdown */}
              {isExpanded && (
                <div className="p-3 pt-0 border-t border-slate-800/80 space-y-3 mt-1 text-[11px]">
                  {/* Multi-Criteria Cost Breakdown */}
                  <div>
                    <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 block mb-1">
                      Weighted Cost Breakdown
                    </span>
                    <div className="grid grid-cols-2 gap-1.5 bg-slate-950/70 p-2 rounded-lg border border-slate-800/60">
                      <div className="flex justify-between">
                        <span className="text-slate-400">Distance Cost:</span>
                        <span className="font-mono text-slate-200">{edge.cost_breakdown.distance_cost.toFixed(3)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Time Cost:</span>
                        <span className="font-mono text-slate-200">{edge.cost_breakdown.time_cost.toFixed(3)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Risk Penalty:</span>
                        <span className="font-mono text-amber-300">{edge.cost_breakdown.risk_cost.toFixed(3)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Terrain Penalty:</span>
                        <span className="font-mono text-emerald-300">{edge.cost_breakdown.terrain_cost.toFixed(3)}</span>
                      </div>
                    </div>
                  </div>

                  {/* Modeled Hazard Risk Scores */}
                  <div>
                    <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 block mb-1">
                      Modeled Environmental Risk Scores [0 – 1]
                    </span>
                    <div className="space-y-1 bg-slate-950/70 p-2 rounded-lg border border-slate-800/60">
                      <div className="flex items-center justify-between">
                        <span className="text-slate-400">Landslide Risk:</span>
                        <div className="flex items-center gap-2">
                          <div className="w-16 h-1.5 rounded-full bg-slate-800 overflow-hidden">
                            <div
                              className="h-full bg-rose-500 rounded-full"
                              style={{ width: `${edge.risk_breakdown.landslide_risk * 100}%` }}
                            />
                          </div>
                          <span className="font-mono text-[10px] text-slate-200">
                            {edge.risk_breakdown.landslide_risk.toFixed(2)}
                          </span>
                        </div>
                      </div>

                      <div className="flex items-center justify-between">
                        <span className="text-slate-400">Flood Vulnerability:</span>
                        <div className="flex items-center gap-2">
                          <div className="w-16 h-1.5 rounded-full bg-slate-800 overflow-hidden">
                            <div
                              className="h-full bg-blue-500 rounded-full"
                              style={{ width: `${edge.risk_breakdown.flood_risk * 100}%` }}
                            />
                          </div>
                          <span className="font-mono text-[10px] text-slate-200">
                            {edge.risk_breakdown.flood_risk.toFixed(2)}
                          </span>
                        </div>
                      </div>

                      <div className="flex items-center justify-between">
                        <span className="text-slate-400">Terrain Difficulty:</span>
                        <div className="flex items-center gap-2">
                          <div className="w-16 h-1.5 rounded-full bg-slate-800 overflow-hidden">
                            <div
                              className="h-full bg-amber-500 rounded-full"
                              style={{ width: `${edge.risk_breakdown.terrain_risk * 100}%` }}
                            />
                          </div>
                          <span className="font-mono text-[10px] text-slate-200">
                            {edge.risk_breakdown.terrain_risk.toFixed(2)}
                          </span>
                        </div>
                      </div>

                      <div className="flex items-center justify-between">
                        <span className="text-slate-400">Surface Degradation:</span>
                        <div className="flex items-center gap-2">
                          <div className="w-16 h-1.5 rounded-full bg-slate-800 overflow-hidden">
                            <div
                              className="h-full bg-purple-500 rounded-full"
                              style={{ width: `${edge.risk_breakdown.surface_risk * 100}%` }}
                            />
                          </div>
                          <span className="font-mono text-[10px] text-slate-200">
                            {edge.risk_breakdown.surface_risk.toFixed(2)}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
