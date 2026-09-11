# RouteIQ 2.0 — Developer Setup & Operation Guide

This guide provides step-by-step instructions for provisioning, running, and testing the RouteIQ 2.0 full-stack development environment.

---

## 1. Prerequisites

Ensure the following tools are installed on your machine:
- **Python**: 3.10 or higher
- **Node.js**: 18.18 or higher (LTS recommended)
- **Git**: 2.30 or higher
- **Database (Optional for initial development)**:
  - Local PostgreSQL 15+ OR
  - Free Supabase project account (cloud)

---

## 2. Environment Configuration

RouteIQ 2.0 uses structured environment files. Follow these steps to set up your environment:

### Root Environment Setup
```bash
# In project root
cp .env.example .env
```

### Backend Environment Setup
```bash
cd backend
cp .env.example .env
```
Edit `backend/.env` if connecting to a PostgreSQL or Supabase instance:
```env
PORT=8000
HOST=0.0.0.0
ENVIRONMENT=development
LOG_LEVEL=info
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Optional PostgreSQL Connection String
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/routeiq

# Optional Supabase Connection
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
```

### Frontend Environment Setup
```bash
cd frontend
cp .env.example .env.local
```
Content of `frontend/.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

> [!WARNING]
> Never commit `.env` or `.env.local` files to Git. Only `.env.example` templates may be committed.

---

## 3. Backend Setup & Startup

### Step 3.1: Create Python Virtual Environment
```bash
cd backend

# Windows (PowerShell or Command Prompt):
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux:
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3.2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3.3: Launch the FastAPI Backend
```bash
uvicorn app.main:app --reload --port 8000
```
- **Live Health Diagnostics**: [http://localhost:8000/health](http://localhost:8000/health)
- **Interactive Swagger Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Alternative Redoc Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 4. Frontend Setup & Startup

### Step 4.1: Install Dependencies
```bash
cd frontend
npm install
```

### Step 4.2: Start Next.js Development Server
```bash
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 5. Database Setup (PostgreSQL or Supabase)

### Option A: Local PostgreSQL
1. Create a database named `routeiq`:
   ```sql
   CREATE DATABASE routeiq;
   ```
2. Execute the migration schema:
   ```bash
   psql -U postgres -d routeiq -f database/schema.sql
   ```
3. Set `DATABASE_URL=postgresql://postgres:[password]@localhost:5432/routeiq` in `backend/.env`.

### Option B: Supabase Cloud
1. Navigate to your Supabase Project Dashboard -> **SQL Editor**.
2. Paste the contents of `database/schema.sql` and run the script.
3. In Project Settings -> API, copy your project URL and `anon` key.
4. Set `SUPABASE_URL` and `SUPABASE_ANON_KEY` in `backend/.env`.

> [!NOTE]
> The backend runs gracefully even if no database is yet configured, reporting `decoupled mode` in `/health`.

---

## 6. Testing & Quality Gate

### Backend Automated Test Suite
Run pytest from the repository root:
```bash
python -m pytest backend/tests -v
```

### Frontend Production Build Verification
Verify type safety and compilation:
```bash
cd frontend
npm run build
```

### Health Check Verification via cURL / PowerShell
```powershell
curl http://localhost:8000/health
```
Expected response:
```json
{
  "status": "healthy",
  "service": "RouteIQ 2.0 API",
  "version": "2.0.0",
  "environment": "development",
  "timestamp": "2026-09-11T...",
  "database": {
    "configured": false,
    "primary": "none",
    "message": "No database credentials configured..."
  }
}
```
