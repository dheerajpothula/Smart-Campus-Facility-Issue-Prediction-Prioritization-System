@echo off
title FIPP — Facility Issue Prediction & Prioritization
cd /d "%~dp0"

echo ================================================================
echo   FIPP — Facility Issue Prediction & Prioritization
echo ================================================================
echo.

if exist "%~dp0.venv\Scripts\python.exe" (
    echo [INFO] Starting application using virtual environment (.venv)...
    "%~dp0.venv\Scripts\python.exe" run_server.py
) else (
    echo [WARNING] .venv not found, attempting system python...
    python run_server.py
)

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Application stopped or encountered an error.
    echo Press any key to close this window...
    pause > nul
)
