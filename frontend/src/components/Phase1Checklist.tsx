import React from "react";

export default function Phase1Checklist() {
  const items = [
    { name: "FastAPI Backend Scaffolding (Python 3.14 + Pydantic v2)", status: "done" },
    { name: "GET /health Endpoint with Live System & DB Diagnostics", status: "done" },
    { name: "PostgreSQL & Supabase Modular Connectivity Layer", status: "done" },
    { name: "PostgreSQL Schema Definition (nodes, edges, hazards)", status: "done" },
    { name: "Next.js 16 App Router + TypeScript + Tailwind CSS Frontend", status: "done" },
    { name: "Frontend-to-Backend Typed API Health Communication", status: "done" },
    { name: "Environment Safety (.env.example templates & .gitignore)", status: "done" },
    { name: "Automated Test Suite (pytest health tests)", status: "done" },
    { name: "Architecture & Setup Documentation (docs/architecture.md, docs/setup.md)", status: "done" },
  ];

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-6">
      <div className="flex items-center justify-between pb-4 border-b border-slate-800">
        <div>
          <h3 className="text-base font-semibold text-white">Phase 1 Acceptance Verification</h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Production-quality project foundation established per specification.
          </p>
        </div>
        <span className="text-xs font-semibold px-2.5 py-1 rounded-md bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          9 / 9 Tasks Ready
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-4">
        {items.map((item, idx) => (
          <div
            key={idx}
            className="flex items-start gap-2.5 p-2.5 rounded-lg bg-slate-950/40 border border-slate-800/80 text-xs"
          >
            <span className="mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-emerald-500/20 text-emerald-400">
              <svg className="w-2.5 h-2.5" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
              </svg>
            </span>
            <span className="text-slate-300 font-medium">{item.name}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
