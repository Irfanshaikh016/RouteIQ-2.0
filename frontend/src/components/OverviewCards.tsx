import React from "react";

export default function OverviewCards() {
  const cards = [
    {
      title: "Full-Stack Foundation",
      tag: "Phase 1 Active",
      tagColor: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
      description: "FastAPI Python backend with Next.js 16 frontend, Supabase/PostgreSQL schema, and automated test suite.",
      metric: "Operational",
      metricLabel: "Core Architecture Status",
      icon: (
        <svg className="w-5 h-5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
        </svg>
      ),
    },
    {
      title: "NER Transport Graph",
      tag: "Phase 2 Preview",
      tagColor: "bg-blue-500/10 text-blue-400 border-blue-500/20",
      description: "Attributed directed road network covering critical hubs: Guwahati, Shillong, Silchar, Dimapur, Kohima, and Imphal.",
      metric: "8 States",
      metricLabel: "Regional Graph Scope",
      icon: (
        <svg className="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
      ),
    },
    {
      title: "Risk & Hazard Engine",
      tag: "Phase 3 Preview",
      tagColor: "bg-amber-500/10 text-amber-400 border-amber-500/20",
      description: "Spatio-temporal risk modeling incorporating monsoon precipitation, landslide frequency, and slope fragility.",
      metric: "Dynamic",
      metricLabel: "Edge Impedance Model",
      icon: (
        <svg className="w-5 h-5 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
      ),
    },
    {
      title: "Multi-Objective Routing",
      tag: "Phase 4 Preview",
      tagColor: "bg-purple-500/10 text-purple-400 border-purple-500/20",
      description: "Pareto-optimal route selection calculating trade-offs between travel duration, route safety, and vehicle load constraints.",
      metric: "Pareto Search",
      metricLabel: "Fastest vs. Safest vs. Eco",
      icon: (
        <svg className="w-5 h-5 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      ),
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card, idx) => (
        <div
          key={idx}
          className="rounded-xl border border-slate-800 bg-slate-900/40 p-5 hover:border-slate-700 transition-all hover:-translate-y-0.5"
        >
          <div className="flex items-center justify-between">
            <div className="p-2 rounded-lg bg-slate-800 border border-slate-700/60">
              {card.icon}
            </div>
            <span className={`text-[11px] font-medium px-2 py-0.5 rounded-full border ${card.tagColor}`}>
              {card.tag}
            </span>
          </div>

          <h3 className="font-semibold text-white mt-4">{card.title}</h3>
          <p className="text-xs text-slate-400 mt-1.5 leading-relaxed line-clamp-3">
            {card.description}
          </p>

          <div className="mt-4 pt-4 border-t border-slate-800/80 flex items-baseline justify-between">
            <span className="text-xs text-slate-400">{card.metricLabel}</span>
            <span className="text-sm font-bold text-slate-200">{card.metric}</span>
          </div>
        </div>
      ))}
    </div>
  );
}
