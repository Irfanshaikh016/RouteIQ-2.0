"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import Header from "@/components/Header";
import MapWrapper from "@/components/map/MapWrapper";
import RoutePlannerSidebar from "@/components/map/RoutePlannerSidebar";
import RouteMetricsPanel from "@/components/map/RouteMetricsPanel";
import RouteSegmentInspector from "@/components/map/RouteSegmentInspector";
import CorridorInfoModal from "@/components/map/CorridorInfoModal";
import DispatchPanel from "@/components/dispatch/DispatchPanel";
import OptimizationResultCard from "@/components/dispatch/OptimizationResultCard";
import VehicleTelemetryDrawer from "@/components/dispatch/VehicleTelemetryDrawer";
import { LayerVisibilityState } from "@/components/map/MapControls";
import {
  getStoredUser,
  listVehicles,
  listLocations,
  listDeliveries,
  listCorridors,
  listRoadEdges,
  calculateRoute,
  compareRoutes,
  getFleetTelemetry,
  getActiveHazards,
  getRoadRestrictions,
  TokenResponse,
  Vehicle,
  Location,
  Delivery,
  CorridorResponse,
  RouteResponse,
  RouteRequest,
  VehicleStateItem,
  RoadRestrictionItem,
  HazardEventItem,
  OptimizationResult,
} from "@/lib/api";

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<TokenResponse | null>(null);

  // Tenant-isolated logistics data
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [locations, setLocations] = useState<Location[]>([]);
  const [deliveries, setDeliveries] = useState<Delivery[]>([]);

  // Phase 6 Telemetry, Weather & Dispatch State
  const [fleetTelemetry, setFleetTelemetry] = useState<VehicleStateItem[]>([]);
  const [roadRestrictions, setRoadRestrictions] = useState<RoadRestrictionItem[]>([]);
  const [activeHazards, setActiveHazards] = useState<HazardEventItem[]>([]);
  const [activeOptimization, setActiveOptimization] = useState<OptimizationResult | null>(null);
  const [selectedTelemetryVehicle, setSelectedTelemetryVehicle] = useState<VehicleStateItem | null>(null);
  const [selectedRouteVehicleId, setSelectedRouteVehicleId] = useState<string | null>(null);
  const [loadingDispatch, setLoadingDispatch] = useState(false);

  // Shared GIS road network data
  const [corridors, setCorridors] = useState<CorridorResponse[]>([]);
  const [roadEdges, setRoadEdges] = useState<any[]>([]);

  // Routing State
  const [originLat, setOriginLat] = useState<string>("26.1158");
  const [originLon, setOriginLon] = useState<string>("91.8210");
  const [destLat, setDestLat] = useState<string>("25.5788");
  const [destLon, setDestLon] = useState<string>("91.8933");
  const [selectedProfile, setSelectedProfile] = useState<string>("balanced");

  const [activeRoute, setActiveRoute] = useState<RouteResponse | null>(null);
  const [comparisonRoutes, setComparisonRoutes] = useState<RouteResponse[] | null>(null);
  const [activeProfile, setActiveProfile] = useState<string>("balanced");
  const [selectedSegmentIndex, setSelectedSegmentIndex] = useState<number | null>(null);
  const [selectedCorridor, setSelectedCorridor] = useState<CorridorResponse | null>(null);

  // UI & Layer States
  const [activeTab, setActiveTab] = useState<"planner" | "metrics" | "inspector" | "dispatch" | "assets">("planner");
  const [showLegend, setShowLegend] = useState(false);
  const [loadingRoute, setLoadingRoute] = useState(false);
  const [loadingCompare, setLoadingCompare] = useState(false);
  const [dataLoading, setDataLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 8 GIS Layer toggles
  const [layers, setLayers] = useState<LayerVisibilityState>({
    roadNetwork: true,
    corridors: true,
    selectedRoute: true,
    alternateRoutes: false,
    vehicles: true,
    locations: true,
    deliveries: true,
    hazardOverlay: false,
  });

  const toggleLayer = (key: keyof LayerVisibilityState) => {
    setLayers((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  // Auth & Initial Data Ingestion
  useEffect(() => {
    const currentUser = getStoredUser();
    if (!currentUser) {
      router.push("/login");
      return;
    }
    setUser(currentUser);

    const loadInitialData = async () => {
      setDataLoading(true);
      try {
        const [vList, lList, dList, corrRes, edgeRes, telRes, hazRes, restrRes] = await Promise.allSettled([
          listVehicles(),
          listLocations(),
          listDeliveries(),
          listCorridors(),
          listRoadEdges({ limit: 80 }),
          getFleetTelemetry(),
          getActiveHazards(),
          getRoadRestrictions(),
        ]);

        if (vList.status === "fulfilled") setVehicles(vList.value);
        if (lList.status === "fulfilled") setLocations(lList.value);
        if (dList.status === "fulfilled") setDeliveries(dList.value);
        if (corrRes.status === "fulfilled") setCorridors(corrRes.value.corridors || []);
        if (edgeRes.status === "fulfilled") setRoadEdges(edgeRes.value.edges || []);
        if (telRes.status === "fulfilled") setFleetTelemetry(telRes.value.vehicles || []);
        if (hazRes.status === "fulfilled") setActiveHazards(hazRes.value || []);
        if (restrRes.status === "fulfilled") setRoadRestrictions(restrRes.value || []);
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : "Failed to load dashboard data";
        setError(msg);
      } finally {
        setDataLoading(false);
      }
    };

    loadInitialData();
  }, [router]);

  // Handle Route Calculation
  const handleCalculate = async (req: RouteRequest) => {
    setError(null);
    setLoadingRoute(true);
    setActiveProfile(req.profile || "balanced");
    try {
      const result = await calculateRoute(req);
      setActiveRoute(result);
      setSelectedSegmentIndex(null);
      // Auto-enable selected route layer
      setLayers((prev) => ({ ...prev, selectedRoute: true }));
      // Switch to metrics tab
      setActiveTab("metrics");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Route calculation failed";
      setError(msg);
    } finally {
      setLoadingRoute(false);
    }
  };

  // Handle Multi-Profile Route Comparison
  const handleCompare = async (req: RouteRequest) => {
    setError(null);
    setLoadingCompare(true);
    try {
      const result = await compareRoutes(req);
      setComparisonRoutes(result.routes || []);
      if (result.routes && result.routes.length > 0) {
        // Set first route as active if none set
        setActiveRoute(result.routes[0]);
        setActiveProfile(result.routes[0].profile.toLowerCase());
      }
      // Enable alternate routes layer
      setLayers((prev) => ({ ...prev, alternateRoutes: true, selectedRoute: true }));
      // Switch to metrics tab to see comparison table
      setActiveTab("metrics");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Route comparison failed";
      setError(msg);
    } finally {
      setLoadingCompare(false);
    }
  };

  if (!user) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center">
        <p className="text-sm text-slate-400">Verifying session...</p>
      </div>
    );
  }

  const availableVehicles = vehicles.filter((v) => v.status === "available").length;
  const pendingDeliveries = deliveries.filter((d) => d.status === "pending" || d.status === "assigned").length;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <Header />

      {/* Operations Console Main Workspace */}
      <main className="flex-1 flex flex-col p-4 sm:p-6 gap-4 max-w-[1720px] w-full mx-auto">
        {/* KPI & Multi-Tenant Status Bar */}
        <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4 p-4 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-xl">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-xl">
              🗺️
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-lg sm:text-xl font-bold text-white tracking-tight">
                  GIS Logistics Operations Console
                </h1>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 uppercase tracking-wider">
                  NER Core
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Organization: <span className="text-slate-200 font-mono font-medium">{user.organization_id}</span> · User:{" "}
                <span className="text-indigo-300 font-medium">{user.full_name}</span> ({user.role})
              </p>
            </div>
          </div>

          {/* Real-time KPI Badges */}
          <div className="flex flex-wrap items-center gap-3 text-xs">
            <Link
              href="/vehicles"
              className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-950/60 border border-slate-800 hover:border-indigo-500/40 transition-colors"
            >
              <span>🚚</span>
              <span className="text-slate-400">Fleet:</span>
              <span className="font-bold text-white font-mono">{vehicles.length}</span>
              <span className="text-[10px] text-emerald-400">({availableVehicles} ready)</span>
            </Link>

            <Link
              href="/locations"
              className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-950/60 border border-slate-800 hover:border-indigo-500/40 transition-colors"
            >
              <span>📍</span>
              <span className="text-slate-400">Hubs:</span>
              <span className="font-bold text-white font-mono">{locations.length}</span>
            </Link>

            <Link
              href="/deliveries"
              className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-950/60 border border-slate-800 hover:border-indigo-500/40 transition-colors"
            >
              <span>📦</span>
              <span className="text-slate-400">Consignments:</span>
              <span className="font-bold text-white font-mono">{deliveries.length}</span>
              <span className="text-[10px] text-amber-400">({pendingDeliveries} active)</span>
            </Link>

            <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-950/60 border border-slate-800">
              <span>🏔️</span>
              <span className="text-slate-400">Strategic Corridors:</span>
              <span className="font-bold text-amber-400 font-mono">{corridors.length || 7}</span>
            </div>
          </div>
        </div>

        {/* Global Error Banner */}
        {error && (
          <div className="p-3.5 rounded-xl bg-red-500/10 border border-red-500/20 text-red-300 text-xs flex items-center justify-between shadow-lg">
            <div className="flex items-center gap-2">
              <span>⚠️</span>
              <span>{error}</span>
            </div>
            <button
              onClick={() => setError(null)}
              className="px-2 py-1 rounded hover:bg-red-500/20 text-xs font-semibold underline"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Primary Layout: Split Sidebar & GIS Map */}
        <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-4 min-h-[620px]">
          {/* Left Console Panel (4 cols on lg, 5 cols on xl) */}
          <div className="lg:col-span-5 xl:col-span-4 flex flex-col gap-3 min-h-[500px]">
            {/* Panel Tabs Navigation */}
            <div className="flex items-center p-1 rounded-xl bg-slate-900 border border-slate-800 text-xs font-medium">
              <button
                onClick={() => setActiveTab("planner")}
                className={`flex-1 py-2 px-2.5 rounded-lg flex items-center justify-center gap-1.5 transition-all ${
                  activeTab === "planner"
                    ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
                }`}
              >
                <span>⚡</span>
                <span className="truncate">Plan Route</span>
              </button>

              <button
                onClick={() => setActiveTab("metrics")}
                className={`flex-1 py-2 px-2.5 rounded-lg flex items-center justify-center gap-1.5 transition-all ${
                  activeTab === "metrics"
                    ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
                }`}
              >
                <span>📊</span>
                <span className="truncate">Metrics</span>
                {comparisonRoutes && comparisonRoutes.length > 0 && (
                  <span className="h-1.5 w-1.5 rounded-full bg-cyan-400" />
                )}
              </button>

              <button
                onClick={() => setActiveTab("inspector")}
                className={`flex-1 py-2 px-2.5 rounded-lg flex items-center justify-center gap-1.5 transition-all ${
                  activeTab === "inspector"
                    ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
                }`}
              >
                <span>🔍</span>
                <span className="truncate">Explain</span>
              </button>

              <button
                onClick={() => setActiveTab("dispatch")}
                className={`flex-1 py-2 px-2.5 rounded-lg flex items-center justify-center gap-1.5 transition-all ${
                  activeTab === "dispatch"
                    ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
                }`}
              >
                <span>🚚</span>
                <span className="truncate">Dispatch</span>
                {activeOptimization && (
                  <span className="h-1.5 w-1.5 rounded-full bg-cyan-400" />
                )}
              </button>

              <button
                onClick={() => setActiveTab("assets")}
                className={`flex-1 py-2 px-2.5 rounded-lg flex items-center justify-center gap-1.5 transition-all ${
                  activeTab === "assets"
                    ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
                }`}
              >
                <span>🏢</span>
                <span className="truncate">Assets</span>
              </button>
            </div>

            {/* Tab Body View Container */}
            <div className="flex-1 overflow-y-auto max-h-[750px] pr-1 space-y-4">
              {/* Tab 1: Route Planner */}
              {activeTab === "planner" && (
                <div className="space-y-4">
                  <RoutePlannerSidebar
                    onCalculateRoute={handleCalculate}
                    onCompareRoutes={handleCompare}
                    loading={loadingRoute || loadingCompare}
                    error={error}
                    selectedProfile={selectedProfile}
                    onProfileChange={setSelectedProfile}
                    originLat={originLat}
                    setOriginLat={setOriginLat}
                    originLon={originLon}
                    setOriginLon={setOriginLon}
                    destLat={destLat}
                    setDestLat={setDestLat}
                    destLon={destLon}
                    setDestLon={setDestLon}
                  />

                  {/* Corridors Quick Picker */}
                  <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/60 shadow-sm space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold uppercase tracking-wider text-slate-300">
                        NER Strategic Corridors ({corridors.length})
                      </span>
                      <span className="text-[10px] text-amber-400">Click to view</span>
                    </div>

                    <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
                      {corridors.map((corr) => (
                        <button
                          key={corr.id}
                          onClick={() => setSelectedCorridor(corr)}
                          className="w-full text-left p-2.5 rounded-lg bg-slate-950/60 border border-slate-800/80 hover:border-amber-500/40 hover:bg-slate-900/80 transition-all flex items-center justify-between text-xs"
                        >
                          <div className="truncate mr-2">
                            <div className="font-semibold text-white truncate">{corr.name}</div>
                            <div className="text-[10px] text-slate-400 font-mono">
                              {corr.national_highway} · {corr.start_point} → {corr.end_point}
                            </div>
                          </div>
                          <span className="text-amber-400 font-mono text-[11px] shrink-0">
                            {corr.approximate_length_km} km
                          </span>
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Tab 2: Metrics & Comparison */}
              {activeTab === "metrics" && (
                <div className="space-y-4">
                  <RouteMetricsPanel
                    activeRoute={activeRoute}
                    comparisonRoutes={comparisonRoutes}
                    onSelectComparedRoute={(r) => {
                      setActiveRoute(r);
                      setActiveProfile(r.profile.toLowerCase());
                    }}
                  />
                  {!activeRoute && (!comparisonRoutes || comparisonRoutes.length === 0) && (
                    <div className="p-8 rounded-xl border border-slate-800 bg-slate-900/40 text-center space-y-3">
                      <span className="text-3xl">📊</span>
                      <p className="text-sm font-semibold text-white">No Route Calculated Yet</p>
                      <p className="text-xs text-slate-400 max-w-xs mx-auto">
                        Head to the Route Planner tab and trigger a single route or multi-profile comparison to view metrics.
                      </p>
                      <button
                        onClick={() => setActiveTab("planner")}
                        className="px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-xs font-medium text-white transition-colors"
                      >
                        Open Route Planner
                      </button>
                    </div>
                  )}
                </div>
              )}

              {/* Tab 3: Segment Explainability Inspector */}
              {activeTab === "inspector" && (
                <div className="space-y-4">
                  {activeRoute ? (
                    <RouteSegmentInspector
                      edges={activeRoute.edges}
                      selectedEdgeIndex={selectedSegmentIndex}
                      onSelectEdge={setSelectedSegmentIndex}
                    />
                  ) : (
                    <div className="p-8 rounded-xl border border-slate-800 bg-slate-900/40 text-center space-y-3">
                      <span className="text-3xl">🔍</span>
                      <p className="text-sm font-semibold text-white">No Active Route Selected</p>
                      <p className="text-xs text-slate-400 max-w-xs mx-auto">
                        Calculate a route to inspect segment-by-segment cost and modeled risk explainability.
                      </p>
                      <button
                        onClick={() => setActiveTab("planner")}
                        className="px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-xs font-medium text-white transition-colors"
                      >
                        Plan a Route
                      </button>
                    </div>
                  )}
                </div>
              )}

              {/* Tab 4: Tenant Assets & Management */}
              {activeTab === "assets" && (
                <div className="space-y-4">
                  {/* Fleet Summary Card */}
                  <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/60 space-y-2.5">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span>🚚</span>
                        <span className="text-xs font-bold uppercase tracking-wider text-white">
                          Fleet Vehicles ({vehicles.length})
                        </span>
                      </div>
                      <Link href="/vehicles" className="text-[11px] text-indigo-400 hover:underline">
                        Manage →
                      </Link>
                    </div>
                    <div className="space-y-1.5 max-h-40 overflow-y-auto pr-1">
                      {vehicles.slice(0, 5).map((v) => (
                        <div
                          key={v.id}
                          className="flex items-center justify-between p-2 rounded-lg bg-slate-950/50 border border-slate-800/80 text-xs"
                        >
                          <div>
                            <span className="font-semibold text-white font-mono">{v.registration_number}</span>
                            <span className="text-slate-400 ml-2">({v.vehicle_type})</span>
                          </div>
                          <span
                            className={`px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase ${
                              v.status === "available"
                                ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                                : "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                            }`}
                          >
                            {v.status}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Hubs Summary Card */}
                  <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/60 space-y-2.5">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span>📍</span>
                        <span className="text-xs font-bold uppercase tracking-wider text-white">
                          Logistics Facilities ({locations.length})
                        </span>
                      </div>
                      <Link href="/locations" className="text-[11px] text-emerald-400 hover:underline">
                        Manage →
                      </Link>
                    </div>
                    <div className="space-y-1.5 max-h-40 overflow-y-auto pr-1">
                      {locations.slice(0, 5).map((l) => (
                        <div
                          key={l.id}
                          className="flex items-center justify-between p-2 rounded-lg bg-slate-950/50 border border-slate-800/80 text-xs"
                        >
                          <div className="truncate mr-2">
                            <div className="font-semibold text-white truncate">{l.name}</div>
                            <div className="text-[10px] text-slate-400 font-mono">
                              {l.city}, {l.state}
                            </div>
                          </div>
                          <span className="text-slate-400 text-[10px] font-mono shrink-0">
                            {l.latitude.toFixed(2)}, {l.longitude.toFixed(2)}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Consignments Summary Card */}
                  <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/60 space-y-2.5">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span>📦</span>
                        <span className="text-xs font-bold uppercase tracking-wider text-white">
                          Consignments ({deliveries.length})
                        </span>
                      </div>
                      <Link href="/deliveries" className="text-[11px] text-amber-400 hover:underline">
                        Manage →
                      </Link>
                    </div>
                    <div className="space-y-1.5 max-h-40 overflow-y-auto pr-1">
                      {deliveries.slice(0, 5).map((d) => (
                        <div
                          key={d.id}
                          className="flex items-center justify-between p-2 rounded-lg bg-slate-950/50 border border-slate-800/80 text-xs"
                        >
                          <div>
                            <div className="font-semibold text-white font-mono">{d.reference_number}</div>
                            <div className="text-[10px] text-slate-400">
                              {d.package_weight} kg · Priority: {d.priority}
                            </div>
                          </div>
                          <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase bg-slate-800 text-slate-300">
                            {d.status}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Tab 5: Fleet Dispatch & VRP Optimization */}
              {activeTab === "dispatch" && (
                <div className="space-y-4">
                  {selectedTelemetryVehicle && (
                    <VehicleTelemetryDrawer
                      vehicle={selectedTelemetryVehicle}
                      activeRoute={
                        activeOptimization?.routes.find(
                          (r) => r.vehicle_id === selectedTelemetryVehicle.vehicle_id
                        ) || null
                      }
                      onClose={() => setSelectedTelemetryVehicle(null)}
                    />
                  )}

                  <DispatchPanel
                    vehicles={vehicles}
                    locations={locations}
                    deliveries={deliveries}
                    loading={loadingDispatch}
                    setLoading={setLoadingDispatch}
                    onOptimizationComplete={(optResult) => {
                      setActiveOptimization(optResult);
                      setLayers((prev) => ({ ...prev, fleetRoutes: true }));
                    }}
                  />

                  {activeOptimization && (
                    <OptimizationResultCard
                      result={activeOptimization}
                      selectedRouteVehicleId={selectedRouteVehicleId}
                      onSelectRoute={(route) => {
                        setSelectedRouteVehicleId(route.vehicle_id);
                        const matchVeh = fleetTelemetry.find((v) => v.vehicle_id === route.vehicle_id);
                        if (matchVeh) setSelectedTelemetryVehicle(matchVeh);
                      }}
                    />
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Right GIS Leaflet Map Area (8 cols on lg, 8 cols on xl) */}
          <div className="lg:col-span-7 xl:col-span-8 flex flex-col min-h-[550px] relative">
            <MapWrapper
              layers={layers}
              onToggleLayer={toggleLayer}
              roadEdges={roadEdges}
              corridors={corridors}
              onSelectCorridor={setSelectedCorridor}
              activeRoute={activeRoute}
              comparisonRoutes={comparisonRoutes}
              activeProfile={activeProfile}
              selectedSegmentIndex={selectedSegmentIndex}
              onSelectSegment={setSelectedSegmentIndex}
              vehicles={vehicles}
              locations={locations}
              deliveries={deliveries}
              fleetRoutes={activeOptimization?.routes || []}
              fleetTelemetry={fleetTelemetry}
              roadRestrictions={roadRestrictions}
              onSelectVehicle={(veh) => {
                setSelectedTelemetryVehicle(veh);
                setSelectedRouteVehicleId(veh.vehicle_id);
                setActiveTab("dispatch");
              }}
              selectedVehicleId={selectedRouteVehicleId}
              showLegend={showLegend}
              onToggleLegend={() => setShowLegend(!showLegend)}
            />
          </div>
        </div>

        {/* Corridor Detailed Waypoint Modal */}
        {selectedCorridor && (
          <CorridorInfoModal
            corridor={selectedCorridor}
            onClose={() => setSelectedCorridor(null)}
            onSelectAsRouteEndpoints={(sLat, sLon, eLat, eLon) => {
              setOriginLat(sLat.toString());
              setOriginLon(sLon.toString());
              setDestLat(eLat.toString());
              setDestLon(eLon.toString());
              setSelectedCorridor(null);
              setActiveTab("planner");
            }}
          />
        )}
      </main>
    </div>
  );
}
