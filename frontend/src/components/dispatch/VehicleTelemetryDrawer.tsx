"use client";

import React from "react";
import { VehicleStateItem, OptimizationRouteItem } from "@/lib/api";

interface VehicleTelemetryDrawerProps {
  vehicle: VehicleStateItem | null;
  activeRoute?: OptimizationRouteItem | null;
  onClose: () => void;
}

export default function VehicleTelemetryDrawer({
  vehicle,
  activeRoute,
  onClose,
}: VehicleTelemetryDrawerProps) {
  if (!vehicle) return null;

  const tel = vehicle.latest_telemetry;
  const freshness = vehicle.freshness;

  const getFreshnessBadge = () => {
    switch (freshness) {
      case "LIVE":
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-950/80 text-emerald-400 border border-emerald-500/40 shadow-sm shadow-emerald-500/20">
            <span className="h-2 w-2 rounded-full bg-emerald-400 animate-ping" />
            LIVE (&lt; 5m)
          </span>
        );
      case "STALE":
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-950/80 text-amber-400 border border-amber-500/40">
            <span className="h-2 w-2 rounded-full bg-amber-400" />
            STALE (5-60m)
          </span>
        );
      case "OFFLINE":
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-800 text-slate-400 border border-slate-700">
            <span className="h-2 w-2 rounded-full bg-slate-500" />
            OFFLINE (&gt; 60m)
          </span>
        );
    }
  };

  return (
    <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/95 backdrop-blur-md shadow-2xl space-y-4">
      {/* Header with Title and Close Button */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-800">
        <div className="flex items-center gap-2.5">
          <div className="h-9 w-9 rounded-lg bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-lg">
            🚚
          </div>
          <div>
            <div className="text-sm font-bold text-white flex items-center gap-2">
              <span>{vehicle.vehicle_name}</span>
              <span className="text-xs font-mono text-slate-400">
                {vehicle.registration_number}
              </span>
            </div>
            <div className="text-[11px] text-slate-400 capitalize">
              {vehicle.vehicle_type} • Capacity: {vehicle.capacity} kg
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {getFreshnessBadge()}
          <button
            onClick={onClose}
            className="h-7 w-7 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white flex items-center justify-center transition-colors"
          >
            ✕
          </button>
        </div>
      </div>

      {/* Telemetry Metrics Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
        <div className="p-2.5 rounded-lg bg-slate-950/70 border border-slate-800/80">
          <div className="text-[10px] uppercase tracking-wider text-slate-400">Current Speed</div>
          <div className="text-base font-bold text-cyan-400 mt-0.5">
            {tel?.speed !== undefined ? tel.speed.toFixed(1) : "--"}{" "}
            <span className="text-xs font-normal text-slate-400">km/h</span>
          </div>
        </div>

        <div className="p-2.5 rounded-lg bg-slate-950/70 border border-slate-800/80">
          <div className="text-[10px] uppercase tracking-wider text-slate-400">Battery Level</div>
          <div className="text-base font-bold text-emerald-400 mt-0.5">
            {tel?.battery_level !== undefined ? `${tel.battery_level}%` : "--"}
          </div>
        </div>

        <div className="p-2.5 rounded-lg bg-slate-950/70 border border-slate-800/80">
          <div className="text-[10px] uppercase tracking-wider text-slate-400">Heading / Compass</div>
          <div className="text-base font-bold text-amber-400 mt-0.5">
            {tel?.heading !== undefined ? `${tel.heading.toFixed(0)}°` : "--"}
          </div>
        </div>

        <div className="p-2.5 rounded-lg bg-slate-950/70 border border-slate-800/80">
          <div className="text-[10px] uppercase tracking-wider text-slate-400">Ignition</div>
          <div className="text-base font-bold text-white mt-0.5 flex items-center gap-1.5">
            <span
              className={`h-2 w-2 rounded-full ${
                tel?.ignition_status ? "bg-emerald-400" : "bg-slate-500"
              }`}
            />
            <span className="text-xs">
              {tel?.ignition_status !== undefined
                ? tel.ignition_status
                  ? "RUNNING"
                  : "STOPPED"
                : "--"}
            </span>
          </div>
        </div>
      </div>

      {/* Geolocation & Source Details */}
      {tel && (
        <div className="p-2.5 rounded-lg bg-slate-950/50 border border-slate-800/60 flex items-center justify-between text-xs">
          <div className="text-slate-300">
            <span className="text-slate-500 mr-1">GPS:</span>
            {tel.latitude.toFixed(4)}, {tel.longitude.toFixed(4)}
          </div>
          <div className="text-[11px] font-mono text-slate-400">
            Source: <span className="text-indigo-400">{tel.source}</span>
          </div>
        </div>
      )}

      {/* Active Route Context if vehicle has assigned route */}
      {activeRoute && (
        <div className="p-3 rounded-lg bg-indigo-950/20 border border-indigo-500/30 text-xs space-y-2">
          <div className="flex items-center justify-between">
            <span className="font-semibold text-indigo-300">
              Assigned Route: {activeRoute.stops.length - 2} deliveries
            </span>
            <span className="text-indigo-400 font-mono text-[11px]">
              {activeRoute.total_distance_km.toFixed(1)} km
            </span>
          </div>

          <div className="flex items-center gap-1 overflow-x-auto py-1">
            {activeRoute.stops.map((s, idx) => (
              <div
                key={s.sequence}
                className="flex-shrink-0 px-2 py-1 rounded bg-slate-900 border border-slate-800 text-[10px] text-slate-300 flex items-center gap-1"
              >
                <span className="font-bold text-cyan-400">#{s.sequence}</span>
                <span className="truncate max-w-[80px]">{s.location_name}</span>
                {idx < activeRoute.stops.length - 1 && (
                  <span className="text-slate-600">→</span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
