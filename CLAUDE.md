# Lumina App Store

Internal marketplace for addons in the Lumina AI ecosystem (Core/Plus/Storage/Care).

## Architecture

```
c:\Lumina\                          ← This repo (marketplace)
├── packages/config-schema/         ← Canonical JSON Schema + Python validator
├── apps/app_engine/                ← Scanner, registry, activation, prompt injection
├── apps/store_backend/             ← FastAPI marketplace API
├── apps/store-frontend/            ← Next.js customer portal + authoring IDE
├── examples/crm-connector/         ← Sample app
├── infra/                          ← Docker compose (Postgres, Redis, MinIO)
├── LuminaApps/                     ← Central ZIP storage for approved app packages
├── init_db.py                      ← DB init + sample data seeder
└── start_here.bat                  ← One-click dev setup (Windows)
```

App Engine code lives in Lumina Core repo (separate). This repo has the spec + tests.

## Key decisions

- **DB source of truth** for is_active (NOT config.json)
- **skill.md prompt injection** in scope v1 (apps actually "run" in Core AI)
- **Live Skill Authoring** replaces vendor upload workflow (Monaco editor + chat test)
- **1-click install** in Menu Apps (download + verify + unzip + activate)
- **JSON columns** for systems/modules (SQLite test compat, works on Postgres too)
- **/LuminaApps/** central ZIP storage (cached on deploy, streamed on download)
- **Dark mode** support (auto via prefers-color-scheme)

## Running

```bash
# Quick start (Windows)
start_here.bat                                       # Installs deps, seeds DB, starts both servers

# Manual start
cd infra && docker compose up -d                     # Postgres + Redis + MinIO (optional, SQLite fallback)
set LUMINA_DATABASE_URL=sqlite+aiosqlite:///./lumina_dev.db
python init_db.py                                    # Create tables + seed 4 sample apps
python -m uvicorn apps.store_backend.main:app --reload --port 8000  # Backend :8000
cd apps/store-frontend && pnpm dev --port 3000       # Frontend :3000

# Tests
python -m pytest packages/config-schema/ apps/app_engine/ apps/store_backend/ -v
```

## Testing

- Framework: pytest (backend), Next.js build check (frontend)
- Run all: `python -m pytest packages/ apps/app_engine/ apps/store_backend/ -v`
- 128 backend tests, TypeScript build passes with zero errors

## Deploy Configuration (configured by /setup-deploy)
- Platform: Vercel (frontend) + Render (backend)
- Frontend URL: https://lumina-store.vercel.app
- Backend URL: https://lumina-api.onrender.com
- Deploy workflow: auto-deploy on push to main (both platforms)
- Merge method: squash
- Project type: web app (marketplace)

### Frontend (Vercel)
- Source: `apps/store-frontend/`
- Framework: Next.js
- Build command: `pnpm build`
- Output: `.next/`
- Health check: https://lumina-store.vercel.app
- Deploy trigger: automatic on push to main

### Backend (Render)
- Source: `apps/store_backend/`
- Runtime: Python 3.11
- Start command: `uvicorn apps.store_backend.main:app --host 0.0.0.0 --port $PORT`
- Health check: https://lumina-api.onrender.com/health
- Deploy trigger: automatic on push to main
- Environment variables needed: LUMINA_DATABASE_URL, LUMINA_REDIS_URL, LUMINA_MINIO_ENDPOINT, LUMINA_JWT_SECRET

### Custom deploy hooks
- Pre-merge: `python -m pytest packages/config-schema/ apps/app_engine/ apps/store_backend/ -v`
- Deploy trigger: automatic on push to main
- Deploy status: poll production URLs
- Health check: GET https://lumina-api.onrender.com/health (expect `{"status":"ok"}`)
