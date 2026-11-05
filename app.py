"""
Smart Campus Facility Issue Prediction & Prioritization System
Root Launcher: Delegates execution to smart-campus-facility-prediction/app.py
"""
import sys
import runpy
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = CURRENT_DIR / "smart-campus-facility-prediction"
TARGET_APP = PROJECT_DIR / "app.py"

if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

if __name__ == "__main__":
    runpy.run_path(str(TARGET_APP), run_name="__main__")
