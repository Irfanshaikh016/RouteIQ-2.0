"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Header from "@/components/Header";
import {
  listVehicles,
  createVehicle,
  updateVehicle,
  deleteVehicle,
  getStoredUser,
  Vehicle,
  VehicleStatus,
} from "@/lib/api";

export default function VehiclesPage() {
  const router = useRouter();
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Form modal states
  const [showModal, setShowModal] = useState(false);
  const [editingVehicle, setEditingVehicle] = useState<Vehicle | null>(null);
  const [formData, setFormData] = useState({
    vehicle_name: "",
    vehicle_type: "Heavy Commercial Truck",
    registration_number: "",
    capacity: 10000,
    capacity_unit: "kg",
    status: "available" as VehicleStatus,
  });
  const [submitting, setSubmitting] = useState(false);

  const fetchVehicles = async () => {
    setLoading(true);
    try {
      const data = await listVehicles();
      setVehicles(data);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load vehicles";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const user = getStoredUser();
    if (!user) {
      router.push("/login");
      return;
    }
    fetchVehicles();
  }, [router]);

  const handleOpenCreate = () => {
    setEditingVehicle(null);
    setFormData({
      vehicle_name: "",
      vehicle_type: "Heavy Commercial Truck",
      registration_number: "",
      capacity: 10000,
      capacity_unit: "kg",
      status: "available",
    });
    setError(null);
    setShowModal(true);
  };

  const handleOpenEdit = (v: Vehicle) => {
    setEditingVehicle(v);
    setFormData({
      vehicle_name: v.vehicle_name,
      vehicle_type: v.vehicle_type,
      registration_number: v.registration_number,
      capacity: v.capacity,
      capacity_unit: v.capacity_unit,
      status: v.status,
    });
    setError(null);
    setShowModal(true);
  };

  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`Are you sure you want to delete vehicle "${name}"?`)) return;
    try {
      await deleteVehicle(id);
      setSuccessMsg(`Vehicle "${name}" deleted.`);
      fetchVehicles();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Delete failed";
      setError(msg);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    if (formData.capacity < 0) {
      setError("Capacity cannot be negative.");
      setSubmitting(false);
      return;
    }

    try {
      if (editingVehicle) {
        await updateVehicle(editingVehicle.id, formData);
        setSuccessMsg(`Vehicle "${formData.vehicle_name}" updated.`);
      } else {
        await createVehicle(formData);
        setSuccessMsg(`Vehicle "${formData.vehicle_name}" registered.`);
      }
      setShowModal(false);
      fetchVehicles();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to save vehicle";
      setError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  const getStatusBadge = (status: VehicleStatus) => {
    switch (status) {
      case "available":
        return <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">Available</span>;
      case "assigned":
        return <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">Assigned</span>;
      case "maintenance":
        return <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">Maintenance</span>;
      case "inactive":
        return <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">Inactive</span>;
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <Header />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        {/* Page Heading */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-extrabold text-white tracking-tight">
              Fleet Vehicle Management
            </h1>
            <p className="text-xs text-slate-400 mt-1">
              Manage organization fleet units, payload capacities, and operational status
            </p>
          </div>
          <button
            onClick={handleOpenCreate}
            className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold text-white shadow-lg shadow-indigo-500/25 transition-all self-start sm:self-auto"
          >
            + Add Vehicle
          </button>
        </div>

        {/* Feedback alerts */}
        {error && (
          <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-xs flex items-center justify-between">
            <span>⚠️ {error}</span>
            <button onClick={() => setError(null)} className="underline hover:text-white">Dismiss</button>
          </div>
        )}
        {successMsg && (
          <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs flex items-center justify-between">
            <span>✓ {successMsg}</span>
            <button onClick={() => setSuccessMsg(null)} className="underline hover:text-white">Dismiss</button>
          </div>
        )}

        {/* Table container */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
          {loading ? (
            <div className="p-12 text-center text-xs text-slate-400">
              <span className="inline-block w-5 h-5 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mb-2" />
              <p>Loading fleet inventory...</p>
            </div>
          ) : vehicles.length === 0 ? (
            <div className="p-12 text-center text-slate-400 space-y-3">
              <span className="text-4xl block">🚚</span>
              <p className="text-sm font-semibold text-slate-200">No vehicles registered yet</p>
              <p className="text-xs max-w-sm mx-auto">
                Add your organization&apos;s commercial trucks, hill haulers, and vans to begin managing fleet operations.
              </p>
              <button
                onClick={handleOpenCreate}
                className="mt-2 px-3 py-1.5 rounded-lg bg-indigo-600 text-xs font-medium text-white hover:bg-indigo-500 transition-colors"
              >
                Register First Vehicle
              </button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-950/80 border-b border-slate-800 text-slate-400 uppercase tracking-wider text-[11px]">
                  <tr>
                    <th className="py-3 px-4">Registration #</th>
                    <th className="py-3 px-4">Vehicle Name</th>
                    <th className="py-3 px-4">Type</th>
                    <th className="py-3 px-4">Payload Capacity</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-slate-300">
                  {vehicles.map((v) => (
                    <tr key={v.id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="py-3.5 px-4 font-mono font-medium text-indigo-400">
                        {v.registration_number}
                      </td>
                      <td className="py-3.5 px-4 font-medium text-white">
                        {v.vehicle_name}
                      </td>
                      <td className="py-3.5 px-4 text-slate-400">
                        {v.vehicle_type}
                      </td>
                      <td className="py-3.5 px-4">
                        {v.capacity.toLocaleString()} {v.capacity_unit}
                      </td>
                      <td className="py-3.5 px-4">
                        {getStatusBadge(v.status)}
                      </td>
                      <td className="py-3.5 px-4 text-right space-x-2">
                        <button
                          onClick={() => handleOpenEdit(v)}
                          className="text-slate-400 hover:text-indigo-400 font-medium transition-colors"
                        >
                          Edit
                        </button>
                        <span className="text-slate-700">·</span>
                        <button
                          onClick={() => handleDelete(v.id, v.vehicle_name)}
                          className="text-slate-400 hover:text-red-400 font-medium transition-colors"
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Modal: Add/Edit Vehicle */}
        {showModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md p-6 shadow-2xl space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <h3 className="text-sm font-bold text-white">
                  {editingVehicle ? "Edit Vehicle Asset" : "Register New Vehicle"}
                </h3>
                <button
                  onClick={() => setShowModal(false)}
                  className="text-slate-400 hover:text-white text-sm"
                >
                  ✕
                </button>
              </div>

              <form onSubmit={handleSubmit} className="space-y-3.5 text-xs">
                <div>
                  <label className="block text-slate-300 mb-1">Vehicle Name / Label</label>
                  <input
                    type="text"
                    required
                    value={formData.vehicle_name}
                    onChange={(e) => setFormData({ ...formData, vehicle_name: e.target.value })}
                    placeholder="e.g. Guwahati Express 16T"
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-white focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  />
                </div>

                <div>
                  <label className="block text-slate-300 mb-1">Registration / Plate Number</label>
                  <input
                    type="text"
                    required
                    value={formData.registration_number}
                    onChange={(e) => setFormData({ ...formData, registration_number: e.target.value })}
                    placeholder="e.g. AS-01-AB-1234"
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-white focus:outline-none focus:ring-1 focus:ring-indigo-500 uppercase"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-slate-300 mb-1">Vehicle Type</label>
                    <select
                      value={formData.vehicle_type}
                      onChange={(e) => setFormData({ ...formData, vehicle_type: e.target.value })}
                      className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-white focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    >
                      <option value="Heavy Commercial Truck">Heavy Truck (16T+)</option>
                      <option value="Medium Commercial Vehicle">Medium Truck (6-12T)</option>
                      <option value="Light Commercial Vehicle">Light Truck (LCV)</option>
                      <option value="4x4 Mountain Van">4x4 Mountain Van</option>
                      <option value="Tanker">Liquid / Fuel Tanker</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-slate-300 mb-1">Status</label>
                    <select
                      value={formData.status}
                      onChange={(e) => setFormData({ ...formData, status: e.target.value as VehicleStatus })}
                      className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-white focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    >
                      <option value="available">Available</option>
                      <option value="assigned">Assigned</option>
                      <option value="maintenance">Maintenance</option>
                      <option value="inactive">Inactive</option>
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-slate-300 mb-1">Capacity (Metric)</label>
                    <input
                      type="number"
                      required
                      min="0"
                      step="any"
                      value={formData.capacity}
                      onChange={(e) => setFormData({ ...formData, capacity: parseFloat(e.target.value) || 0 })}
                      className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-white focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    />
                  </div>
                  <div>
                    <label className="block text-slate-300 mb-1">Unit</label>
                    <select
                      value={formData.capacity_unit}
                      onChange={(e) => setFormData({ ...formData, capacity_unit: e.target.value })}
                      className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-white focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    >
                      <option value="kg">kg</option>
                      <option value="tonnes">tonnes</option>
                      <option value="m3">cubic meters (m³)</option>
                    </select>
                  </div>
                </div>

                <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-800">
                  <button
                    type="button"
                    onClick={() => setShowModal(false)}
                    className="px-3 py-1.5 rounded-lg border border-slate-700 text-slate-300 hover:text-white hover:bg-slate-800 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submitting}
                    className="px-4 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-medium transition-colors"
                  >
                    {submitting ? "Saving..." : editingVehicle ? "Save Changes" : "Create Vehicle"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
