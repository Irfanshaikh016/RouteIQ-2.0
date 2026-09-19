"use client";

import React, { useState } from "react";
import {
  Vehicle,
  Location,
  Delivery,
  OptimizationRequestPayload,
  OptimizationResult,
  ReoptimizationTriggerPayload,
  ReoptimizationResult,
  optimizeCVRP,
  optimizeVRPTW,
  triggerReoptimization,
} from "@/lib/api";

interface DispatchPanelProps {
  vehicles: Vehicle[];
  locations: Location[];
  deliveries: Delivery[];
  onOptimizationComplete: (result: OptimizationResult) => void;
  loading: boolean;
  setLoading: (loading: boolean) => void;
}

export default function DispatchPanel({
  vehicles,
  locations,
  deliveries,
  onOptimizationComplete,
  loading,
  setLoading,
}: DispatchPanelProps) {
  // Config state
  const [selectedDepotId, setSelectedDepotId] = useState<string>(
    locations.length > 0 ? locations[0].id : ""
  );
  const [problemType, setProblemType] = useState<"CVRP" | "VRPTW">("CVRP");
  const [selectedProfile, setSelectedProfile] = useState<string>("balanced");

  // Selection states
  const [selectedVehicleIds, setSelectedVehicleIds] = useState<Set<string>>(
    new Set(vehicles.map((v) => v.id))
  );
  const [selectedDeliveryIds, setSelectedDeliveryIds] = useState<Set<string>>(
    new Set(deliveries.map((d) => d.id))
  );

  // Status & Error
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const toggleVehicle = (id: string) => {
    setSelectedVehicleIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const toggleDelivery = (id: string) => {
    setSelectedDeliveryIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const handleSelectAllVehicles = () => {
    if (selectedVehicleIds.size === vehicles.length) {
      setSelectedVehicleIds(new Set());
    } else {
      setSelectedVehicleIds(new Set(vehicles.map((v) => v.id)));
    }
  };

  const handleSelectAllDeliveries = () => {
    if (selectedDeliveryIds.size === deliveries.length) {
      setSelectedDeliveryIds(new Set());
    } else {
      setSelectedDeliveryIds(new Set(deliveries.map((d) => d.id)));
    }
  };

  // Run OR-Tools Optimization
  const handleRunOptimization = async () => {
    setLoading(true);
    setErrorMessage(null);
    setStatusMessage(null);

    const chosenDepot = locations.find((l) => l.id === selectedDepotId);
    const depotLat = chosenDepot?.latitude || 26.1158;
    const depotLon = chosenDepot?.longitude || 91.821;

    const chosenVehicles = vehicles
      .filter((v) => selectedVehicleIds.has(v.id))
      .map((v) => ({
        vehicle_id: v.id,
        vehicle_name: v.vehicle_name,
        capacity: v.capacity,
      }));

    if (chosenVehicles.length === 0) {
      setErrorMessage("Please select at least 1 vehicle for optimization.");
      setLoading(false);
      return;
    }

    const chosenDeliveries = deliveries
      .filter((d) => selectedDeliveryIds.has(d.id))
      .map((d) => {
        const destLoc = locations.find((l) => l.id === d.delivery_location_id);
        return {
          delivery_id: d.id,
          location_id: d.delivery_location_id,
          latitude: destLoc?.latitude || 25.5788,
          longitude: destLoc?.longitude || 91.8933,
          demand: d.package_weight || 50.0,
          service_duration_minutes: 15,
          time_window_start_minutes: 0,
          time_window_end_minutes: 480,
        };
      });

    if (chosenDeliveries.length === 0) {
      setErrorMessage("Please select at least 1 delivery order for optimization.");
      setLoading(false);
      return;
    }

    const payload: OptimizationRequestPayload = {
      depot_location_id: selectedDepotId || undefined,
      depot_lat: depotLat,
      depot_lon: depotLon,
      problem_type: problemType,
      profile: selectedProfile,
      vehicles: chosenVehicles,
      deliveries: chosenDeliveries,
    };

    try {
      const result =
        problemType === "VRPTW"
          ? await optimizeVRPTW(payload)
          : await optimizeCVRP(payload);

      setStatusMessage(
        `Optimization completed: ${result.vehicles_used} vehicles assigned to ${result.served_deliveries_count} deliveries.`
      );
      onOptimizationComplete(result);
    } catch (err: any) {
      setErrorMessage(err.message || "Optimization failed. Please check capacity and constraints.");
    } finally {
      setLoading(false);
    }
  };

  // Disruption Simulation Triggers
  const handleSimulateDisruption = async (type: "VEHICLE_BREAKDOWN" | "ROAD_CLOSURE" | "DELIVERY_CANCELLATION") => {
    setLoading(true);
    setErrorMessage(null);
    setStatusMessage(null);

    let payload: ReoptimizationTriggerPayload;

    if (type === "VEHICLE_BREAKDOWN") {
      const targetVehicle = vehicles.find((v) => selectedVehicleIds.has(v.id)) || vehicles[0];
      if (!targetVehicle) {
        setErrorMessage("No vehicle available to trigger breakdown.");
        setLoading(false);
        return;
      }
      payload = {
        trigger_type: "VEHICLE_BREAKDOWN",
        affected_vehicle_id: targetVehicle.id,
        reason: `Breakdown reported for ${targetVehicle.vehicle_name}: Engine overheat on corridor`,
        profile: selectedProfile,
        depot_location_id: selectedDepotId,
      };
    } else if (type === "ROAD_CLOSURE") {
      payload = {
        trigger_type: "ROAD_CLOSURE",
        affected_road_edge_id: "CORR-01-E1",
        reason: "Landslide blockage reported by State Disaster Management",
        profile: selectedProfile,
        depot_location_id: selectedDepotId,
      };
    } else {
      const targetDeliv = deliveries.find((d) => selectedDeliveryIds.has(d.id)) || deliveries[0];
      if (!targetDeliv) {
        setErrorMessage("No delivery available to cancel.");
        setLoading(false);
        return;
      }
      payload = {
        trigger_type: "DELIVERY_CANCELLATION",
        affected_delivery_id: targetDeliv.id,
        reason: `Consignee cancelled order ${targetDeliv.reference_number}`,
        profile: selectedProfile,
        depot_location_id: selectedDepotId,
      };
    }

    try {
      const res = await triggerReoptimization(payload);
      if (res.reoptimization_performed && res.updated_optimization) {
        setStatusMessage(res.message);
        onOptimizationComplete(res.updated_optimization);
      } else {
        setStatusMessage(res.message);
      }
    } catch (err: any) {
      setErrorMessage(err.message || "Disruption re-optimization failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Messages */}
      {statusMessage && (
        <div className="p-3 rounded-lg bg-emerald-950/40 border border-emerald-500/40 text-xs text-emerald-300 flex items-center justify-between">
          <span>✓ {statusMessage}</span>
          <button onClick={() => setStatusMessage(null)} className="text-emerald-400 hover:text-white">✕</button>
        </div>
      )}
      {errorMessage && (
        <div className="p-3 rounded-lg bg-rose-950/40 border border-rose-500/40 text-xs text-rose-300 flex items-center justify-between">
          <span>⚠️ {errorMessage}</span>
          <button onClick={() => setErrorMessage(null)} className="text-rose-400 hover:text-white">✕</button>
        </div>
      )}

      {/* Problem Configuration Card */}
      <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/60 shadow-sm space-y-3">
        <div className="text-xs font-bold uppercase tracking-wider text-slate-300">
          Optimization Parameters
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
          <div>
            <label className="text-[11px] text-slate-400 font-medium block mb-1">
              Central Depot Hub
            </label>
            <select
              value={selectedDepotId}
              onChange={(e) => setSelectedDepotId(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-slate-200 focus:border-indigo-500 focus:outline-none"
            >
              {locations.length > 0 ? (
                locations.map((l) => (
                  <option key={l.id} value={l.id}>
                    {l.name} ({l.city})
                  </option>
                ))
              ) : (
                <option value="">Guwahati Hub (Default: 26.1158, 91.8210)</option>
              )}
            </select>
          </div>

          <div>
            <label className="text-[11px] text-slate-400 font-medium block mb-1">
              Problem Constraints
            </label>
            <div className="grid grid-cols-2 gap-1.5 bg-slate-950 p-1 rounded-lg border border-slate-800">
              <button
                onClick={() => setProblemType("CVRP")}
                className={`py-1 rounded font-medium transition-all ${
                  problemType === "CVRP"
                    ? "bg-indigo-600 text-white"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                CVRP (Payload)
              </button>
              <button
                onClick={() => setProblemType("VRPTW")}
                className={`py-1 rounded font-medium transition-all ${
                  problemType === "VRPTW"
                    ? "bg-indigo-600 text-white"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                VRP-TW (Windows)
              </button>
            </div>
          </div>
        </div>

        {/* Profile Picker */}
        <div>
          <label className="text-[11px] text-slate-400 font-medium block mb-1">
            Cost Model Profile
          </label>
          <div className="grid grid-cols-3 gap-2 text-xs">
            {[
              { id: "fastest", label: "⚡ Fastest", color: "border-cyan-500/50 text-cyan-300" },
              { id: "balanced", label: "⚖️ Balanced", color: "border-purple-500/50 text-purple-300" },
              { id: "safest", label: "🛡️ Safest", color: "border-emerald-500/50 text-emerald-300" },
            ].map((p) => (
              <button
                key={p.id}
                onClick={() => setSelectedProfile(p.id)}
                className={`py-2 px-2.5 rounded-lg border font-medium transition-all ${
                  selectedProfile === p.id
                    ? `${p.color} bg-slate-800/90 shadow-sm`
                    : "border-slate-800 bg-slate-950 text-slate-400 hover:text-slate-200"
                }`}
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Fleet Vehicles Multi-Select */}
      <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/60 shadow-sm space-y-2.5">
        <div className="flex items-center justify-between">
          <div className="text-xs font-bold uppercase tracking-wider text-slate-300">
            Available Fleet Vehicles ({selectedVehicleIds.size}/{vehicles.length})
          </div>
          <button
            onClick={handleSelectAllVehicles}
            className="text-[11px] text-indigo-400 hover:text-indigo-300"
          >
            {selectedVehicleIds.size === vehicles.length ? "Deselect All" : "Select All"}
          </button>
        </div>

        <div className="space-y-1.5 max-h-36 overflow-y-auto pr-1">
          {vehicles.map((veh) => {
            const isChecked = selectedVehicleIds.has(veh.id);
            return (
              <label
                key={veh.id}
                className={`flex items-center justify-between p-2 rounded-lg border text-xs cursor-pointer transition-all ${
                  isChecked
                    ? "border-indigo-500/40 bg-indigo-950/20 text-slate-200"
                    : "border-slate-800 bg-slate-950/40 text-slate-400"
                }`}
              >
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={isChecked}
                    onChange={() => toggleVehicle(veh.id)}
                    className="rounded border-slate-700 bg-slate-900 text-indigo-600 focus:ring-0"
                  />
                  <span className="font-medium text-white">{veh.vehicle_name}</span>
                  <span className="text-[10px] font-mono text-slate-400">
                    {veh.registration_number}
                  </span>
                </div>
                <div className="text-[11px] text-indigo-400 font-mono">
                  {veh.capacity} kg
                </div>
              </label>
            );
          })}
        </div>
      </div>

      {/* Delivery Consignments Multi-Select */}
      <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/60 shadow-sm space-y-2.5">
        <div className="flex items-center justify-between">
          <div className="text-xs font-bold uppercase tracking-wider text-slate-300">
            Pending Orders ({selectedDeliveryIds.size}/{deliveries.length})
          </div>
          <button
            onClick={handleSelectAllDeliveries}
            className="text-[11px] text-indigo-400 hover:text-indigo-300"
          >
            {selectedDeliveryIds.size === deliveries.length ? "Deselect All" : "Select All"}
          </button>
        </div>

        <div className="space-y-1.5 max-h-36 overflow-y-auto pr-1">
          {deliveries.map((deliv) => {
            const isChecked = selectedDeliveryIds.has(deliv.id);
            return (
              <label
                key={deliv.id}
                className={`flex items-center justify-between p-2 rounded-lg border text-xs cursor-pointer transition-all ${
                  isChecked
                    ? "border-rose-500/40 bg-rose-950/20 text-slate-200"
                    : "border-slate-800 bg-slate-950/40 text-slate-400"
                }`}
              >
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={isChecked}
                    onChange={() => toggleDelivery(deliv.id)}
                    className="rounded border-slate-700 bg-slate-900 text-indigo-600 focus:ring-0"
                  />
                  <span className="font-medium text-white">{deliv.reference_number}</span>
                  <span className="text-[10px] text-slate-400 capitalize">
                    {deliv.priority}
                  </span>
                </div>
                <div className="text-[11px] text-rose-400 font-mono">
                  {deliv.package_weight} kg
                </div>
              </label>
            );
          })}
        </div>
      </div>

      {/* Main Action Button */}
      <button
        onClick={handleRunOptimization}
        disabled={loading}
        className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-indigo-600 to-cyan-600 hover:from-indigo-500 hover:to-cyan-500 text-white font-bold text-sm shadow-lg shadow-indigo-600/30 transition-all disabled:opacity-50 flex items-center justify-center gap-2"
      >
        {loading ? (
          <>
            <span className="h-4 w-4 rounded-full border-2 border-white border-t-transparent animate-spin" />
            <span>Solving OR-Tools Combinatorics...</span>
          </>
        ) : (
          <>
            <span>🚀</span>
            <span>Run {problemType} Fleet Optimization</span>
          </>
        )}
      </button>

      {/* Disruption Simulation & Dynamic Re-Optimization Bar */}
      <div className="p-3.5 rounded-xl border border-slate-800 bg-slate-900/40 space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
            Controlled Disruption Triggers
          </span>
          <span className="text-[10px] text-slate-500 font-mono">Debounced (10s)</span>
        </div>

        <div className="grid grid-cols-3 gap-1.5 text-xs">
          <button
            onClick={() => handleSimulateDisruption("VEHICLE_BREAKDOWN")}
            disabled={loading}
            className="p-2 rounded-lg bg-rose-950/30 hover:bg-rose-900/50 border border-rose-800/40 text-rose-300 font-medium transition-all text-center flex flex-col items-center gap-0.5 disabled:opacity-50"
          >
            <span>💥 Breakdown</span>
            <span className="text-[9px] text-rose-400/80">Re-route Fleet</span>
          </button>

          <button
            onClick={() => handleSimulateDisruption("ROAD_CLOSURE")}
            disabled={loading}
            className="p-2 rounded-lg bg-amber-950/30 hover:bg-amber-900/50 border border-amber-800/40 text-amber-300 font-medium transition-all text-center flex flex-col items-center gap-0.5 disabled:opacity-50"
          >
            <span>🚧 Road Closed</span>
            <span className="text-[9px] text-amber-400/80">Corridor Bypass</span>
          </button>

          <button
            onClick={() => handleSimulateDisruption("DELIVERY_CANCELLATION")}
            disabled={loading}
            className="p-2 rounded-lg bg-blue-950/30 hover:bg-blue-900/50 border border-blue-800/40 text-blue-300 font-medium transition-all text-center flex flex-col items-center gap-0.5 disabled:opacity-50"
          >
            <span>❌ Cancel Order</span>
            <span className="text-[9px] text-blue-400/80">Re-sequence</span>
          </button>
        </div>
      </div>
    </div>
  );
}
