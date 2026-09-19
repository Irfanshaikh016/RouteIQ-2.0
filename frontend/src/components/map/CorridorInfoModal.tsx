"use client";

import React from "react";
import { CorridorResponse } from "@/lib/api";

interface CorridorInfoModalProps {
  corridor: CorridorResponse | null;
  onClose: () => void;
  onSelectAsRouteEndpoints?: (startLat: number, startLon: number, endLat: number, endLon: number) => void;
}

export default function CorridorInfoModal({
  corridor,
  onClose,
  onSelectAsRouteEndpoints,
}: CorridorInfoModalProps) {
  if (!corridor) return null;

  const firstWaypoint = corridor.intermediate_waypoints[0];
  const lastWaypoint = corridor.intermediate_waypoints[corridor.intermediate_waypoints.length - 1];

  return (
    <div className="fixed inset-0 z-[1200] bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="w-full max-w-2xl rounded-2xl bg-slate-900 border border-indigo-900/50 shadow-2xl p-6 space-y-5 animate-in zoom-in-95 duration-150">
        {/* Modal Header */}
        <div className="flex items-start justify-between pb-3 border-b border-slate-800">
          <div>
            <div className="inline-flex items-center gap-2 px-2 py-0.5 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/30 mb-1.5">
              <span>🏔️</span>
              <span>{corridor.national_highway} Strategic Lifeline</span>
            </div>
            <h3 className="text-xl font-bold text-white tracking-tight">
              {corridor.name}
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              States: <span className="text-slate-200">{corridor.states_covered.join(", ")}</span> · Approx {corridor.approximate_length_km} km
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white p-1.5 rounded-lg hover:bg-slate-800 transition-colors"
          >
            ✕
          </button>
        </div>

        {/* Terrain & Strategic Notes */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
          <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-1">
            <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">
              Terrain Profile
            </span>
            <p className="text-slate-200 font-medium">{corridor.terrain_type}</p>
          </div>
          <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-1">
            <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">
              Terminal Endpoints
            </span>
            <p className="text-slate-200 font-medium">
              {corridor.start_point} → {corridor.end_point}
            </p>
          </div>
        </div>

        <div className="p-3 rounded-xl bg-amber-500/5 border border-amber-500/20 text-xs text-amber-200/90 leading-relaxed">
          <span className="font-semibold text-amber-300 block mb-0.5">Strategic Logistics Context:</span>
          {corridor.strategic_notes}
        </div>

        {/* Waypoints Table */}
        <div className="space-y-2">
          <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider block">
            Corridor Waypoints &amp; Altitudes ({corridor.intermediate_waypoints.length})
          </span>
          <div className="max-h-48 overflow-y-auto rounded-xl border border-slate-800 bg-slate-950/50 divide-y divide-slate-800/60 text-xs">
            {corridor.intermediate_waypoints.map((wp, idx) => (
              <div key={idx} className="p-2.5 flex items-center justify-between hover:bg-slate-900/50">
                <div className="flex items-center gap-2">
                  <span className="h-5 w-5 rounded-full bg-slate-800 text-[10px] font-bold text-slate-400 flex items-center justify-center">
                    {idx + 1}
                  </span>
                  <div>
                    <span className="font-medium text-white">{wp.name}</span>
                    <span className="text-[10px] text-slate-400 ml-1.5">({wp.state})</span>
                  </div>
                </div>
                <div className="text-right">
                  <span className="text-indigo-400 font-mono text-[11px] block">
                    {wp.latitude.toFixed(4)}°N, {wp.longitude.toFixed(4)}°E
                  </span>
                  {wp.elevation_m !== null && wp.elevation_m !== undefined && (
                    <span className="text-[10px] text-emerald-400">
                      ⛰️ {wp.elevation_m}m ASL
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Modal Footer */}
        <div className="flex items-center justify-between pt-3 border-t border-slate-800">
          {onSelectAsRouteEndpoints && firstWaypoint && lastWaypoint ? (
            <button
              onClick={() => {
                onSelectAsRouteEndpoints(
                  firstWaypoint.latitude,
                  firstWaypoint.longitude,
                  lastWaypoint.latitude,
                  lastWaypoint.longitude
                );
                onClose();
              }}
              className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-xs font-medium text-white shadow-lg shadow-indigo-500/20 transition-all flex items-center gap-1.5"
            >
              <span>⚡</span>
              <span>Set as Origin &amp; Destination</span>
            </button>
          ) : <div />}
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-300 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
