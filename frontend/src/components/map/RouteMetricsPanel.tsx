"use client";

import React from "react";
import { RouteResponse } from "@/lib/api";

interface RouteMetricsPanelProps {
  activeRoute: RouteResponse | null;
  comparisonRoutes: RouteResponse[] | null;
  onSelectComparedRoute?: (route: RouteResponse) => void;
}

export default function RouteMetricsPanel({
  activeRoute,
  comparisonRoutes,
  onSelectComparedRoute,
}: RouteMetricsPanelProps) {
  if (!activeRoute && (!comparisonRoutes || comparisonRoutes.length === 0)) {
    return null;
  }

  const profileColors: Record<string, { badge: string; text: string; border: string }> = {
    fastest: { badge: "bg-cyan-500/10 text-cyan-400 border-cyan-500/30", text: "text-cyan-400", border: "border-cyan-500/40" },
    safest: { badge: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30", text: "text-emerald-400", border: "border-emerald-500/40" },
    balanced: { badge: "bg-amber-500/10 text-amber-400 border-amber-500/30", text: "text-amber-400", border: "border-amber-500/40" },
  };

  return (
    <div className="space-y-4">
      {/* Active Route Primary Metrics */}
      {activeRoute && (
        <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/80 shadow-md space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-400 font-medium">Selected Profile:</span>
              <span
                className={`px-2 py-0.5 rounded-full text-xs font-bold uppercase tracking-wide border ${
                  profileColors[activeRoute.profile.toLowerCase()]?.badge || "bg-indigo-500/10 text-indigo-400 border-indigo-500/30"
                }`}
              >
                {activeRoute.profile}
              </span>
            </div>
            <span className="text-[10px] text-slate-500 font-mono">
              ID: {activeRoute.route_id.slice(0, 8)}...
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
            <div className="p-2.5 rounded-lg bg-slate-950/70 border border-slate-800/80">
              <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">
                Total Distance
              </span>
              <span className="text-lg font-bold text-white tracking-tight">
                {activeRoute.metrics.distance_km} <span className="text-xs font-normal text-slate-400">km</span>
              </span>
            </div>

            <div className="p-2.5 rounded-lg bg-slate-950/70 border border-slate-800/80">
              <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">
                Estimated Duration
              </span>
              <span className="text-lg font-bold text-white tracking-tight">
                {Math.round(activeRoute.metrics.estimated_time_minutes)}{" "}
                <span className="text-xs font-normal text-slate-400">min</span>
              </span>
            </div>

            <div className="p-2.5 rounded-lg bg-slate-950/70 border border-slate-800/80">
              <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">
                Modeled Risk
              </span>
              <span className="text-lg font-bold text-amber-400 tracking-tight">
                {activeRoute.metrics.risk_score.toFixed(2)}{" "}
                <span className="text-[10px] font-normal text-slate-400">/ 1.0</span>
              </span>
            </div>

            <div className="p-2.5 rounded-lg bg-slate-950/70 border border-slate-800/80">
              <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">
                Terrain Grade
              </span>
              <span className="text-lg font-bold text-emerald-400 tracking-tight">
                {activeRoute.metrics.terrain_score.toFixed(2)}{" "}
                <span className="text-[10px] font-normal text-slate-400">/ 1.0</span>
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Multi-Profile Comparison Table */}
      {comparisonRoutes && comparisonRoutes.length > 0 && (
        <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/80 shadow-md space-y-2.5">
          <div className="flex items-center justify-between pb-1 border-b border-slate-800">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-300">
              Neutral Profile Comparison ({comparisonRoutes.length} Profiles)
            </span>
            <span className="text-[10px] text-slate-400">Select to display on map</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead>
                <tr className="text-[10px] uppercase font-semibold text-slate-400 border-b border-slate-800">
                  <th className="py-2 px-2">Profile</th>
                  <th className="py-2 px-2">Distance</th>
                  <th className="py-2 px-2">Est. Time</th>
                  <th className="py-2 px-2">Modeled Risk</th>
                  <th className="py-2 px-2">Terrain Score</th>
                  <th className="py-2 px-2 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-medium">
                {comparisonRoutes.map((route) => {
                  const isSelected = activeRoute?.route_id === route.route_id || activeRoute?.profile === route.profile;
                  const colors = profileColors[route.profile.toLowerCase()];

                  return (
                    <tr
                      key={route.profile}
                      className={`transition-colors ${
                        isSelected ? "bg-indigo-950/40 text-white" : "hover:bg-slate-800/40 text-slate-300"
                      }`}
                    >
                      <td className="py-2.5 px-2 flex items-center gap-1.5">
                        <span
                          className={`h-2 w-2 rounded-full ${
                            route.profile === "fastest"
                              ? "bg-cyan-400"
                              : route.profile === "safest"
                              ? "bg-emerald-400"
                              : "bg-amber-400"
                          }`}
                        />
                        <span className={`font-bold capitalize ${colors?.text || "text-white"}`}>
                          {route.profile}
                        </span>
                      </td>
                      <td className="py-2.5 px-2">{route.metrics.distance_km} km</td>
                      <td className="py-2.5 px-2">{Math.round(route.metrics.estimated_time_minutes)} min</td>
                      <td className="py-2.5 px-2 font-mono text-amber-300">
                        {route.metrics.risk_score.toFixed(2)}
                      </td>
                      <td className="py-2.5 px-2 font-mono text-emerald-300">
                        {route.metrics.terrain_score.toFixed(2)}
                      </td>
                      <td className="py-2.5 px-2 text-right">
                        <button
                          onClick={() => onSelectComparedRoute && onSelectComparedRoute(route)}
                          className={`px-2.5 py-1 rounded-md text-[10px] font-semibold transition-all ${
                            isSelected
                              ? "bg-indigo-600 text-white"
                              : "bg-slate-800 hover:bg-slate-700 text-slate-300"
                          }`}
                        >
                          {isSelected ? "Active" : "Inspect"}
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
