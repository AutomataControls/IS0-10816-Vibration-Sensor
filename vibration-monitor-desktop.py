#!/usr/bin/env python3
"""
AutomataNexus Vibration Monitor Desktop Application
Launches the Flask backend and opens the UI in a native window
"""

import os
import sys
import time
import threading
import webbrowser
import subprocess
from multiprocessing import Process

# Import the Flask app
from multi_port_vibration_monitor import app, monitor_instance

def run_flask_backend():
    """Run the Flask backend server"""
    print("Starting vibration monitoring backend...")
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)

def open_desktop_ui():
    """Open the UI in the default browser or Tauri if available"""
    time.sleep(2)  # Wait for Flask to start
    
    # Check if Tauri app exists
    tauri_path = os.path.join(os.path.dirname(__file__), 
                             "IS0-10816-Vibration-Monitor-UI", 
                             "src-tauri", "target", "release", 
                             "IS0-10816-Vibration-Monitor-UI.exe")
    
    if os.path.exists(tauri_path):
        print("Launching Tauri desktop application...")
        subprocess.Popen([tauri_path])
    else:
        # Fallback to browser
        print("Opening in web browser...")
        # Open the local HTML file that connects to Flask backend
        html_path = os.path.join(os.path.dirname(__file__), 
                                "IS0-10816-Vibration-Monitor-UI", 
                                "src", "index.html")
        webbrowser.open(f"file:///{html_path}")

def main():
    """Main entry point"""
    print("=" * 60)
    print("AutomataNexus Vibration Monitor")
    print("Professional Industrial Monitoring System")
    print("(c) 2025 AutomataNexus AI & AutomataControls")
    print("=" * 60)
    print()
    
    # Start Flask backend in a separate process
    backend_process = Process(target=run_flask_backend)
    backend_process.start()
    
    # Open the UI
    ui_thread = threading.Thread(target=open_desktop_ui)
    ui_thread.start()
    
    try:
        # Keep the main thread alive
        backend_process.join()
    except KeyboardInterrupt:
        print("\nShutting down...")
        backend_process.terminate()
        sys.exit(0)

if __name__ == "__main__":
    main()