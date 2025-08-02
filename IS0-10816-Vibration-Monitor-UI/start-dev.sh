#!/bin/bash
# Development server for AutomataNexus Vibration Monitor UI

echo "🚀 Starting AutomataNexus Vibration Monitor in development mode..."

# Check if the Python backend is running
if ! curl -s http://localhost:5000/api/status > /dev/null 2>&1; then
    echo "⚠️  Warning: Backend API not responding at http://localhost:5000"
    echo "   Make sure to run: python universal_vibration_monitor.py"
    echo ""
fi

# Start Tauri dev server
npm run dev