# FIPP 2.0 - Launch Script (PowerShell)
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "Starting FIPP 2.0 (FastAPI Backend + React Frontend)" -ForegroundColor Green
Write-Host "======================================================================"

Write-Host "`n[1/2] Launching FastAPI Backend on http://127.0.0.1:8000 ..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", ".\venv_backend\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

Write-Host "`n[2/2] Launching React Frontend on http://127.0.0.1:5173 ..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev"

Write-Host "`n======================================================================" -ForegroundColor Cyan
Write-Host "React Frontend:    http://127.0.0.1:5173" -ForegroundColor White
Write-Host "FastAPI Backend:   http://127.0.0.1:8000" -ForegroundColor White
Write-Host "API Swagger Docs:  http://127.0.0.1:8000/docs" -ForegroundColor White
Write-Host "Legacy Streamlit:  http://127.0.0.1:8501 (via start_fipp_streamlit.bat)" -ForegroundColor Gray
Write-Host "======================================================================" -ForegroundColor Cyan

Start-Process "http://127.0.0.1:5173"
