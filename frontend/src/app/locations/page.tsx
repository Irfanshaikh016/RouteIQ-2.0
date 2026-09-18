"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Header from "@/components/Header";
import {
  listLocations,
  createLocation,
  updateLocation,
  deleteLocation,
  getStoredUser,
  Location,
} from "@/lib/api";

export default function LocationsPage() {
  const router = useRouter();
  const [locations, setLocations] = useState<Location[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Modal states
  const [showModal, setShowModal] = useState(false);
  const [editingLocation, setEditingLocation] = useState<Location | null>(null);
  const [formData, setFormData] = useState({
    name: "",
    address_line: "",
    city: "Guwahati",
    state: "Assam",
    postal_code: "",
    latitude: 26.1445,
    longitude: 91.7362,
  });
  const [submitting, setSubmitting] = useState(false);

  const fetchLocations = async () => {
    setLoading(true);
    try {
      const data = await listLocations();
      setLocations(data);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load locations";
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
    fetchLocations();
  }, [router]);

  const handleOpenCreate = () => {
    setEditingLocation(null);
    setFormData({
      name: "",
      address_line: "",
      city: "Guwahati",
      state: "Assam",
      postal_code: "",
      latitude: 26.1445,
      longitude: 91.7362,
    });
    setError(null);
    setShowModal(true);
  };

  const handleOpenEdit = (loc: Location) => {
    setEditingLocation(loc);
    setFormData({
      name: loc.name,
      address_line: loc.address_line || "",
      city: loc.city,
      state: loc.state,
      postal_code: loc.postal_code || "",
      latitude: loc.latitude,
      longitude: loc.longitude,
    });
    setError(null);
    setShowModal(true);
  };

  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`Are you sure you want to delete location "${name}"?`)) return;
    try {
      await deleteLocation(id);
      setSuccessMsg(`Location "${name}" deleted.`);
      fetchLocations();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Delete failed";
      setError(msg);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    // Validate coordinates
    if (formData.latitude < -90 || formData.latitude > 90) {
      setError("Latitude must be between -90.0 and +90.0 degrees.");
      setSubmitting(false);
      return;
    }
    if (formData.longitude < -180 || formData.longitude > 180) {
      setError("Longitude must be between -180.0 and +180.0 degrees.");
      setSubmitting(false);
      return;
    }

    try {
      if (editingLocation) {
        await updateLocation(editingLocation.id, formData);
        setSuccessMsg(`Location "${formData.name}" updated.`);
      } else {
        await createLocation(formData);
        setSuccessMsg(`Location "${formData.name}" established.`);
      }
      setShowModal(false);
      fetchLocations();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to save location";
      setError(msg);
    } finally {
      setSubmitting(false);
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
              Logistics Facilities &amp; Locations
            </h1>
            <p className="text-xs text-slate-400 mt-1">
              Maintain depots, transit hubs, and pickup/destination address coordinates
            </p>
          </div>
          <button
            onClick={handleOpenCreate}
            className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold text-white shadow-lg shadow-indigo-500/25 transition-all self-start sm:self-auto"
          >
            + Add Facility Location
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
              <p>Loading facilities...</p>
            </div>
          ) : locations.length === 0 ? (
            <div className="p-12 text-center text-slate-400 space-y-3">
              <span className="text-4xl block">📍</span>
              <p className="text-sm font-semibold text-slate-200">No facilities or hubs created yet</p>
              <p className="text-xs max-w-sm mx-auto">
                Create depots and warehouses across the 8 North Eastern states to support delivery dispatching.
              </p>
              <button
                onClick={handleOpenCreate}
                className="mt-2 px-3 py-1.5 rounded-lg bg-indigo-600 text-xs font-medium text-white hover:bg-indigo-500 transition-colors"
              >
                Add First Facility
              </button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-950/80 border-b border-slate-800 text-slate-400 uppercase tracking-wider text-[11px]">
                  <tr>
                    <th className="py-3 px-4">Facility Name</th>
                    <th className="py-3 px-4">City / State</th>
                    <th className="py-3 px-4">Address</th>
                    <th className="py-3 px-4">Postal Code</th>
                    <th className="py-3 px-4">Coordinates (Lat, Lon)</th>
                    <th className="py-3 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-slate-300">
                  {locations.map((loc) => (
                    <tr key={loc.id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="py-3.5 px-4 font-medium text-white flex items-center gap-2">
                        <span className="text-indigo-400">📍</span>
                        {loc.name}
                      </td>
                      <td className="py-3.5 px-4">
                        <span className="font-semibold text-slate-200">{loc.city}</span>, {loc.state}
                      </td>
                      <td className="py-3.5 px-4 text-slate-400 max-w-xs truncate">
                        {loc.address_line || "—"}
                      </td>
                      <td className="py-3.5 px-4 font-mono text-slate-400">
                        {loc.postal_code || "—"}
                      </td>
                      <td className="py-3.5 px-4 font-mono text-slate-400">
                        {loc.latitude.toFixed(4)}, {loc.longitude.toFixed(4)}
                      </td>
                      <td className="py-3.5 px-4 text-right space-x-2">
                        <button
                          onClick={() => handleOpenEdit(loc)}
                          className="text-slate-400 hover:text-indigo-400 font-medium transition-colors"
                        >
                          Edit
                        </button>
                        <span className="text-slate-700">·</span>
                        <button
                          onClick={() => handleDelete(loc.id, loc.name)}
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

        {/* Modal: Add/Edit Location */}
        {showModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md p-6 shadow-2xl space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <h3 className="text-sm font-bold text-white">
                  {editingLocation ? "Edit Facility Location" : "Add Facility Location"}
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
                  <label className="block text-slate-300 mb-1">Facility / Hub Name</label>
                  <input
                    type="text"
                    required
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="e.g. Guwahati Central Freight Hub"
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-white focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  />
                </div>

                <div>
                  <label className="block text-slate-300 mb-1">Street / Industrial Address</label>
                  <input
                    type="text"
                    value={formData.address_line}
                    onChange={(e) => setFormData({ ...formData, address_line: e.target.value })}
                    placeholder="e.g. Plot 44, Amingaon Industrial Estate"
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-white focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-slate-300 mb-1">City</label>
                    <input
                      type="text"
                      required
                      value={formData.city}
                      onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                      placeholder="e.g. Guwahati"
                      className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-white focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    />
                  </div>

                  <div>
                    <label className="block text-slate-300 mb-1">State</label>
                    <select
                      value={formData.state}
                      onChange={(e) => setFormData({ ...formData, state: e.target.value })}
                      className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-white focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    >
                      <option value="Assam">Assam</option>
                      <option value="Meghalaya">Meghalaya</option>
                      <option value="Arunachal Pradesh">Arunachal Pradesh</option>
                      <option value="Nagaland">Nagaland</option>
                      <option value="Manipur">Manipur</option>
                      <option value="Mizoram">Mizoram</option>
                      <option value="Tripura">Tripura</option>
                      <option value="Sikkim">Sikkim</option>
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-3">
                  <div>
                    <label className="block text-slate-300 mb-1">Postal Code</label>
                    <input
                      type="text"
                      value={formData.postal_code}
                      onChange={(e) => setFormData({ ...formData, postal_code: e.target.value })}
                      placeholder="781031"
                      className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-white focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    />
                  </div>
                  <div>
                    <label className="block text-slate-300 mb-1">Latitude (-90 to +90)</label>
                    <input
                      type="number"
                      required
                      step="any"
                      value={formData.latitude}
                      onChange={(e) => setFormData({ ...formData, latitude: parseFloat(e.target.value) || 0 })}
                      className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-white focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    />
                  </div>
                  <div>
                    <label className="block text-slate-300 mb-1">Longitude (-180 to +180)</label>
                    <input
                      type="number"
                      required
                      step="any"
                      value={formData.longitude}
                      onChange={(e) => setFormData({ ...formData, longitude: parseFloat(e.target.value) || 0 })}
                      className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-white focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    />
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
                    {submitting ? "Saving..." : editingLocation ? "Save Changes" : "Create Location"}
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
