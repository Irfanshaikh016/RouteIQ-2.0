"use client";

import React, { useState, useEffect, useCallback } from "react";
import { checkBackendHealth, ApiPingResult, getApiBaseUrl } from "@/lib/api";

export default function ConnectivityStatus() {
  const [result, setResult] = useState<ApiPingResult | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [lastChecked, setLastChecked] = useState<string>("");
  const apiUrl = getApiBaseUrl();

  const handlePing = useCallback(async () => {
    setLoading(true);
    const res = await checkBackendHealth();
    setResult(res);
    setLoading(false);
    setLastChecked(new Date().toLocaleTimeString());
  }, []);

  useEffect(() => {
    handlePing();
  }, [handlePing]);

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur-md shadow-xl">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-xl font-semibold text-white">Full-Stack Connectivity Console</h2>
            {loading ? (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20">
                <span className="h-1.5 w-1.5 rounded-full bg-amber-400 animate-pulse" />
                Pinging Backend...
              </span>
            ) : result?.ok ? (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
                Backend Connected (HTTP {result.statusCode})
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-rose-500/10 text-rose-400 border border-rose-500/20">
                <span className="h-1.5 w-1.5 rounded-full bg-rose-400" />
                Backend Unreachable
              </span>
            )}
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Validating communication between Next.js (port 3000) and FastAPI (<code className="text-cyan-400 text-xs">{apiUrl}</code>).
          </p>
        </div>

        <button
          onClick={handlePing}
          disabled={loading}
          className="inline-flex items-center justify-center px-4 py-2 rounded-lg text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-md hover:shadow-indigo-500/25 active:scale-95 cursor-pointer"
        >
          {loading ? (
            <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
            </svg>
          ) : (
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          )}
          Ping Backend API
        </button>
      </div>

      {/* Diagnostics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
        {/* Latency card */}
        <div className="p-4 rounded-lg bg-slate-800/50 border border-slate-700/60">
          <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Round-Trip Latency</div>
          <div className="text-2xl font-bold text-white mt-1">
            {result ? `${result.latencyMs} ms` : "—"}
          </div>
          <div className="text-xs text-slate-400 mt-1">
            Last checked: {lastChecked || "Never"}
          </div>
        </div>

        {/* Backend service card */}
        <div className="p-4 rounded-lg bg-slate-800/50 border border-slate-700/60">
          <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">FastAPI Service</div>
          <div className="text-xl font-bold text-slate-200 mt-1 truncate">
            {result?.data?.service || "RouteIQ 2.0 API"}
          </div>
          <div className="text-xs text-slate-400 mt-1">
            Version {result?.data?.version || "2.0.0"} · {result?.data?.environment || "development"}
          </div>
        </div>

        {/* Database state card */}
        <div className="p-4 rounded-lg bg-slate-800/50 border border-slate-700/60">
          <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Database Connectivity</div>
          <div className="flex items-center gap-2 mt-1">
            {result?.data?.database?.configured ? (
              <span className="text-emerald-400 font-semibold text-lg flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-emerald-400" />
                {result.data.database.primary.toUpperCase()} Ready
              </span>
            ) : (
              <span className="text-amber-400 font-medium text-base flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-amber-400" />
                Decoupled / Ready
              </span>
            )}
          </div>
          <div className="text-xs text-slate-400 mt-1 truncate">
            {result?.data?.database?.message || (result?.data?.database?.configured ? "Driver connected" : "Awaiting credentials")}
          </div>
        </div>
      </div>

      {/* Error or Success Details */}
      {result?.error && (
        <div className="mt-5 p-4 rounded-lg bg-rose-950/30 border border-rose-800/50 text-rose-300 text-sm">
          <div className="font-semibold flex items-center gap-2">
            <svg className="w-4 h-4 text-rose-400" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
            API Connection Notice
          </div>
          <p className="mt-1 text-xs text-rose-200">{result.error}</p>
          <div className="mt-3 text-xs bg-slate-950/50 p-2.5 rounded font-mono text-slate-300">
            Start backend with: <span className="text-cyan-400">cd backend &amp;&amp; python -m uvicorn app.main:app --port 8000</span>
          </div>
        </div>
      )}

      {/* JSON Payload Viewer */}
      {result?.data && (
        <div className="mt-5">
          <details className="group">
            <summary className="text-xs font-medium text-slate-400 hover:text-slate-200 cursor-pointer flex items-center gap-1 select-none">
              <span className="group-open:rotate-90 transition-transform">▸</span>
              View Live Response JSON Payload
            </summary>
            <pre className="mt-2 p-3 rounded-lg bg-slate-950 border border-slate-800 text-xs text-emerald-400 font-mono overflow-x-auto">
              {JSON.stringify(result.data, null, 2)}
            </pre>
          </details>
        </div>
      )}
    </div>
  );
}
