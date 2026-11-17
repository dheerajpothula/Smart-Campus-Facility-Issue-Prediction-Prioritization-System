"""
Launcher script for FIPP — Facility Issue Prediction & Prioritization.
Starts the core Streamlit SaaS application on an available local port and opens the browser.
"""

import os
import sys
import subprocess
import webbrowser
import threading
import time

def open_browser_delayed(url: str):
    time.sleep(1.8)
    try:
        webbrowser.open(url)
    except Exception:
        pass

if __name__ == "__main__":
    port = 8501
    url = f"http://localhost:{port}"
    print("=" * 65)
    print("  FIPP — Facility Issue Prediction & Prioritization")
    print(f"  Live Application: {url}")
    print("  Opening browser automatically...")
    print("  Press Ctrl+C to stop the application.")
    print("=" * 65)

    # Launch browser in a background thread
    threading.Thread(target=open_browser_delayed, args=(url,), daemon=True).start()

    # Launch Streamlit
    cmd = [sys.executable, "-m", "streamlit", "run", "app.py", "--server.port", str(port)]
    subprocess.run(cmd)
