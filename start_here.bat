@echo off
title Lumina App Store - Dev Environment
color 0A
echo.
echo  ╔══════════════════════════════════════════╗
echo  ║       LUMINA APP STORE - DEV START       ║
echo  ╚══════════════════════════════════════════╝
echo.

:: Check Python
where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Install Python 3.11+
    pause
    exit /b 1
)

:: Check Node
where node >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found. Install Node.js 20+
    pause
    exit /b 1
)

:: Check pnpm
where pnpm >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing pnpm...
    npm install -g pnpm
)

echo [1/5] Installing Python dependencies...
pip install fastapi uvicorn sqlalchemy aiosqlite pydantic pydantic-settings python-multipart python-jose passlib jsonschema httpx websockets --quiet 2>nul

echo [2/5] Creating database + sample data...
cd /d %~dp0
python init_db.py

echo [3/5] Installing frontend dependencies...
cd /d %~dp0apps\store-frontend
if not exist node_modules (
    pnpm install --frozen-lockfile 2>nul || pnpm install
)

echo [4/5] Running backend tests...
cd /d %~dp0
python -m pytest packages/config-schema/test_validator.py apps/app_engine/tests/ apps/store_backend/tests/ -q 2>nul
if errorlevel 1 (
    echo [WARN] Some tests failed. Check output above.
) else (
    echo        All tests passed!
)

echo [5/5] Starting servers...
echo.
echo  ┌─────────────────────────────────────────┐
echo  │  Backend:  http://localhost:8000         │
echo  │  Swagger:  http://localhost:8000/docs    │
echo  │  Frontend: http://localhost:3000         │
echo  │                                         │
echo  │  Press Ctrl+C to stop all servers       │
echo  └─────────────────────────────────────────┘
echo.

:: Start backend in background
cd /d %~dp0
start "Lumina Backend" cmd /k "cd /d %~dp0 && set LUMINA_DATABASE_URL=sqlite+aiosqlite:///./lumina_dev.db && python -m uvicorn apps.store_backend.main:app --reload --port 8000"

:: Wait for backend to start
timeout /t 3 /nobreak >nul

:: Start frontend in foreground
cd /d %~dp0apps\store-frontend
set NEXT_PUBLIC_API_URL=http://localhost:8000
pnpm dev --port 3000
