"use client";

import React, { useEffect, useRef } from "react";
import L from "leaflet";
import MapControls, { LayerVisibilityState } from "./MapControls";
import MapLegend from "./MapLegend";
import { RouteResponse, RouteEdgeItem, CorridorResponse, Vehicle, Location, Delivery } from "@/lib/api";

export interface RouteIQMapProps {
  layers: LayerVisibilityState;
  onToggleLayer: (layer: keyof LayerVisibilityState) => void;
  roadEdges?: any[];
  corridors?: CorridorResponse[];
  onSelectCorridor?: (corridor: CorridorResponse) => void;
  activeRoute?: RouteResponse | null;
  comparisonRoutes?: RouteResponse[] | null;
  activeProfile?: string;
  selectedSegmentIndex?: number | null;
  onSelectSegment?: (index: number | null) => void;
  vehicles?: Vehicle[];
  locations?: Location[];
  deliveries?: Delivery[];
  showLegend: boolean;
  onToggleLegend: () => void;
}

// NER Geographic Center and Defaults
const NER_CENTER: [number, number] = [25.8, 92.5];
const DEFAULT_ZOOM = 7;
const MIN_ZOOM = 5;
const MAX_ZOOM = 18;

// Road Class Styling
const ROAD_TYPE_COLORS: Record<string, string> = {
  trunk: "#3b82f6", // Blue
  primary: "#06b6d4", // Cyan
  secondary: "#8b5cf6", // Purple
  tertiary: "#64748b", // Slate
  unclassified: "#475569",
};

// Profile Route Colors
const PROFILE_COLORS: Record<string, string> = {
  fastest: "#06b6d4", // Cyan
  safest: "#10b981", // Emerald Green
  balanced: "#a855f7", // Purple / Amber
};

export default function RouteIQMap({
  layers,
  onToggleLayer,
  roadEdges = [],
  corridors = [],
  onSelectCorridor,
  activeRoute,
  comparisonRoutes = [],
  activeProfile = "balanced",
  selectedSegmentIndex,
  onSelectSegment,
  vehicles = [],
  locations = [],
  deliveries = [],
  showLegend,
  onToggleLegend,
}: RouteIQMapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);

  // Layer groups refs to easily clear and re-render layers
  const roadNetworkLayerRef = useRef<L.LayerGroup | null>(null);
  const corridorsLayerRef = useRef<L.LayerGroup | null>(null);
  const selectedRouteLayerRef = useRef<L.LayerGroup | null>(null);
  const alternateRoutesLayerRef = useRef<L.LayerGroup | null>(null);
  const vehiclesLayerRef = useRef<L.LayerGroup | null>(null);
  const locationsLayerRef = useRef<L.LayerGroup | null>(null);
  const deliveriesLayerRef = useRef<L.LayerGroup | null>(null);
  const hazardOverlayLayerRef = useRef<L.LayerGroup | null>(null);

  // Initialize Map
  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const map = L.map(containerRef.current, {
      center: NER_CENTER,
      zoom: DEFAULT_ZOOM,
      minZoom: MIN_ZOOM,
      maxZoom: MAX_ZOOM,
      zoomControl: false,
    });

    // Add CartoDB Dark Matter tile layer
    L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>',
      subdomains: "abcd",
      maxZoom: 19,
    }).addTo(map);

    // Initialize layer groups and add to map in specific order
    roadNetworkLayerRef.current = L.layerGroup().addTo(map);
    corridorsLayerRef.current = L.layerGroup().addTo(map);
    alternateRoutesLayerRef.current = L.layerGroup().addTo(map);
    hazardOverlayLayerRef.current = L.layerGroup().addTo(map);
    selectedRouteLayerRef.current = L.layerGroup().addTo(map);
    deliveriesLayerRef.current = L.layerGroup().addTo(map);
    locationsLayerRef.current = L.layerGroup().addTo(map);
    vehiclesLayerRef.current = L.layerGroup().addTo(map);

    mapRef.current = map;

    // Handle container resize
    const resizeObserver = new ResizeObserver(() => {
      map.invalidateSize();
    });
    resizeObserver.observe(containerRef.current);

    return () => {
      resizeObserver.disconnect();
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // Map Controls Helpers
  const handleZoomIn = () => {
    mapRef.current?.zoomIn();
  };

  const handleZoomOut = () => {
    mapRef.current?.zoomOut();
  };

  const handleResetView = () => {
    mapRef.current?.flyTo(NER_CENTER, DEFAULT_ZOOM, { duration: 1 });
  };

  // 1. Render Road Network Layer
  useEffect(() => {
    const layerGroup = roadNetworkLayerRef.current;
    if (!layerGroup) return;
    layerGroup.clearLayers();

    if (!layers.roadNetwork || !roadEdges || roadEdges.length === 0) return;

    roadEdges.forEach((edge) => {
      if (!edge.geometry || !edge.geometry.coordinates) return;
      const coords = edge.geometry.coordinates.map(
        (c: [number, number]) => [c[1], c[0]] as [number, number]
      );
      const color = ROAD_TYPE_COLORS[edge.road_type] || "#64748b";

      const polyline = L.polyline(coords, {
        color: color,
        weight: edge.road_type === "trunk" ? 3 : edge.road_type === "primary" ? 2.5 : 1.5,
        opacity: 0.65,
      });

      polyline.bindPopup(`
        <div class="text-xs space-y-1">
          <div class="font-bold text-white">${edge.road_name || edge.name || "Highway Segment"}</div>
          <div class="text-slate-300">Type: <span class="capitalize text-indigo-300 font-mono">${edge.road_type}</span></div>
          <div class="text-slate-300">Length: <span class="font-mono">${((edge.length_meters || edge.length_m || 0) / 1000).toFixed(1)} km</span></div>
          <div class="text-slate-300">Speed: <span class="font-mono">${edge.max_speed_kph || edge.speed_limit_kmh || 50} km/h</span></div>
        </div>
      `);

      polyline.addTo(layerGroup);
    });
  }, [layers.roadNetwork, roadEdges]);

  // 2. Render Strategic Corridors Layer
  useEffect(() => {
    const layerGroup = corridorsLayerRef.current;
    if (!layerGroup) return;
    layerGroup.clearLayers();

    if (!layers.corridors || !corridors || corridors.length === 0) return;

    corridors.forEach((corr) => {
      const waypoints = corr.intermediate_waypoints || (corr as any).waypoints || [];
      if (waypoints && waypoints.length > 0) {
        waypoints.forEach((wp: any, idx: number) => {
          const lat = wp.latitude ?? wp.coordinates?.[1];
          const lon = wp.longitude ?? wp.coordinates?.[0];
          if (lat == null || lon == null) return;

          const isTerminus = idx === 0 || idx === waypoints.length - 1;
          const markerIcon = L.divIcon({
            className: "custom-div-icon",
            html: `
              <div class="flex items-center justify-center h-5 w-5 rounded-full ${
                isTerminus ? "bg-amber-500 ring-4 ring-amber-500/30" : "bg-amber-600/80 ring-2 ring-amber-600/20"
              } text-white shadow-lg text-[9px] font-bold">
                ${idx + 1}
              </div>
            `,
            iconSize: [20, 20],
            iconAnchor: [10, 10],
          });

          const marker = L.marker([lat, lon], { icon: markerIcon });
          marker.bindTooltip(`<b>${corr.name}</b><br/>Waypoint: ${wp.name}`, {
            direction: "top",
            offset: [0, -10],
          });
          marker.on("click", () => {
            onSelectCorridor?.(corr);
          });
          marker.addTo(layerGroup);
        });

        // Corridor connecting polyline
        const coords: [number, number][] = waypoints
          .map((wp: any) => {
            const lat = wp.latitude ?? wp.coordinates?.[1];
            const lon = wp.longitude ?? wp.coordinates?.[0];
            return lat != null && lon != null ? ([lat, lon] as [number, number]) : null;
          })
          .filter((c: [number, number] | null): c is [number, number] => c !== null);

        if (coords.length > 1) {
          const polyline = L.polyline(coords, {
            color: "#f59e0b",
            weight: 3.5,
            opacity: 0.85,
            dashArray: "6, 8",
          });

          polyline.bindPopup(`
            <div class="text-xs space-y-1.5 p-1">
              <div class="font-bold text-amber-400 text-sm">${corr.name}</div>
              <div class="text-slate-300 font-mono text-[11px]">${corr.national_highway || ""} • ${corr.terrain_type || "Corridor"}</div>
              <div class="text-slate-400 leading-relaxed">${corr.strategic_notes || ""}</div>
              <div class="text-slate-300">Length: <span class="font-bold text-white font-mono">${corr.approximate_length_km || 0} km</span></div>
            </div>
          `);

          polyline.on("click", () => {
            onSelectCorridor?.(corr);
          });

          polyline.addTo(layerGroup);
        }
      }
    });
  }, [layers.corridors, corridors, onSelectCorridor]);

  // 3. Render Alternate Routes (from /compare)
  useEffect(() => {
    const layerGroup = alternateRoutesLayerRef.current;
    if (!layerGroup) return;
    layerGroup.clearLayers();

    if (!layers.alternateRoutes || !comparisonRoutes || comparisonRoutes.length === 0) return;

    comparisonRoutes.forEach((route) => {
      // Don't duplicate the currently active profile route if selectedRoute is visible
      if (route.profile.toLowerCase() === activeProfile.toLowerCase() && layers.selectedRoute) return;

      if (route.geometry?.coordinates && route.geometry.coordinates.length > 0) {
        const coords = route.geometry.coordinates.map(
          (c: [number, number]) => [c[1], c[0]] as [number, number]
        );
        const color = PROFILE_COLORS[route.profile.toLowerCase()] || "#94a3b8";

        const polyline = L.polyline(coords, {
          color: color,
          weight: 3.5,
          opacity: 0.7,
          dashArray: "4, 6",
        });

        polyline.bindPopup(`
          <div class="text-xs space-y-1">
            <div class="font-bold uppercase tracking-wide text-xs" style="color: ${color}">
              ${route.profile} Profile Route
            </div>
            <div class="text-slate-300">Distance: <span class="font-mono text-white">${route.metrics.distance_km} km</span></div>
            <div class="text-slate-300">Travel Time: <span class="font-mono text-white">${route.metrics.estimated_time_minutes} min</span></div>
            <div class="text-slate-300">Modeled Risk: <span class="font-mono text-white">${route.metrics.risk_score}</span></div>
          </div>
        `);

        polyline.addTo(layerGroup);
      }
    });
  }, [layers.alternateRoutes, layers.selectedRoute, comparisonRoutes, activeProfile]);

  // 4. Render Active Selected Route & Segments
  useEffect(() => {
    const layerGroup = selectedRouteLayerRef.current;
    if (!layerGroup) return;
    layerGroup.clearLayers();

    if (!layers.selectedRoute || !activeRoute) return;

    // A. Main route polyline
    if (activeRoute.geometry?.coordinates && activeRoute.geometry.coordinates.length > 0) {
      const coords = activeRoute.geometry.coordinates.map(
        (c: [number, number]) => [c[1], c[0]] as [number, number]
      );
      const color = PROFILE_COLORS[activeProfile.toLowerCase()] || "#06b6d4";

      // Glow effect background polyline
      L.polyline(coords, {
        color: color,
        weight: 8,
        opacity: 0.25,
      }).addTo(layerGroup);

      // Foreground crisp polyline
      const mainLine = L.polyline(coords, {
        color: color,
        weight: 4,
        opacity: 0.95,
      }).addTo(layerGroup);

      // Fit map bounds to active route
      if (mapRef.current && coords.length > 1) {
        mapRef.current.fitBounds(mainLine.getBounds(), {
          padding: [50, 50],
          maxZoom: 14,
        });
      }

      // Origin Marker
      const startCoord = coords[0];
      const startIcon = L.divIcon({
        className: "custom-div-icon",
        html: `
          <div class="flex items-center justify-center h-7 w-7 rounded-full bg-emerald-500 text-white font-bold ring-4 ring-emerald-500/30 shadow-xl text-xs">
            A
          </div>
        `,
        iconSize: [28, 28],
        iconAnchor: [14, 14],
      });
      L.marker(startCoord, { icon: startIcon })
        .bindTooltip("<b>Origin</b><br/>" + `${activeRoute.origin.latitude.toFixed(4)}, ${activeRoute.origin.longitude.toFixed(4)}`, {
          direction: "top",
          offset: [0, -14],
        })
        .addTo(layerGroup);

      // Destination Marker
      const endCoord = coords[coords.length - 1];
      const endIcon = L.divIcon({
        className: "custom-div-icon",
        html: `
          <div class="flex items-center justify-center h-7 w-7 rounded-full bg-rose-500 text-white font-bold ring-4 ring-rose-500/30 shadow-xl text-xs">
            B
          </div>
        `,
        iconSize: [28, 28],
        iconAnchor: [14, 14],
      });
      L.marker(endCoord, { icon: endIcon })
        .bindTooltip("<b>Destination</b><br/>" + `${activeRoute.destination.latitude.toFixed(4)}, ${activeRoute.destination.longitude.toFixed(4)}`, {
          direction: "top",
          offset: [0, -14],
        })
        .addTo(layerGroup);
    }

    // B. Individual interactive segments
    const edges = activeRoute.edges || (activeRoute as any).segments || [];
    if (edges && edges.length > 0 && activeRoute.geometry?.coordinates) {
      // If edges don't have separate geometries, split nodes or map to coordinate indices
      const coords = activeRoute.geometry.coordinates;
      edges.forEach((edge: RouteEdgeItem, idx: number) => {
        const segCoords = (edge as any).geometry?.coordinates
          ? (edge as any).geometry.coordinates.map((c: [number, number]) => [c[1], c[0]] as [number, number])
          : coords.length > idx + 1
          ? [[coords[idx][1], coords[idx][0]], [coords[idx + 1][1], coords[idx + 1][0]]]
          : null;

        if (!segCoords) return;
        const isSelected = selectedSegmentIndex === idx;

        const segLine = L.polyline(segCoords, {
          color: isSelected ? "#f43f5e" : "transparent",
          weight: isSelected ? 8 : 12,
          opacity: isSelected ? 0.9 : 0.001,
        });

        segLine.on("click", () => {
          onSelectSegment?.(idx);
        });

        segLine.bindTooltip(
          `<b>Segment #${idx + 1}</b><br/>${edge.road_name || "Highway"}<br/>${(
            edge.length_meters / 1000
          ).toFixed(1)} km • Risk: ${edge.risk_breakdown?.overall_risk?.toFixed(2) ?? 0}`,
          { direction: "top", sticky: true }
        );

        segLine.addTo(layerGroup);
      });
    }
  }, [layers.selectedRoute, activeRoute, activeProfile, selectedSegmentIndex, onSelectSegment]);

  // 5. Render Modeled Risk Overlay
  useEffect(() => {
    const layerGroup = hazardOverlayLayerRef.current;
    if (!layerGroup) return;
    layerGroup.clearLayers();

    if (!layers.hazardOverlay || !activeRoute) return;

    const edges = activeRoute.edges || [];
    const coords = activeRoute.geometry?.coordinates || [];

    edges.forEach((edge: RouteEdgeItem, idx: number) => {
      const segCoords = (edge as any).geometry?.coordinates
        ? (edge as any).geometry.coordinates.map((c: [number, number]) => [c[1], c[0]] as [number, number])
        : coords.length > idx + 1
        ? [[coords[idx][1], coords[idx][0]], [coords[idx + 1][1], coords[idx + 1][0]]]
        : null;

      if (!segCoords) return;

      const riskScore = edge.risk_breakdown?.overall_risk ?? 0;
      let riskColor = "#10b981"; // Low risk (< 0.25)
      let riskTier = "Low Modeled Risk";
      if (riskScore >= 0.5) {
        riskColor = "#ef4444"; // High risk
        riskTier = "High Modeled Risk (Monsoon/Flood/Slope)";
      } else if (riskScore >= 0.25) {
        riskColor = "#f59e0b"; // Medium risk
        riskTier = "Medium Modeled Risk";
      }

      const riskLine = L.polyline(segCoords, {
        color: riskColor,
        weight: 6,
        opacity: 0.65,
        lineCap: "round",
      });

      riskLine.bindPopup(`
        <div class="text-xs space-y-1">
          <div class="font-bold" style="color: ${riskColor}">${riskTier}</div>
          <div class="text-slate-300">Composite Risk: <span class="font-mono text-white">${riskScore.toFixed(3)}</span></div>
          <div class="text-slate-400 text-[10px]">Heuristic penalty calculation. No live sensor feed.</div>
        </div>
      `);

      riskLine.addTo(layerGroup);
    });
  }, [layers.hazardOverlay, activeRoute]);

  // 6. Render Fleet Vehicles Layer (Tenant Isolated)
  useEffect(() => {
    const layerGroup = vehiclesLayerRef.current;
    if (!layerGroup) return;
    layerGroup.clearLayers();

    if (!layers.vehicles || !vehicles || vehicles.length === 0) return;

    // Anchor vehicles to locations or distributed points in NER
    vehicles.forEach((veh, idx) => {
      const baseLat = 26.1445 + (idx % 4) * 0.2 - 0.1;
      const baseLng = 91.7362 + ((idx * 3) % 5) * 0.3 - 0.2;

      const isAvailable = veh.status === "available";
      const iconHtml = `
        <div class="flex items-center justify-center h-8 w-8 rounded-xl bg-slate-900 border ${
          isAvailable ? "border-emerald-500 text-emerald-400 shadow-emerald-500/30" : "border-amber-500 text-amber-400"
        } shadow-lg text-sm">
          🚚
        </div>
      `;

      const icon = L.divIcon({
        className: "custom-div-icon",
        html: iconHtml,
        iconSize: [32, 32],
        iconAnchor: [16, 16],
      });

      const marker = L.marker([baseLat, baseLng], { icon });
      marker.bindPopup(`
        <div class="text-xs space-y-1.5 p-1">
          <div class="flex items-center justify-between gap-2">
            <span class="font-bold text-white font-mono">${veh.registration_number || veh.vehicle_name}</span>
            <span class="px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase ${
              isAvailable ? "bg-emerald-500/20 text-emerald-300" : "bg-amber-500/20 text-amber-300"
            }">${veh.status}</span>
          </div>
          <div class="text-slate-300">Name: <span class="text-white">${veh.vehicle_name}</span></div>
          <div class="text-slate-300">Type: <span class="capitalize text-indigo-300">${veh.vehicle_type}</span></div>
          <div class="text-slate-300">Capacity: <span class="font-mono text-white">${veh.capacity} ${veh.capacity_unit}</span></div>
          <div class="text-[10px] text-slate-500 border-t border-slate-800 pt-1">Scoped to Organization</div>
        </div>
      `);

      marker.addTo(layerGroup);
    });
  }, [layers.vehicles, vehicles]);

  // 7. Render Depots and Facilities Layer (Tenant Isolated)
  useEffect(() => {
    const layerGroup = locationsLayerRef.current;
    if (!layerGroup) return;
    layerGroup.clearLayers();

    if (!layers.locations || !locations || locations.length === 0) return;

    locations.forEach((loc) => {
      if (loc.latitude == null || loc.longitude == null) return;

      const iconHtml = `
        <div class="flex items-center justify-center h-8 w-8 rounded-xl bg-indigo-950 border border-indigo-500 text-indigo-300 shadow-lg shadow-indigo-500/30 text-sm">
          📍
        </div>
      `;

      const icon = L.divIcon({
        className: "custom-div-icon",
        html: iconHtml,
        iconSize: [32, 32],
        iconAnchor: [16, 16],
      });

      const marker = L.marker([loc.latitude, loc.longitude], { icon });
      marker.bindPopup(`
        <div class="text-xs space-y-1.5 p-1">
          <div class="font-bold text-indigo-300 text-sm">${loc.name}</div>
          <div class="text-slate-300 font-mono text-[11px]">${loc.city || ""}, ${loc.state || ""}</div>
          <div class="text-slate-400">Address: <span class="text-slate-200">${loc.address_line || "Regional Hub"}</span></div>
          <div class="text-[10px] text-slate-500 border-t border-slate-800 pt-1">Tenant Facility</div>
        </div>
      `);

      marker.addTo(layerGroup);
    });
  }, [layers.locations, locations]);

  // 8. Render Delivery Orders Layer (Tenant Isolated)
  useEffect(() => {
    const layerGroup = deliveriesLayerRef.current;
    if (!layerGroup) return;
    layerGroup.clearLayers();

    if (!layers.deliveries || !deliveries || deliveries.length === 0) return;

    // Connect locations if found
    const locMap = new Map(locations.map((l) => [l.id, l]));

    deliveries.forEach((del) => {
      const pLoc = locMap.get(del.pickup_location_id);
      const dLoc = locMap.get(del.delivery_location_id);

      if (pLoc && dLoc) {
        const line = L.polyline(
          [
            [pLoc.latitude, pLoc.longitude],
            [dLoc.latitude, dLoc.longitude],
          ],
          {
            color: "#f43f5e",
            weight: 2,
            opacity: 0.65,
            dashArray: "3, 6",
          }
        );

        line.bindPopup(`
          <div class="text-xs space-y-1 p-1">
            <div class="font-bold text-rose-400">Order: ${del.reference_number}</div>
            <div class="text-slate-300">Weight: <span class="font-mono text-white">${del.package_weight} kg</span></div>
            <div class="text-slate-300">Priority: <span class="font-mono uppercase text-indigo-300">${del.priority}</span></div>
            <div class="text-slate-300">Status: <span class="font-mono uppercase text-emerald-400">${del.status}</span></div>
          </div>
        `);

        line.addTo(layerGroup);
      }
    });
  }, [layers.deliveries, deliveries, locations]);

  return (
    <div className="relative w-full h-full min-h-[550px] overflow-hidden rounded-2xl bg-slate-950 border border-slate-800 shadow-2xl">
      {/* Map DOM Target */}
      <div ref={containerRef} className="w-full h-full z-0" />

      {/* Floating Map Navigation & Layer Controls */}
      <MapControls
        layers={layers}
        onToggleLayer={onToggleLayer}
        onResetView={handleResetView}
        onZoomIn={handleZoomIn}
        onZoomOut={handleZoomOut}
        showLegend={showLegend}
        onToggleLegend={onToggleLegend}
      />

      {/* Floating Symbology Legend */}
      <MapLegend isOpen={showLegend} onClose={onToggleLegend} />
    </div>
  );
}
