"""
Launcher script for FIPP — Facility Issue Prediction & Prioritization.
Starts the FastAPI application with Uvicorn on an available local port.
"""

import socket
import threading
import time
import webbrowser
import uvicorn

def is_port_available(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) != 0

def find_open_port(preferred_port: int = 8000) -> int:
    port = preferred_port
    while port < preferred_port + 20:
        if is_port_available(port):
            return port
        port += 1
    return preferred_port

def open_browser_delayed(url: str):
    time.sleep(1.2)
    try:
        webbrowser.open(url)
    except Exception:
        pass

if __name__ == "__main__":
    port = find_open_port(8000)
    url = f"http://127.0.0.1:{port}"
    print("=" * 65)
    print("  FIPP — Facility Issue Prediction & Prioritization")
    print(f"  Live Server: {url}")
    print("  Opening browser automatically...")
    print("  Press Ctrl+C to stop the server.")
    print("=" * 65)

    # Launch browser in a background thread
    threading.Thread(target=open_browser_delayed, args=(url,), daemon=True).start()

    uvicorn.run("app.main:app", host="127.0.0.1", port=port, reload=False)
