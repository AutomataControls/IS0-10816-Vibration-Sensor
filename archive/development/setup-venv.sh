#!/bin/bash
# Setup Python virtual environment for AutomataNexus Vibration Monitor

echo "🐍 Setting up Python Virtual Environment"
echo "======================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Create virtual environment
echo -e "${YELLOW}Creating virtual environment...${NC}"
python3 -m venv venv

if [ ! -d "venv" ]; then
    echo -e "${RED}✗ Failed to create virtual environment${NC}"
    echo "You may need to install: sudo apt-get install python3-venv"
    exit 1
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Upgrade pip
echo -e "${YELLOW}Upgrading pip...${NC}"
python -m pip install --upgrade pip

# Install requirements
echo -e "${YELLOW}Installing requirements...${NC}"
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ Virtual environment setup complete!${NC}"
    echo ""
    echo "To use the virtual environment:"
    echo "  source venv/bin/activate"
    echo "  python universal_vibration_monitor.py"
    echo ""
    echo "Or just run:"
    echo "  ./start-all.sh"
else
    echo -e "${RED}✗ Failed to install dependencies${NC}"
    exit 1
fi