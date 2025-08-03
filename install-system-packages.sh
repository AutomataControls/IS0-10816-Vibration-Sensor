#!/bin/bash
# Install system packages for AutomataNexus Vibration Monitor

echo "📦 Installing System Packages for Vibration Monitor"
echo "=================================================="
echo ""
echo "This script will automatically install all required packages."
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${YELLOW}Installing required system packages...${NC}"
echo ""

# Update package list
echo -e "${BLUE}Updating package list...${NC}"
sudo apt-get update

# Install all required packages including GUI dependencies
echo -e "${BLUE}Installing Python packages and GUI dependencies...${NC}"
sudo apt-get install -y \
    python3-numpy \
    python3-scipy \
    python3-pandas \
    python3-flask \
    python3-flask-cors \
    python3-serial \
    python3-dotenv \
    python3-tk \
    python3-pil \
    python3-pil.imagetk \
    python3-pip \
    sqlite3

# For Raspberry Pi GPIO support
if [ -f /proc/device-tree/model ] && grep -q "Raspberry Pi" /proc/device-tree/model; then
    echo -e "${BLUE}Detected Raspberry Pi - Installing GPIO support...${NC}"
    sudo apt-get install -y python3-rpi.gpio
fi

echo ""

# Check what's already installed
echo -e "${YELLOW}Currently installed:${NC}"
python3 -c "
import importlib
packages = {
    'numpy': 'numpy',
    'scipy': 'scipy', 
    'pandas': 'pandas',
    'flask': 'Flask',
    'flask_cors': 'Flask-CORS',
    'serial': 'pyserial',
    'dotenv': 'python-dotenv'
}

for name, display in packages.items():
    try:
        importlib.import_module(name)
        print(f'✓ {display}')
    except ImportError:
        print(f'✗ {display} - NOT INSTALLED')
"

echo ""
echo "After installing packages, run:"
echo "  ./start-all.sh"