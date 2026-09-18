"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Header from "@/components/Header";
import {
  listDeliveries,
  createDelivery,
  updateDelivery,
  deleteDelivery,
  listLocations,
  getStoredUser,
  Delivery,
  Location,
  DeliveryPriority,
  DeliveryStatus,
} from "@/lib/api";

export default function DeliveriesPage() {
  const router = useRouter();
  const [deliveries, setDeliveries] = useState<Delivery[]>([]);
  const [locations, setLocations] = useState<Location[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Modal states
  const [showModal, setShowModal] = useState(false);
  const [editingDelivery, setEditingDelivery] = useState<Delivery | null>(null);
  const [formData, setFormData] = useState({
    reference_number: "",
    pickup_location_id: "",
    delivery_location_id: "",
    priority: "normal" as DeliveryPriority,
    status: "pending" as DeliveryStatus,
    package_weight: 500,
    package_volume: 2.0,
    requested_delivery_date: new Date().toISOString().split("T")[0],
    time_window_start: "",
    time_window_end: "",
    notes: "",
  });
  const [submitting, setSubmitting] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [dList, lList] = await Promise.all([
        listDeliveries(),
        listLocations(),
      ]);
      setDeliveries(dList);
      setLocations(lList);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load deliveries";
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
    fetchData();
  }, [router]);

  const handleOpenCreate = () => {
    setEditingDelivery(null);
    setFormData({
      reference_number: `ORD-NER-${Math.floor(1000 + Math.random() * 9000)}`,
      pickup_location_id: locations.length > 0 ? locations[0].id : "",
      delivery_location_id: locations.length > 1 ? locations[1].id : locations[0]?.id || "",
      priority: "normal",
      status: "pending",
      package_weight: 500,
      package_volume: 2.0,
      requested_delivery_date: new Date().toISOString().split("T")[0],
      time_window_start: "",
      time_window_end: "",
      notes: "",
    });
    setError(null);
    setShowModal(true);
  };

  const handleOpenEdit = (d: Delivery) => {
    setEditingDelivery(d);
    setFormData({
      reference_number: d.reference_number,
      pickup_location_id: d.pickup_location_id,
      delivery_location_id: d.delivery_location_id,
      priority: d.priority,
      status: d.status,
      package_weight: d.package_weight,
      package_volume: d.package_volume,
      requested_delivery_date: d.requested_delivery_date || "",
      time_window_start: d.time_window_start ? d.time_window_start.substring(0, 16) : "",
      time_window_end: d.time_window_end ? d.time_window_end.substring(0, 16) : "",
      notes: d.notes || "",
    });
    setError(null);
    setShowModal(true);
  };

  const handleDelete = async (id: string, ref: string) => {
    if (!confirm(`Are you sure you want to cancel or delete delivery order "${ref}"?`)) return;
    try {
      await deleteDelivery(id);
      setSuccessMsg(`Delivery "${ref}" deleted.`);
      fetchData();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Delete failed";
      setError(msg);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    if (!formData.pickup_location_id || !formData.delivery_location_id) {
      setError("Please select both a pickup and delivery destination location.");
      setSubmitting(false);
      return;
    }

    if (formData.time_window_start && formData.time_window_end) {
      if (new Date(formData.time_window_start) > new Date(formData.time_window_end)) {
        setError("Time window start must be before or equal to time window end.");
        setSubmitting(false);
        return;
      }
    }

    try {
      const payload = {
        ...formData,
        time_window_start: formData.time_window_start ? new Date(formData.time_window_start).toISOString() : undefined,
        time_window_end: formData.time_window_end ? new Date(formData.time_window_end).toISOString() : undefined,
      };

      if (editingDelivery) {
        await updateDelivery(editingDelivery.id, payload);
        setSuccessMsg(`Delivery order "${formData.reference_number}" updated.`);
      } else {
        await createDelivery(payload);
        setSuccessMsg(`Delivery order "${formData.reference_number}" registered.`);
      }
      setShowModal(false);
      fetchData();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to save delivery";
      setError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  const getLocationName = (id: string) => {
    const loc = locations.find((l) => l.id === id);
    return loc ? `${loc.name} (${loc.city})` : id.substring(0, 8);
  };

  const getPriorityBadge = (priority: DeliveryPriority) => {
    switch (priority) {
      case "urgent":
        return <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20 animate-pulse">Urgent</span>;
      case "high":
        return <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">High</span>;
      case "normal":
        return <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">Normal</span>;
      case "low":
        return <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-slate-500/10 text-slate-400 border border-slate-500/20">Low</span>;
    }
  };

  const getStatusBadge = (status: DeliveryStatus) => {
    switch (status) {
      case "pending":
        return <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-slate-500/10 text-slate-300 border border-slate-700">Pending</span>;
      case "assigned":
        return <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">Assigned</span>;
      case "in_transit":
        return <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">In Transit</span>;
      case "delivered":
        return <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">Delivered</span>;
      case "cancelled":
        return <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">Cancelled</span>;
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
              Delivery Order Management
            </h1>
            <p className="text-xs text-slate-400 mt-1">
              Dispatch orders, cargo weight/volume parameters, priority levels, and delivery time windows
            </p>
          </div>
          <button
            onClick={handleOpenCreate}
            className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-xs font-semibold text-white shadow-lg shadow-indigo-500/25 transition-all self-start sm:self-auto"
          >
            + Create Delivery Order
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

        {/* Deliveries Table */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
          {loading ? (
            <div className="p-12 text-center text-xs text-slate-400">
              <span className="inline-block w-5 h-5 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mb-2" />
              <p>Loading delivery consignments...</p>
            </div>
          ) : deliveries.length === 0 ? (
            <div className="p-12 text-center text-slate-400 space-y-3">
              <span className="text-4xl block">📦</span>
              <p className="text-sm font-semibold text-slate-200">No deliveries created yet</p>
              <p className="text-xs max-w-sm mx-auto">
                Dispatch orders between your registered pickup and delivery facilities.
              </p>
              {locations.length === 0 ? (
                <p className="text-xs text-amber-400 font-medium">
                  Note: Please create at least one Facility Location before adding deliveries.
                </p>
              ) : (
                <button
                  onClick={handleOpenCreate}
                  className="mt-2 px-3 py-1.5 rounded-lg bg-indigo-600 text-xs font-medium text-white hover:bg-indigo-500 transition-colors"
                >
                  Create First Delivery
                </button>
              )}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-950/80 border-b border-slate-800 text-slate-400 uppercase tracking-wider text-[11px]">
                  <tr>
                    <th className="py-3 px-4">Ref #</th>
                    <th className="py-3 px-4">Origin / Pickup</th>
                    <th className="py-3 px-4">Destination</th>
                    <th className="py-3 px-4">Priority</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4">Weight / Volume</th>
                    <th className="py-3 px-4">Target Date</th>
                    <th className="py-3 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-slate-300">
                  {deliveries.map((d) => (
                    <tr key={d.id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="py-3.5 px-4 font-mono font-medium text-indigo-400">
                        {d.reference_number}
                      </td>
                      <td className="py-3.5 px-4 text-white">
                        {getLocationName(d.pickup_location_id)}
                      </td>
                      <td className="py-3.5 px-4 text-white">
                        {getLocationName(d.delivery_location_id)}
                      </td>
                      <td className="py-3.5 px-4">
                        {getPriorityBadge(d.priority)}
                      </td>
                      <td className="py-3.5 px-4">
                        {getStatusBadge(d.status)}
                      </td>
                      <td className="py-3.5 px-4 text-slate-400">
                        {d.package_weight.toLocaleString()} kg · {d.package_volume} m³
                      </td>
                      <td className="py-3.5 px-4 text-slate-400">
                        {d.requested_delivery_date || "Flexible"}
                      </td>
                      <td className="py-3.5 px-4 text-right space-x-2">
                        <button
                          onClick={() => handleOpenEdit(d)}
                          className="text-slate-400 hover:text-indigo-400 font-medium transition-colors"
                        >
                          Edit
                        </button>
                        <span className="text-slate-700">·</span>
                        <button
                          onClick={() => handleDelete(d.id, d.reference_number)}
                          className="text-slate-400 hover:text-red-400 font-medium transition-colors"
                        >
                          Cancel
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Modal: Add/Edit Delivery */}
        {showModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg p-6 shadow-2xl space-y-4 max-h-[90vh] overflow-y-auto">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <h3 className="text-sm font-bold text-white">
                  {editingDelivery ? "Edit Delivery Order" : "New Delivery Consignment"}
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
                  <label className="block text-slate-300 mb-1">Reference Number / Tracking Code</label>
                  <input
                    type="text"
                    required
                    value={formData.reference_number}
                    onChange={(e) => setFormData({ ...formData, reference_number: e.target.value })}
                    placeholder="e.g. ORD-GAU-SHL-101"
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-white uppercase focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  />
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-slate-300 mb-1">Origin / Pickup Location</label>
                    <select
                      required
                      value={formData.pickup_location_id}
                      onChange={(e) => setFormData({ ...formData, pickup_location_id: e.target.value })}
                      className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-white focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    >
                      <option value="">Select origin facility</option>
                      {locations.map((loc) => (
                        <option key={loc.id} value={loc.id}>
                          {loc.name} ({loc.city})
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-slate-300 mb-1">Destination Location</label>
                    <select
                      required
                      value={formData.delivery_location_id}
                      onChange={(e) => setFormData({ ...formData, delivery_location_id: e.target.value })}
                      className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-white focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    >
                      <option value="">Select destination facility</option>
                      {locations.map((loc) => (
                        <option key={loc.id} value={loc.id}>
                          {loc.name} ({loc.city})
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <div>
                    <label className="block text-slate-300 mb-1">Priority</label>
                    <select
                      value={formData.priority}
                      onChange={(e) => setFormData({ ...formData, priority: e.target.value as DeliveryPriority })}
                      className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-white focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    >
                      <option value="low">Low</option>
                      <option value="normal">Normal</option>
                      <option value="high">High</option>
                      <option value="urgent">Urgent</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-slate-300 mb-1">Status</label>
                    <select
                      value={formData.status}
                      onChange={(e) => setFormData({ ...formData, status: e.target.value as DeliveryStatus })}
                      className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-white focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    >
                      <option value="pending">Pending</option>
                      <option value="assigned">Assigned</option>
                      <option value="in_transit">In Transit</option>
                      <option value="delivered">Delivered</option>
                      <option value="cancelled">Cancelled</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-slate-300 mb-1">Weight (kg)</label>
                    <input
                      type="number"
                      min="0"
                      step="any"
                      value={formData.package_weight}
                      onChange={(e) => setFormData({ ...formData, package_weight: parseFloat(e.target.value) || 0 })}
                      className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-white focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    />
                  </div>

                  <div>
                    <label className="block text-slate-300 mb-1">Volume (m³)</label>
                    <input
                      type="number"
                      min="0"
                      step="any"
                      value={formData.package_volume}
                      onChange={(e) => setFormData({ ...formData, package_volume: parseFloat(e.target.value) || 0 })}
                      className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-white focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div>
                    <label className="block text-slate-300 mb-1">Target Delivery Date</label>
                    <input
                      type="date"
                      value={formData.requested_delivery_date}
                      onChange={(e) => setFormData({ ...formData, requested_delivery_date: e.target.value })}
                      className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-white focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    />
                  </div>

                  <div>
                    <label className="block text-slate-300 mb-1">Time Window Start</label>
                    <input
                      type="datetime-local"
                      value={formData.time_window_start}
                      onChange={(e) => setFormData({ ...formData, time_window_start: e.target.value })}
                      className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-white focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    />
                  </div>

                  <div>
                    <label className="block text-slate-300 mb-1">Time Window End</label>
                    <input
                      type="datetime-local"
                      value={formData.time_window_end}
                      onChange={(e) => setFormData({ ...formData, time_window_end: e.target.value })}
                      className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-white focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-slate-300 mb-1">Handling Notes / Constraints</label>
                  <textarea
                    rows={2}
                    value={formData.notes}
                    onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                    placeholder="e.g. Fragile terrain corridor, avoid monsoon washout detour"
                    className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-white focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  />
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
                    {submitting ? "Saving..." : editingDelivery ? "Save Changes" : "Create Delivery"}
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
