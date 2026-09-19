"use client";

import React from "react";
import dynamic from "next/dynamic";
import type { RouteIQMapProps } from "./RouteIQMap";

// Dynamically import Leaflet map component with ssr: false to prevent window/document SSR errors
const RouteIQMap = dynamic(() => import("./RouteIQMap"), {
  ssr: false,
  loading: () => (
    <div className="relative w-full h-full min-h-[500px] flex flex-col items-center justify-center rounded-2xl bg-slate-950 border border-slate-800 shadow-2xl p-6">
      <div className="relative flex items-center justify-center mb-4">
        <div className="h-14 w-14 rounded-full border-4 border-indigo-500/20 border-t-indigo-500 animate-spin" />
        <span className="absolute text-xl">🗺️</span>
      </div>
      <h3 className="text-sm font-semibold text-slate-200">Initializing GIS Engine...</h3>
      <p className="text-xs text-slate-500 mt-1 max-w-xs text-center">
        Loading CartoDB Dark Matter tiles, OSM Road Network, and NER Strategic Corridors.
      </p>
    </div>
  ),
});

export default function MapWrapper(props: RouteIQMapProps) {
  return <RouteIQMap {...props} />;
}
