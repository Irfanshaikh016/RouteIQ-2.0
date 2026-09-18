"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import Header from "@/components/Header";
import {
  getStoredUser,
  listVehicles,
  listLocations,
  listDeliveries,
  TokenResponse,
  Vehicle,
  Location,
  Delivery,
} from "@/lib/api";

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<TokenResponse | null>(null);
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [locations, setLocations] = useState<Location[]>([]);
  const [deliveries, setDeliveries] = useState<Delivery[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const currentUser = getStoredUser();
    if (!currentUser) {
      router.push("/login");
      return;
    }
    setUser(currentUser);

    const loadData = async () => {
      setLoading(true);
      try {
        const [vList, lList, dList] = await Promise.all([
          listVehicles(),
          listLocations(),
          listDeliveries(),
        ]);
        setVehicles(vList);
        setLocations(lList);
        setDeliveries(dList);
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : "Failed to load dashboard data";
        setError(msg);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [router]);

  if (!user) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center">
        <p className="text-sm text-slate-400">Verifying session...</p>
      </div>
    );
  }

  const activeVehicles = vehicles.filter((v) => v.status === "available").length;
  const pendingDeliveries = deliveries.filter((d) => d.status === "pending" || d.status === "assigned").length;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <Header />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Organization & User Welcome Banner */}
        <div className="rounded-2xl border border-indigo-900/40 bg-gradient-to-r from-slate-900 via-indigo-950/30 to-slate-900 p-6 sm:p-8 shadow-xl">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full text-xs font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 mb-2">
                <span>🛡️</span> Multi-Tenant Session Active
              </div>
              <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
                Logistics Operations Center
              </h1>
              <p className="text-xs sm:text-sm text-slate-300 mt-1">
                Signed in as <span className="text-white font-medium">{user.full_name}</span> ({user.email}) ·{" "}
                <span className="text-cyan-400 font-semibold uppercase">{user.role}</span>
              </p>
              <p className="text-xs text-slate-400 mt-0.5">
                Organization Tenant ID: <code className="text-slate-300 font-mono text-[11px]">{user.organization_id}</code>
              </p>
            </div>

            <div className="flex items-center gap-3">
              <Link
                href="/deliveries"
                className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-xs font-medium text-white shadow-lg shadow-indigo-500/20 transition-all text-center"
              >
                + New Delivery
              </Link>
            </div>
          </div>
        </div>

        {error && (
          <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-xs flex items-center justify-between">
            <span>⚠️ {error}</span>
            <button
              onClick={() => setError(null)}
              className="text-xs underline hover:text-white"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Phase 2 Metrics Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
          {/* Vehicles Card */}
          <Link
            href="/vehicles"
            className="group block p-6 rounded-xl border border-slate-800 bg-slate-900/60 hover:border-indigo-500/40 hover:bg-slate-900 transition-all shadow-md"
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-400">Total Fleet Vehicles</span>
              <span className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400 text-lg">🚚</span>
            </div>
            <div className="mt-4 flex items-baseline gap-2">
              <span className="text-3xl font-bold text-white tracking-tight">
                {loading ? "..." : vehicles.length}
              </span>
              <span className="text-xs text-emerald-400">
                ({activeVehicles} available)
              </span>
            </div>
            <p className="mt-2 text-xs text-slate-400 group-hover:text-indigo-300 transition-colors">
              Manage vehicle assets &amp; capacities →
            </p>
          </Link>

          {/* Locations Card */}
          <Link
            href="/locations"
            className="group block p-6 rounded-xl border border-slate-800 bg-slate-900/60 hover:border-indigo-500/40 hover:bg-slate-900 transition-all shadow-md"
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-400">Logistics Hubs &amp; Depots</span>
              <span className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400 text-lg">📍</span>
            </div>
            <div className="mt-4 flex items-baseline gap-2">
              <span className="text-3xl font-bold text-white tracking-tight">
                {loading ? "..." : locations.length}
              </span>
              <span className="text-xs text-slate-400">active facilities</span>
            </div>
            <p className="mt-2 text-xs text-slate-400 group-hover:text-emerald-300 transition-colors">
              Manage facility coordinate stops →
            </p>
          </Link>

          {/* Deliveries Card */}
          <Link
            href="/deliveries"
            className="group block p-6 rounded-xl border border-slate-800 bg-slate-900/60 hover:border-indigo-500/40 hover:bg-slate-900 transition-all shadow-md"
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-slate-400">Shipment Deliveries</span>
              <span className="p-2 rounded-lg bg-amber-500/10 text-amber-400 text-lg">📦</span>
            </div>
            <div className="mt-4 flex items-baseline gap-2">
              <span className="text-3xl font-bold text-white tracking-tight">
                {loading ? "..." : deliveries.length}
              </span>
              <span className="text-xs text-amber-400">
                ({pendingDeliveries} active/pending)
              </span>
            </div>
            <p className="mt-2 text-xs text-slate-400 group-hover:text-amber-300 transition-colors">
              Inspect delivery orders &amp; time windows →
            </p>
          </Link>
        </div>

        {/* Quick Access Action Hub */}
        <div className="p-6 rounded-xl border border-slate-800 bg-slate-900/40">
          <h2 className="text-sm font-semibold text-white uppercase tracking-wider mb-4">
            Phase 2 Core Logistics Architecture
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs text-slate-300">
            <div className="p-4 rounded-lg bg-slate-950/70 border border-slate-800/80">
              <p className="font-semibold text-white mb-1">Strict Organization Isolation</p>
              <p className="text-slate-400 leading-relaxed">
                All vehicles, locations, and delivery consignments are cryptographically bound to your organization ID. Cross-tenant access is rejected with HTTP 404/403.
              </p>
            </div>
            <div className="p-4 rounded-lg bg-slate-950/70 border border-slate-800/80">
              <p className="font-semibold text-white mb-1">Geographic Bounds &amp; Time Windows</p>
              <p className="text-slate-400 leading-relaxed">
                Coordinates strictly adhere to ISO degrees (-90 to 90 lat, -180 to 180 lon). Deliveries enforce non-negative metric payloads and chronological time windows.
              </p>
            </div>
            <div className="p-4 rounded-lg bg-slate-950/70 border border-slate-800/80">
              <p className="font-semibold text-white mb-1">Ready for Phase 3 Ingestion</p>
              <p className="text-slate-400 leading-relaxed">
                Locations and fleets are structured to be ingested directly by Phase 3 PostGIS road graph and hazard intelligence models without breaking changes.
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
