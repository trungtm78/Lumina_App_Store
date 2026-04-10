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
└── infra/                          ← Docker compose (Postgres, Redis, MinIO)
```

App Engine code lives in Lumina Core repo (separate). This repo has the spec + tests.

## Key decisions

- **DB source of truth** for is_active (NOT config.json)
- **skill.md prompt injection** in scope v1 (apps actually "run" in Core AI)
- **Live Skill Authoring** replaces vendor upload workflow (Monaco editor + chat test)
- **1-click install** in Menu Apps (download + verify + unzip + activate)
- **JSON columns** for systems/modules (SQLite test compat, works on Postgres too)

## Running

```bash
# Backend
cd infra && docker compose up -d                    # Postgres + Redis + MinIO
cd apps/store_backend && uvicorn main:app --reload  # API on :8000

# Frontend
cd apps/store-frontend && pnpm dev                  # Next.js on :3000

# Tests
python -m pytest packages/config-schema/ apps/app_engine/ apps/store_backend/ -v
```

## Testing

- Framework: pytest (backend), Next.js build check (frontend)
- Run all: `python -m pytest packages/ apps/app_engine/ apps/store_backend/ -v`
- 127 backend tests, TypeScript build passes with zero errors
