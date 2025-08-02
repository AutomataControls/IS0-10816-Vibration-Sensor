#!/bin/bash
# Install system packages for AutomataNexus Vibration Monitor

echo "📦 Installing System Packages for Vibration Monitor"
echo "=================================================="
echo ""
echo "This script will help you install the required packages."
echo "You'll need to run the sudo commands manually."
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${YELLOW}Please run these commands:${NC}"
echo ""
echo -e "${BLUE}# Update package list${NC}"
echo "sudo apt-get update"
echo ""
echo -e "${BLUE}# Install Python packages${NC}"
echo "sudo apt-get install -y python3-numpy python3-scipy python3-pandas python3-flask python3-flask-cors python3-serial python3-dotenv"
echo ""
echo -e "${BLUE}# For Raspberry Pi only:${NC}"
echo "sudo apt-get install -y python3-rpi.gpio"
echo ""
echo -e "${BLUE}# OR, if you prefer virtual environments:${NC}"
echo "sudo apt-get install -y python3-venv"
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