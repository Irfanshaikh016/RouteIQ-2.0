import Header from "@/components/Header";
import ConnectivityStatus from "@/components/ConnectivityStatus";
import OverviewCards from "@/components/OverviewCards";
import Phase1Checklist from "@/components/Phase1Checklist";

export default function Home() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 selection:bg-indigo-500 selection:text-white">
      <Header />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Welcome / Context Banner */}
        <div className="relative overflow-hidden rounded-2xl border border-indigo-950/60 bg-gradient-to-r from-slate-900 via-indigo-950/40 to-slate-900 p-8 shadow-2xl">
          <div className="relative z-10 max-w-3xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 mb-3">
              <span>🚀</span> RouteIQ 2.0 · North Eastern Region Logistics Intelligence
            </div>
            <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white leading-tight">
              Cognitive, Graph-Aware Logistics Intelligence
            </h1>
            <p className="mt-3 text-sm sm:text-base text-slate-300 leading-relaxed">
              Engineered for extreme geography, monsoon precipitation, and fragile mountain corridors across the 8 North Eastern states. Reframing regional logistics from static heuristics to a self-learning, multi-objective graph decision system.
            </p>
          </div>

          <div className="absolute right-0 top-0 bottom-0 w-1/3 bg-gradient-to-l from-indigo-500/10 to-transparent pointer-events-none" />
        </div>

        {/* Live Connectivity Console */}
        <section aria-labelledby="connectivity-heading">
          <ConnectivityStatus />
        </section>

        {/* System Overview Cards */}
        <section aria-labelledby="overview-heading">
          <div className="mb-4">
            <h2 id="overview-heading" className="text-lg font-semibold text-white">System Architecture &amp; Future Waves</h2>
            <p className="text-xs text-slate-400">Core pillars and progressive phase trajectory</p>
          </div>
          <OverviewCards />
        </section>

        {/* Phase 1 Verification Checklist */}
        <section aria-labelledby="verification-heading">
          <Phase1Checklist />
        </section>

        {/* Developer Quick Links Footer */}
        <footer className="pt-6 pb-12 border-t border-slate-800/80 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-400">
          <div>
            RouteIQ 2.0 · Full-Stack Foundation · Milestone 1
          </div>
          <div className="flex items-center gap-4">
            <a
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noreferrer"
              className="hover:text-white transition-colors"
            >
              Backend Swagger (/docs)
            </a>
            <span className="text-slate-700">·</span>
            <a
              href="http://localhost:8000/health"
              target="_blank"
              rel="noreferrer"
              className="hover:text-white transition-colors"
            >
              GET /health
            </a>
            <span className="text-slate-700">·</span>
            <span>Next.js + FastAPI + Supabase/PostgreSQL</span>
          </div>
        </footer>
      </main>
    </div>
  );
}
