# RouteIQ 2.0 — Render Cloud Deployment Guide

## 1. Overview

RouteIQ 2.0 includes a declarative infrastructure blueprint (`render.yaml`) for deploying the FastAPI backend as a managed Web Service on [Render](https://render.com).

---

## 2. Infrastructure Blueprint (`render.yaml`)

```yaml
services:
  - type: web
    name: routeiq-backend
    runtime: python
    region: singapore
    plan: free
    branch: main
    buildCommand: pip install --upgrade pip && pip install -r backend/requirements.txt
    startCommand: cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT
    healthCheckPath: /health
    autoDeploy: true
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.8
      - key: ENVIRONMENT
        value: production
      - key: APP_NAME
        value: RouteIQ 2.0 Backend
      - key: CORS_ORIGINS
        value: http://localhost:3000,https://routeiq.vercel.app
      - key: ACCESS_TOKEN_EXPIRE_MINUTES
        value: 1440
      - key: JWT_SECRET_KEY
        generateValue: true
      - key: SUPABASE_URL
        sync: false
      - key: SUPABASE_KEY
        sync: false
      - key: DATABASE_URL
        sync: false
```

---

## 3. Step-by-Step Deployment Procedure

1. **Connect GitHub Repository**:
   - In the Render Dashboard, select **New +** → **Blueprint**.
   - Connect the repository: `https://github.com/Irfanshaikh016/RouteIQ-2.0.git`.
2. **Review Blueprint Parameters**:
   - Render detects `render.yaml` and parses the service specification.
   - Region: `singapore` (recommended for minimal latency to India / NER).
3. **Configure Environment Secrets**:
   - Supply `DATABASE_URL` (direct connection string to PostgreSQL / Supabase with PostGIS).
   - Supply `SUPABASE_URL` and `SUPABASE_KEY` (if using Supabase authentication or storage).
   - Render automatically generates a secure pseudo-random `JWT_SECRET_KEY`.
4. **Deploy**:
   - Click **Apply**.
   - Render runs `pip install -r backend/requirements.txt`, boots the service via Uvicorn, and verifies the `/health` endpoint before shifting traffic.
5. **Zero-Downtime Auto-Deploy**:
   - Commits pushed to `main` trigger automatic background builds and zero-downtime rolling deploys.
