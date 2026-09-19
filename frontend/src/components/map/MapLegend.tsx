"use client";

import React from "react";

interface MapLegendProps {
  isOpen?: boolean;
  onClose: () => void;
}

export default function MapLegend({ isOpen = true, onClose }: MapLegendProps) {
  if (!isOpen) return null;

  return (
    <div className="absolute bottom-6 right-4 z-[1000] w-72 p-4 rounded-xl bg-slate-900/95 backdrop-blur-md border border-slate-800 shadow-2xl space-y-3.5 text-xs text-slate-300 animate-in fade-in duration-150">
      <div className="flex items-center justify-between pb-2 border-b border-slate-800">
        <div className="flex items-center gap-1.5 font-semibold text-white">
          <span>🗺️</span>
          <span>Map Symbology &amp; Legend</span>
        </div>
        <button
          onClick={onClose}
          className="text-slate-400 hover:text-white p-1 rounded-md hover:bg-slate-800 text-xs"
          title="Close Legend"
        >
          ✕
        </button>
      </div>

      {/* Road Classifications */}
      <div>
        <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 block mb-1.5">
          Road Classifications (OSM)
        </span>
        <div className="grid grid-cols-2 gap-1.5 text-[11px]">
          <div className="flex items-center gap-2">
            <span className="h-2 w-5 rounded-full bg-blue-500 inline-block" />
            <span>Trunk (NH)</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="h-1.5 w-5 rounded-full bg-cyan-400 inline-block" />
            <span>Primary (SH)</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="h-1.5 w-5 rounded-full bg-purple-400 inline-block" />
            <span>Secondary</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="h-1 w-5 rounded-full bg-slate-500 inline-block" />
            <span>Tertiary / Local</span>
          </div>
        </div>
      </div>

      {/* Strategic Corridors */}
      <div>
        <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 block mb-1.5">
          NER Strategic Corridors
        </span>
        <div className="flex items-center gap-2 text-[11px]">
          <span className="h-2 w-6 rounded-full bg-amber-400 inline-block shadow-sm shadow-amber-400/50" />
          <span>National Highway Lifeline (NH-06, NH-27, etc.)</span>
        </div>
      </div>

      {/* Routing Profiles */}
      <div>
        <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 block mb-1.5">
          Optimization Profiles
        </span>
        <div className="space-y-1 text-[11px]">
          <div className="flex items-center gap-2">
            <span className="h-2 w-5 rounded-full bg-cyan-400 inline-block" />
            <span className="text-cyan-300 font-medium">Fastest</span>
            <span className="text-[10px] text-slate-500">(Time prioritized)</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="h-2 w-5 rounded-full bg-emerald-400 inline-block" />
            <span className="text-emerald-300 font-medium">Safest</span>
            <span className="text-[10px] text-slate-500">(Risk &amp; slope avoided)</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="h-2 w-5 rounded-full bg-amber-400 inline-block" />
            <span className="text-amber-300 font-medium">Balanced</span>
            <span className="text-[10px] text-slate-500">(Equilibrium trade-off)</span>
          </div>
        </div>
      </div>

      {/* Tenant Operational Assets */}
      <div>
        <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 block mb-1.5">
          Operational Assets (Tenant)
        </span>
        <div className="grid grid-cols-2 gap-1.5 text-[11px]">
          <div className="flex items-center gap-1.5">
            <span className="text-sm">🚚</span>
            <span>Fleet Vehicle</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-sm">📍</span>
            <span>Facility / Depot</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-sm">📦</span>
            <span>Consignment</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="text-sm">🏔️</span>
            <span>Corridor Node</span>
          </div>
        </div>
      </div>

      {/* Modeled Risk Overlay */}
      <div className="pt-2 border-t border-slate-800">
        <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 block mb-1.5">
          Modeled Routing Risk
        </span>
        <div className="flex items-center justify-between text-[10px] text-slate-400">
          <span className="flex items-center gap-1">
            <span className="h-2 w-2 rounded-full bg-emerald-500 inline-block" />
            <span>Low (&lt;0.25)</span>
          </span>
          <span className="flex items-center gap-1">
            <span className="h-2 w-2 rounded-full bg-amber-500 inline-block" />
            <span>Moderate</span>
          </span>
          <span className="flex items-center gap-1">
            <span className="h-2 w-2 rounded-full bg-rose-500 inline-block" />
            <span>High (&gt;0.50)</span>
          </span>
        </div>
        <p className="text-[9px] text-slate-500 italic mt-1 leading-tight">
          * Modeled routing optimization penalty. Not a live sensor or official disaster alert.
        </p>
      </div>
    </div>
  );
}
