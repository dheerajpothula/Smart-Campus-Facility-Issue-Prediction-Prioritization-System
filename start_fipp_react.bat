@echo off
TITLE FIPP 2.0 - Facility Issue Prediction & Prioritisation Platform
echo ======================================================================
echo Starting FIPP 2.0 (FastAPI Backend + React Frontend)
echo ======================================================================

echo.
echo [1/2] Launching FastAPI Backend on http://127.0.0.1:8000 ...
start "FIPP 2.0 Backend (FastAPI)" cmd /k ".\venv_backend\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

echo.
echo [2/2] Launching React Frontend on http://127.0.0.1:5173 ...
start "FIPP 2.0 Frontend (React + Vite)" cmd /k "cd frontend && npm run dev"

echo.
echo ======================================================================
echo Applications are launching!
echo.
echo  - React Frontend:    http://127.0.0.1:5173
echo  - FastAPI Backend:   http://127.0.0.1:8000
echo  - API Swagger Docs:  http://127.0.0.1:8000/docs
echo.
echo Opening React Frontend in your default browser...
start http://127.0.0.1:5173
echo ======================================================================
pause
