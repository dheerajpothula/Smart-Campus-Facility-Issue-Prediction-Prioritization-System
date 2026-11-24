@echo off
TITLE FIPP 2.0 - All Application Layers
echo ======================================================================
echo Starting All Three FIPP Application Layers
echo ======================================================================

echo.
echo [1/3] Launching FastAPI Backend on http://127.0.0.1:8000 ...
start "FIPP 2.0 Backend (FastAPI)" cmd /k ".\venv_backend\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000"

echo.
echo [2/3] Launching React Frontend on http://127.0.0.1:5173 ...
start "FIPP 2.0 Frontend (React + Vite)" cmd /k "cd frontend && npm run dev"

echo.
echo [3/3] Launching Legacy Streamlit on http://127.0.0.1:8501 ...
start "FIPP Legacy Portal (Streamlit)" cmd /k "python -m streamlit run smart-campus-facility-prediction/app.py --server.port 8501 --server.address 127.0.0.1"

echo.
echo ======================================================================
echo All 3 layers are running concurrently:
echo  1. React Frontend (New):     http://127.0.0.1:5173
echo  2. FastAPI Backend:          http://127.0.0.1:8000
echo  3. Streamlit Portal (Legacy): http://127.0.0.1:8501
echo ======================================================================
pause
