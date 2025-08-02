#!/bin/bash
# Simple start script that doesn't require pip

echo "🚀 Starting AutomataNexus Vibration Monitor System"
echo "=================================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check if Python backend is already running
if curl -s http://localhost:5000/api/status > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Backend already running${NC}"
else
    echo -e "${YELLOW}Starting Python backend...${NC}"
    
    # Quick dependency check
    if ! python3 -c "import numpy" 2>/dev/null; then
        echo -e "${RED}✗ Python dependencies missing!${NC}"
        echo ""
        echo "Please install system packages:"
        echo "  sudo apt-get update"
        echo "  sudo apt-get install -y python3-numpy python3-scipy python3-pandas \\"
        echo "    python3-flask python3-flask-cors python3-serial python3-dotenv"
        echo ""
        echo "Or run: ./install-system-packages.sh"
        exit 1
    fi
    
    # Start Python backend
    cd "$SCRIPT_DIR"
    python3 universal_vibration_monitor.py > backend.log 2>&1 &
    BACKEND_PID=$!
    echo "Backend PID: $BACKEND_PID"
    
    # Wait for backend
    echo -n "Waiting for backend to start"
    for i in {1..30}; do
        if curl -s http://localhost:5000/api/status > /dev/null 2>&1; then
            echo -e "\n${GREEN}✓ Backend started successfully${NC}"
            break
        fi
        echo -n "."
        sleep 1
    done
    
    if ! curl -s http://localhost:5000/api/status > /dev/null 2>&1; then
        echo -e "\n${RED}✗ Backend failed to start. Check backend.log${NC}"
        cat backend.log
        exit 1
    fi
fi

echo ""
echo -e "${YELLOW}Starting Tauri UI...${NC}"

# Cleanup function
cleanup() {
    echo -e "\n${YELLOW}Shutting down...${NC}"
    if [ ! -z "$BACKEND_PID" ]; then
        echo "Stopping backend (PID: $BACKEND_PID)"
        kill $BACKEND_PID 2>/dev/null
    fi
    exit
}

trap cleanup INT TERM

# Start UI
cd "$SCRIPT_DIR/IS0-10816-Vibration-Monitor-UI"
source "$HOME/.cargo/env" 2>/dev/null
npm run dev

cleanup