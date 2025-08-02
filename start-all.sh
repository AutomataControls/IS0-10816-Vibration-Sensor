#!/bin/bash
# Start both the Python backend and Tauri frontend

echo "🚀 Starting AutomataNexus Vibration Monitor System"
echo "=================================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check if Python backend is already running
if curl -s http://localhost:5000/api/status > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Backend already running${NC}"
else
    echo -e "${YELLOW}Starting Python backend...${NC}"
    
    # Check for virtual environment
    if [ ! -d "venv" ]; then
        echo -e "${YELLOW}Setting up Python virtual environment...${NC}"
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt || {
            echo -e "${RED}✗ Failed to setup environment${NC}"
            echo "Please run: ./setup-venv.sh"
            exit 1
        }
    else
        # Activate existing venv
        source venv/bin/activate
    fi
    
    # Check Python dependencies
    if ! python -c "import numpy" 2>/dev/null; then
        echo -e "${YELLOW}Installing Python dependencies...${NC}"
        pip install -r requirements.txt
    fi
    echo -e "${GREEN}✓ Python environment ready${NC}"
    
    # Start Python backend in background
    cd "$SCRIPT_DIR"
    if [ -f "universal_vibration_monitor.py" ]; then
        python universal_vibration_monitor.py > backend.log 2>&1 &
        BACKEND_PID=$!
        echo "Backend PID: $BACKEND_PID"
        
        # Wait for backend to start
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
            exit 1
        fi
    else
        echo -e "${RED}✗ universal_vibration_monitor.py not found!${NC}"
        echo "Make sure you're in the right directory"
        exit 1
    fi
fi

echo ""
echo -e "${YELLOW}Starting Tauri UI...${NC}"

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}Shutting down...${NC}"
    if [ ! -z "$BACKEND_PID" ]; then
        echo "Stopping backend (PID: $BACKEND_PID)"
        kill $BACKEND_PID 2>/dev/null
    fi
    exit
}

# Set trap to cleanup on Ctrl+C
trap cleanup INT TERM

# Start Tauri UI
cd "$SCRIPT_DIR/IS0-10816-Vibration-Monitor-UI"
source "$HOME/.cargo/env" 2>/dev/null
npm run dev

# If we get here, Tauri has exited
cleanup