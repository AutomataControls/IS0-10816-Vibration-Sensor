#!/bin/bash
# Setup all dependencies for AutomataNexus Vibration Monitor

echo "🔧 AutomataNexus Vibration Monitor - Dependency Setup"
echo "===================================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 is not installed${NC}"
    echo "Please install Python 3 first:"
    echo "  sudo apt-get install python3"
    exit 1
else
    echo -e "${GREEN}✓ Python 3 found: $(python3 --version)${NC}"
fi

# Check pip
if ! python3 -m pip --version &> /dev/null 2>&1; then
    echo -e "${RED}✗ pip is not installed${NC}"
    echo ""
    echo "Please install pip:"
    echo "  sudo apt-get update"
    echo "  sudo apt-get install python3-pip"
    echo ""
    echo "Or on Windows (in PowerShell as admin):"
    echo "  python -m ensurepip --upgrade"
    exit 1
else
    echo -e "${GREEN}✓ pip found: $(python3 -m pip --version)${NC}"
fi

# Install Python dependencies
echo ""
echo -e "${YELLOW}Installing Python dependencies...${NC}"
echo "This may take a few minutes on first run..."
echo ""

# Use --user flag to avoid permission issues
python3 -m pip install --user -r requirements.txt

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ All Python dependencies installed successfully!${NC}"
else
    echo ""
    echo -e "${RED}✗ Failed to install some dependencies${NC}"
    echo ""
    echo "Common fixes:"
    echo "1. On Raspberry Pi, you might need:"
    echo "   sudo apt-get install python3-numpy python3-scipy python3-pandas"
    echo ""
    echo "2. Or try installing one by one:"
    echo "   python3 -m pip install --user pyserial"
    echo "   python3 -m pip install --user numpy"
    echo "   python3 -m pip install --user scipy"
    echo "   python3 -m pip install --user Flask"
    echo "   python3 -m pip install --user Flask-CORS"
    echo "   python3 -m pip install --user pandas"
    echo "   python3 -m pip install --user python-dotenv"
    echo "   python3 -m pip install --user RPi.GPIO  # Only on Raspberry Pi"
    exit 1
fi

# Check Rust (for Tauri)
echo ""
if ! command -v cargo &> /dev/null; then
    echo -e "${YELLOW}⚠ Rust not installed (needed for desktop app)${NC}"
    echo "To install: curl --proto='=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"
else
    echo -e "${GREEN}✓ Rust found: $(cargo --version)${NC}"
fi

# Check Node.js (for Tauri)
if ! command -v node &> /dev/null; then
    echo -e "${YELLOW}⚠ Node.js not installed (needed for desktop app)${NC}"
else
    echo -e "${GREEN}✓ Node.js found: $(node --version)${NC}"
fi

echo ""
echo "===================================================="
echo -e "${GREEN}Setup complete! You can now run:${NC}"
echo ""
echo "  ./start-all.sh        # Start everything"
echo "  python3 universal_vibration_monitor.py  # Backend only"
echo ""
echo "===================================================="