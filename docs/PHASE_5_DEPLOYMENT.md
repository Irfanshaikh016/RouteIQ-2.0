# RouteIQ 2.0 — Phase 5 Deployment & Verification Guide

## 1. Prerequisites & Environment

RouteIQ 2.0 Phase 5 requires:
- **Node.js**: v18.17+ or v20+ (Next.js 16.3.4 runtime)
- **Python**: 3.11+ (FastAPI + NetworkX backend)
- **Database**: PostgreSQL with PostGIS or Supabase cloud instance
- **Dependencies**: Leaflet & `@types/leaflet` (already installed in `frontend/package.json`)

---

## 2. Verification Checklist

### 2.1 Backend Automated Test Suite
Run the full backend test suite containing all 47 tests:
```powershell
python -m pytest backend/tests -v
```
Expected output:
```
============================= 47 passed in 9.62s ==============================
```

### 2.2 Next.js Production Build
Compile the frontend static pages to ensure complete TypeScript, JSX, and SSR compliance:
```powershell
cd frontend
npm run build
```
Expected output:
```
✓ Generating static pages using 11 workers (10/10)
○ (Static) prerendered as static content
Exit code 0
```

### 2.3 Starting Local Development Servers

**Terminal 1 — Backend**:
```powershell
cd c:\Users\irfan\Downloads\RouteIQ-2.0
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 — Frontend**:
```powershell
cd c:\Users\irfan\Downloads\RouteIQ-2.0\frontend
npm run dev
```
Open browser to `http://localhost:3000/dashboard` to interact with the Operations Console.

---

## 3. Production Deployment Notes (Vercel & Render)

- **Frontend (Vercel)**:
  - Framework Preset: Next.js
  - Root Directory: `frontend`
  - Build Command: `npm run build`
  - Output Directory: `.next`
  - Environment Variables:
    - `NEXT_PUBLIC_API_URL`: URL of deployed FastAPI backend (e.g. `https://routeiq-backend.onrender.com`)
- **Backend (Render)**:
  - Service Type: Web Service
  - Environment: Python
  - Build Command: `pip install -r backend/requirements.txt`
  - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
  - Refer to `render.yaml` for infrastructure blueprint.
