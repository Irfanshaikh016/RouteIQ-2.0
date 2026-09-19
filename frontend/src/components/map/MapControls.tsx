"use client";

import React, { useState } from "react";

export interface LayerVisibilityState {
  roadNetwork: boolean;
  corridors: boolean;
  selectedRoute: boolean;
  alternateRoutes: boolean;
  vehicles: boolean;
  locations: boolean;
  deliveries: boolean;
  hazardOverlay: boolean;
  fleetRoutes?: boolean;
  roadRestrictions?: boolean;
}

interface MapControlsProps {
  layers: LayerVisibilityState;
  onToggleLayer: (layer: keyof LayerVisibilityState) => void;
  onResetView: () => void;
  onZoomIn: () => void;
  onZoomOut: () => void;
  showLegend: boolean;
  onToggleLegend: () => void;
}

export default function MapControls({
  layers,
  onToggleLayer,
  onResetView,
  onZoomIn,
  onZoomOut,
  showLegend,
  onToggleLegend,
}: MapControlsProps) {
  const [showLayerMenu, setShowLayerMenu] = useState(false);

  const layerItems: { key: keyof LayerVisibilityState; label: string; icon: string; color: string }[] = [
    { key: "roadNetwork", label: "Road Network (OSM)", icon: "🛣️", color: "text-blue-400" },
    { key: "corridors", label: "NER Strategic Corridors", icon: "🏔️", color: "text-amber-400" },
    { key: "selectedRoute", label: "Selected Route", icon: "⚡", color: "text-cyan-400" },
    { key: "alternateRoutes", label: "Alternate Profiles", icon: "🔀", color: "text-purple-400" },
    { key: "fleetRoutes", label: "VRP Multi-Fleet Routes", icon: "🎨", color: "text-teal-400" },
    { key: "roadRestrictions", label: "Road Closures & Slows", icon: "🚧", color: "text-red-400" },
    { key: "vehicles", label: "Fleet Vehicles (Telemetry)", icon: "🚚", color: "text-emerald-400" },
    { key: "locations", label: "Depots & Facilities", icon: "📍", color: "text-indigo-400" },
    { key: "deliveries", label: "Consignment Orders", icon: "📦", color: "text-rose-400" },
    { key: "hazardOverlay", label: "Modeled Risk Overlay", icon: "⚠️", color: "text-yellow-400" },
  ];

  return (
    <div className="absolute top-4 right-4 z-[1000] flex flex-col items-end gap-2">
      {/* Primary Map Navigation Controls */}
      <div className="flex items-center gap-1.5 p-1.5 rounded-xl bg-slate-900/90 backdrop-blur-md border border-slate-800 shadow-xl text-xs">
        <button
          onClick={onZoomIn}
          title="Zoom In"
          className="h-8 w-8 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-white font-bold flex items-center justify-center transition-colors shadow-sm"
        >
          +
        </button>
        <button
          onClick={onZoomOut}
          title="Zoom Out"
          className="h-8 w-8 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-white font-bold flex items-center justify-center transition-colors shadow-sm"
        >
          −
        </button>
        <div className="h-5 w-px bg-slate-700 mx-0.5" />
        <button
          onClick={onResetView}
          title="Reset View to North Eastern Region"
          className="px-2.5 h-8 rounded-lg bg-slate-800/80 hover:bg-indigo-600/30 hover:text-indigo-300 text-slate-300 font-medium flex items-center gap-1.5 transition-colors shadow-sm"
        >
          <span>🎯</span>
          <span className="hidden sm:inline">NER View</span>
        </button>
        <button
          onClick={() => setShowLayerMenu(!showLayerMenu)}
          title="Toggle Layers"
          className={`px-2.5 h-8 rounded-lg font-medium flex items-center gap-1.5 transition-colors shadow-sm ${
            showLayerMenu
              ? "bg-indigo-600 text-white"
              : "bg-slate-800/80 hover:bg-slate-700 text-slate-300"
          }`}
        >
          <span>🥞</span>
          <span className="hidden sm:inline">Layers</span>
        </button>
        <button
          onClick={onToggleLegend}
          title="Toggle Map Legend"
          className={`px-2.5 h-8 rounded-lg font-medium flex items-center gap-1.5 transition-colors shadow-sm ${
            showLegend
              ? "bg-indigo-600 text-white"
              : "bg-slate-800/80 hover:bg-slate-700 text-slate-300"
          }`}
        >
          <span>ℹ️</span>
          <span className="hidden sm:inline">Legend</span>
        </button>
      </div>

      {/* Dropdown Menu for Layer Toggles */}
      {showLayerMenu && (
        <div className="w-64 p-3 rounded-xl bg-slate-900/95 backdrop-blur-md border border-slate-800 shadow-2xl space-y-2 animate-in fade-in duration-150">
          <div className="flex items-center justify-between pb-2 border-b border-slate-800">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              Active Map Overlays
            </span>
            <span className="text-[10px] text-indigo-400">GIS Layers</span>
          </div>

          <div className="space-y-1">
            {layerItems.map((item) => {
              const active = layers[item.key];
              return (
                <button
                  key={item.key}
                  onClick={() => onToggleLayer(item.key)}
                  className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs transition-colors ${
                    active
                      ? "bg-indigo-500/10 text-white border border-indigo-500/30"
                      : "bg-slate-950/40 text-slate-400 hover:bg-slate-800/50 hover:text-slate-200 border border-transparent"
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <span>{item.icon}</span>
                    <span className={active ? item.color : "text-slate-400"}>
                      {item.label}
                    </span>
                  </div>
                  <span
                    className={`h-2 w-2 rounded-full ${
                      active ? "bg-emerald-400 shadow-sm shadow-emerald-400/50" : "bg-slate-600"
                    }`}
                  />
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
