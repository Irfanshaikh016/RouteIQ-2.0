"use client";

import React, { useState } from "react";
import { RouteRequest } from "@/lib/api";

interface RoutePlannerSidebarProps {
  onCalculateRoute: (request: RouteRequest) => Promise<void>;
  onCompareRoutes: (request: RouteRequest) => Promise<void>;
  loading: boolean;
  error: string | null;
  selectedProfile: string;
  onProfileChange: (profile: string) => void;
  originLat: string;
  setOriginLat: (val: string) => void;
  originLon: string;
  setOriginLon: (val: string) => void;
  destLat: string;
  setDestLat: (val: string) => void;
  destLon: string;
  setDestLon: (val: string) => void;
}

const REGIONAL_HUB_PRESETS: { name: string; state: string; lat: number; lon: number }[] = [
  { name: "Guwahati (Khanapara)", state: "Assam", lat: 26.1158, lon: 91.8210 },
  { name: "Shillong (Barik)", state: "Meghalaya", lat: 25.5788, lon: 91.8933 },
  { name: "Silchar (Central)", state: "Assam", lat: 24.8333, lon: 92.7789 },
  { name: "Dimapur (Railhead)", state: "Nagaland", lat: 25.9068, lon: 93.7274 },
  { name: "Kohima (Capital)", state: "Nagaland", lat: 25.6751, lon: 94.1086 },
  { name: "Imphal (Valley Hub)", state: "Manipur", lat: 24.8170, lon: 93.9368 },
  { name: "Agartala (Central)", state: "Tripura", lat: 23.8315, lon: 91.2868 },
  { name: "Aizawl (Ridge Terminal)", state: "Mizoram", lat: 23.7271, lon: 92.7176 },
  { name: "Itanagar (Naharlagun)", state: "Arunachal Pradesh", lat: 27.0844, lon: 93.6053 },
  { name: "Gangtok (Sikkim)", state: "Sikkim", lat: 27.3389, lon: 88.6065 },
];

export default function RoutePlannerSidebar({
  onCalculateRoute,
  onCompareRoutes,
  loading,
  error,
  selectedProfile,
  onProfileChange,
  originLat,
  setOriginLat,
  originLon,
  setOriginLon,
  destLat,
  setDestLat,
  destLon,
  setDestLon,
}: RoutePlannerSidebarProps) {
  const [activeTab, setActiveTab] = useState<"plan" | "presets">("plan");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const lat1 = parseFloat(originLat);
    const lon1 = parseFloat(originLon);
    const lat2 = parseFloat(destLat);
    const lon2 = parseFloat(destLon);

    if (isNaN(lat1) || isNaN(lon1) || isNaN(lat2) || isNaN(lon2)) {
      return;
    }

    onCalculateRoute({
      origin: { latitude: lat1, longitude: lon1 },
      destination: { latitude: lat2, longitude: lon2 },
      profile: selectedProfile,
    });
  };

  const handleCompare = () => {
    const lat1 = parseFloat(originLat);
    const lon1 = parseFloat(originLon);
    const lat2 = parseFloat(destLat);
    const lon2 = parseFloat(destLon);

    if (isNaN(lat1) || isNaN(lon1) || isNaN(lat2) || isNaN(lon2)) {
      return;
    }

    onCompareRoutes({
      origin: { latitude: lat1, longitude: lon1 },
      destination: { latitude: lat2, longitude: lon2 },
    });
  };

  const setPresetAsOrigin = (hub: (typeof REGIONAL_HUB_PRESETS)[0]) => {
    setOriginLat(hub.lat.toString());
    setOriginLon(hub.lon.toString());
  };

  const setPresetAsDest = (hub: (typeof REGIONAL_HUB_PRESETS)[0]) => {
    setDestLat(hub.lat.toString());
    setDestLon(hub.lon.toString());
  };

  return (
    <div className="p-4 rounded-2xl border border-slate-800 bg-slate-900/90 shadow-xl space-y-4 text-xs">
      <div className="flex items-center justify-between pb-2 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <span className="text-base">🧭</span>
          <h2 className="text-sm font-bold text-white tracking-tight">Route Dispatch Planner</h2>
        </div>
        <div className="flex items-center p-0.5 rounded-lg bg-slate-950 border border-slate-800">
          <button
            onClick={() => setActiveTab("plan")}
            className={`px-2 py-0.5 rounded-md text-[10px] font-semibold transition-all ${
              activeTab === "plan" ? "bg-indigo-600 text-white" : "text-slate-400 hover:text-white"
            }`}
          >
            Coordinates
          </button>
          <button
            onClick={() => setActiveTab("presets")}
            className={`px-2 py-0.5 rounded-md text-[10px] font-semibold transition-all ${
              activeTab === "presets" ? "bg-indigo-600 text-white" : "text-slate-400 hover:text-white"
            }`}
          >
            Hub Presets
          </button>
        </div>
      </div>

      {error && (
        <div className="p-2.5 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-[11px] leading-relaxed">
          ⚠️ {error}
        </div>
      )}

      {activeTab === "plan" ? (
        <form onSubmit={handleSubmit} className="space-y-3.5">
          {/* Origin Coordinates */}
          <div className="space-y-1">
            <span className="text-[10px] font-semibold uppercase tracking-wider text-cyan-400 flex items-center gap-1">
              <span>🟢</span> Origin (Pickup Dispatch)
            </span>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="text-[9px] text-slate-400 block mb-0.5">Latitude</label>
                <input
                  type="number"
                  step="any"
                  placeholder="26.1158"
                  value={originLat}
                  onChange={(e) => setOriginLat(e.target.value)}
                  required
                  className="w-full px-2.5 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-cyan-500 font-mono text-[11px]"
                />
              </div>
              <div>
                <label className="text-[9px] text-slate-400 block mb-0.5">Longitude</label>
                <input
                  type="number"
                  step="any"
                  placeholder="91.8210"
                  value={originLon}
                  onChange={(e) => setOriginLon(e.target.value)}
                  required
                  className="w-full px-2.5 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-cyan-500 font-mono text-[11px]"
                />
              </div>
            </div>
          </div>

          {/* Destination Coordinates */}
          <div className="space-y-1">
            <span className="text-[10px] font-semibold uppercase tracking-wider text-rose-400 flex items-center gap-1">
              <span>🔴</span> Destination (Consignment Stop)
            </span>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="text-[9px] text-slate-400 block mb-0.5">Latitude</label>
                <input
                  type="number"
                  step="any"
                  placeholder="25.5788"
                  value={destLat}
                  onChange={(e) => setDestLat(e.target.value)}
                  required
                  className="w-full px-2.5 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-rose-500 font-mono text-[11px]"
                />
              </div>
              <div>
                <label className="text-[9px] text-slate-400 block mb-0.5">Longitude</label>
                <input
                  type="number"
                  step="any"
                  placeholder="91.8933"
                  value={destLon}
                  onChange={(e) => setDestLon(e.target.value)}
                  required
                  className="w-full px-2.5 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-rose-500 font-mono text-[11px]"
                />
              </div>
            </div>
          </div>

          {/* Profile Selector */}
          <div className="space-y-1.5 pt-1">
            <label className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 block">
              Multi-Objective Profile
            </label>
            <div className="grid grid-cols-3 gap-1.5">
              {[
                { id: "fastest", label: "Fastest", color: "hover:border-cyan-500 active:border-cyan-500", activeBg: "bg-cyan-500/20 border-cyan-500 text-cyan-300" },
                { id: "safest", label: "Safest", color: "hover:border-emerald-500 active:border-emerald-500", activeBg: "bg-emerald-500/20 border-emerald-500 text-emerald-300" },
                { id: "balanced", label: "Balanced", color: "hover:border-amber-500 active:border-amber-500", activeBg: "bg-amber-500/20 border-amber-500 text-amber-300" },
              ].map((p) => {
                const isActive = selectedProfile === p.id;
                return (
                  <button
                    key={p.id}
                    type="button"
                    onClick={() => onProfileChange(p.id)}
                    className={`py-1.5 rounded-lg border text-[11px] font-semibold transition-all text-center ${
                      isActive
                        ? p.activeBg
                        : "bg-slate-950 border-slate-800 text-slate-400 hover:text-white"
                    }`}
                  >
                    {p.label}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="pt-2 flex flex-col sm:flex-row gap-2">
            <button
              type="submit"
              disabled={loading}
              className="flex-1 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-semibold text-xs shadow-lg shadow-indigo-500/20 transition-all flex items-center justify-center gap-1.5"
            >
              {loading ? (
                <>
                  <span className="inline-block animate-spin">⏳</span>
                  <span>Optimizing...</span>
                </>
              ) : (
                <>
                  <span>🚀</span>
                  <span>Calculate Route</span>
                </>
              )}
            </button>
            <button
              type="button"
              onClick={handleCompare}
              disabled={loading}
              className="py-2 px-3 rounded-xl bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-slate-200 font-medium text-xs transition-all flex items-center justify-center gap-1"
              title="Compare Fastest, Safest, and Balanced Profiles side-by-side"
            >
              <span>⚖️</span>
              <span>Compare All</span>
            </button>
          </div>
        </form>
      ) : (
        /* Presets Tab */
        <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
          <span className="text-[10px] text-slate-400 block mb-1">
            Select major NER logistics hubs for fast testing:
          </span>
          {REGIONAL_HUB_PRESETS.map((hub) => (
            <div
              key={hub.name}
              className="p-2 rounded-lg bg-slate-950/60 border border-slate-800/80 flex items-center justify-between"
            >
              <div>
                <span className="font-semibold text-white block">{hub.name}</span>
                <span className="text-[10px] text-slate-400">
                  {hub.state} · {hub.lat.toFixed(2)}°N, {hub.lon.toFixed(2)}°E
                </span>
              </div>
              <div className="flex items-center gap-1">
                <button
                  type="button"
                  onClick={() => {
                    setPresetAsOrigin(hub);
                    setActiveTab("plan");
                  }}
                  className="px-2 py-0.5 rounded bg-cyan-950/60 hover:bg-cyan-900 border border-cyan-700/50 text-[10px] text-cyan-300"
                >
                  Origin
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setPresetAsDest(hub);
                    setActiveTab("plan");
                  }}
                  className="px-2 py-0.5 rounded bg-rose-950/60 hover:bg-rose-900 border border-rose-700/50 text-[10px] text-rose-300"
                >
                  Dest
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
