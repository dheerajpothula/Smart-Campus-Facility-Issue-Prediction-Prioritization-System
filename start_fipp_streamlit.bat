@echo off
TITLE FIPP 1.0 - Legacy Streamlit Application
echo ======================================================================
echo Starting FIPP 1.0 Legacy Application (Streamlit)
echo ======================================================================

echo.
echo Launching Streamlit on http://127.0.0.1:8501 ...
python -m streamlit run smart-campus-facility-prediction/app.py --server.port 8501 --server.address 127.0.0.1
pause
