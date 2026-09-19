"use client";

import React, { useState } from "react";
import {
  OptimizationResult,
  OptimizationRouteItem,
  OptimizationStopItem,
  UnservedDeliveryItem,
} from "@/lib/api";

interface OptimizationResultCardProps {
  result: OptimizationResult;
  onSelectRoute?: (route: OptimizationRouteItem) => void;
  selectedRouteVehicleId?: string | null;
}

const VEHICLE_PALETTE = ["#06b6d4", "#a855f7", "#10b981", "#f59e0b", "#ec4899", "#3b82f6"];

export default function OptimizationResultCard({
  result,
  onSelectRoute,
  selectedRouteVehicleId,
}: OptimizationResultCardProps) {
  const [expandedRouteId, setExpandedRouteId] = useState<string | null>(
    result.routes.length > 0 ? result.routes[0].vehicle_id : null
  );

  return (
    <div className="space-y-4">
      {/* Overview Metrics Banner */}
      <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/90 shadow-lg space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-xs font-bold uppercase tracking-wider text-slate-200">
              OR-Tools {result.problem_type} Solution
            </span>
          </div>
          <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-800 text-cyan-400 border border-slate-700">
            {result.profile.toUpperCase()} PROFILE
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1">
          <div className="p-2.5 rounded-lg bg-slate-950/70 border border-slate-800/80">
            <div className="text-[10px] uppercase tracking-wider text-slate-400">Fleet Used</div>
            <div className="text-base font-bold text-white mt-0.5">
              {result.vehicles_used}{" "}
              <span className="text-xs font-normal text-slate-400">veh</span>
            </div>
          </div>

          <div className="p-2.5 rounded-lg bg-slate-950/70 border border-slate-800/80">
            <div className="text-[10px] uppercase tracking-wider text-slate-400">Deliveries Served</div>
            <div className="text-base font-bold text-emerald-400 mt-0.5">
              {result.served_deliveries_count} / {result.total_deliveries}
            </div>
          </div>

          <div className="p-2.5 rounded-lg bg-slate-950/70 border border-slate-800/80">
            <div className="text-[10px] uppercase tracking-wider text-slate-400">Total Distance</div>
            <div className="text-base font-bold text-cyan-400 mt-0.5">
              {result.total_distance_km.toFixed(1)}{" "}
              <span className="text-xs font-normal text-slate-400">km</span>
            </div>
          </div>

          <div className="p-2.5 rounded-lg bg-slate-950/70 border border-slate-800/80">
            <div className="text-[10px] uppercase tracking-wider text-slate-400">Total Duration</div>
            <div className="text-base font-bold text-amber-400 mt-0.5">
              {Math.floor(result.total_duration_minutes / 60)}h{" "}
              {Math.round(result.total_duration_minutes % 60)}m
            </div>
          </div>
        </div>
      </div>

      {/* Unserved Deliveries Diagnostic Warning */}
      {result.unserved_deliveries && result.unserved_deliveries.length > 0 && (
        <div className="p-3.5 rounded-xl border border-rose-900/60 bg-rose-950/30 text-xs text-rose-300 space-y-1.5">
          <div className="font-semibold flex items-center gap-1.5 text-rose-200">
            <span>⚠️</span>
            <span>{result.unserved_deliveries.length} Unserved Deliveries Diagnostic</span>
          </div>
          <div className="space-y-1 max-h-32 overflow-y-auto pr-1">
            {result.unserved_deliveries.map((u, i) => (
              <div key={i} className="flex items-center justify-between text-[11px] p-1.5 rounded bg-rose-950/50 border border-rose-800/40">
                <span className="font-mono text-rose-200">{u.delivery_id}</span>
                <span className="text-rose-400">{u.reason}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Vehicle Routes Accordion */}
      <div className="space-y-2.5">
        <div className="text-xs font-semibold uppercase tracking-wider text-slate-400 px-1">
          Vehicle Dispatch Schedules ({result.routes.length})
        </div>

        {result.routes.map((route, idx) => {
          const color = VEHICLE_PALETTE[idx % VEHICLE_PALETTE.length];
          const isExpanded = expandedRouteId === route.vehicle_id;
          const isSelected = selectedRouteVehicleId === route.vehicle_id;

          return (
            <div
              key={route.vehicle_id}
              className={`rounded-xl border transition-all overflow-hidden ${
                isSelected
                  ? "border-cyan-500/80 bg-slate-900/90 shadow-md shadow-cyan-500/10"
                  : "border-slate-800 bg-slate-900/50 hover:border-slate-700"
              }`}
            >
              {/* Route Header */}
              <button
                onClick={() => {
                  setExpandedRouteId(isExpanded ? null : route.vehicle_id);
                  onSelectRoute?.(route);
                }}
                className="w-full p-3.5 text-left flex items-center justify-between gap-2"
              >
                <div className="flex items-center gap-2.5">
                  <span
                    className="h-3.5 w-3.5 rounded-full flex-shrink-0 border-2 border-slate-900"
                    style={{ backgroundColor: color }}
                  />
                  <div>
                    <div className="text-xs font-bold text-white flex items-center gap-2">
                      <span>{route.vehicle_name}</span>
                      <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-slate-800 text-slate-300">
                        {route.stops.length - 2} stops
                      </span>
                    </div>
                    <div className="text-[11px] text-slate-400 mt-0.5">
                      {route.total_distance_km.toFixed(1)} km • {Math.round(route.total_duration_minutes)} mins
                    </div>
                  </div>
                </div>

                <div className="text-right">
                  <div className="text-xs font-semibold text-slate-200">
                    {route.capacity_utilization_pct}% payload
                  </div>
                  <div className="text-[10px] text-slate-400">
                    {route.peak_load} / {route.capacity} kg
                  </div>
                </div>
              </button>

              {/* Payload Utilization Bar */}
              <div className="px-3.5 pb-2">
                <div className="w-full h-1.5 rounded-full bg-slate-800 overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all"
                    style={{
                      width: `${Math.min(route.capacity_utilization_pct, 100)}%`,
                      backgroundColor: color,
                    }}
                  />
                </div>
              </div>

              {/* Stop by Stop Detailed Timeline */}
              {isExpanded && (
                <div className="border-t border-slate-800/80 bg-slate-950/60 p-3 space-y-2">
                  <div className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
                    Sequential Stops
                  </div>

                  <div className="space-y-1.5">
                    {route.stops.map((stop) => (
                      <div
                        key={stop.sequence}
                        className="flex items-center justify-between text-xs p-2 rounded-lg bg-slate-900/60 border border-slate-800/60"
                      >
                        <div className="flex items-center gap-2">
                          <span
                            className="h-5 w-5 rounded-full flex items-center justify-center text-[10px] font-bold text-slate-900"
                            style={{ backgroundColor: color }}
                          >
                            {stop.is_depot ? (stop.sequence === 1 ? "D" : "R") : stop.sequence - 1}
                          </span>
                          <div>
                            <div className="font-medium text-slate-200 text-[11px]">
                              {stop.location_name}
                            </div>
                            <div className="text-[10px] text-slate-400">
                              Arr: {stop.arrival_time_minutes}m • Dep: {stop.departure_time_minutes}m
                              {stop.waiting_time_minutes ? ` (wait: ${stop.waiting_time_minutes}m)` : ""}
                            </div>
                          </div>
                        </div>

                        <div className="text-right text-[10px] text-slate-400 font-mono">
                          {stop.is_depot ? "Depot" : `Load: ${stop.load_after_stop} kg`}
                        </div>
                      </div>
                    ))}
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
