#!/bin/bash
################################################################################
# AutomataNexus Vibration Monitor - Development Cleanup Script
# Removes all traces including test data and development files
################################################################################

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'
BOLD='\033[1m'

echo -e "${CYAN}${BOLD}AutomataNexus Vibration Monitor - Complete Cleanup${NC}"
echo -e "${CYAN}===================================================${NC}"
echo
echo -e "${YELLOW}${BOLD}WARNING:${NC} This will remove ALL files including:"
echo "  • All CSV data files"
echo "  • Configuration files"
echo "  • Python cache files"
echo "  • Database files"
echo "  • Generated desktop files"
echo "  • Node-RED package files"
echo

read -p "Are you SURE you want to remove everything? (yes/no): " confirm

if [[ "$confirm" != "yes" ]]; then
    echo "Cleanup cancelled."
    exit 0
fi

echo
echo -e "${BLUE}Starting cleanup...${NC}"

# Stop service if running
echo -e "${BLUE}▸${NC} Stopping service..."
sudo systemctl stop vibration-monitor 2>/dev/null || true
sudo systemctl disable vibration-monitor 2>/dev/null || true
sudo rm -f /etc/systemd/system/vibration-monitor.service
sudo systemctl daemon-reload

# Remove from standard installation locations
echo -e "${BLUE}▸${NC} Removing installation directories..."
sudo rm -rf /opt/automatanexus-vibration-monitor 2>/dev/null
sudo rm -rf /opt/automatanexus/IS0-10816-Vibration-Sensor 2>/dev/null
sudo rm -rf /opt/automatanexus 2>/dev/null

# Clean current directory if we're in the repo
if [[ "$PWD" == *"IS0-10816-Vibration-Sensor"* ]]; then
    echo -e "${BLUE}▸${NC} Cleaning current directory..."
    
    # Remove all CSV files
    echo "  Removing CSV files..."
    rm -f *.csv
    
    # Remove Python cache
    echo "  Removing Python cache..."
    rm -rf __pycache__
    rm -rf .pytest_cache
    
    # Remove config files
    echo "  Removing config files..."
    rm -f equipment_config.json
    rm -f sensor_config.json
    rm -f .vibration_monitor_config.json
    
    # Remove database
    echo "  Removing database..."
    rm -f vibration_monitor.db
    rm -f *.db
    
    # Remove generated files
    echo "  Removing generated files..."
    rm -f vibration-monitor.service
    rm -f vibration-monitor.desktop
    rm -f *.desktop
    
    # Remove log files
    echo "  Removing log files..."
    rm -f *.log
    
    # Remove any .pyc files
    find . -name "*.pyc" -delete 2>/dev/null
    find . -name "*.pyo" -delete 2>/dev/null
fi

# Remove from home directory
echo -e "${BLUE}▸${NC} Cleaning home directory..."
rm -f ~/.vibration_monitor_config.json
rm -f ~/vibration_monitor.db
rm -f ~/vibration_monitor.log
rm -f ~/Desktop/vibration-monitor.desktop
rm -f ~/.local/share/applications/vibration-monitor.desktop

# Remove Node-RED package
echo -e "${BLUE}▸${NC} Checking Node-RED package..."
if [ -d ~/.node-red ]; then
    cd ~/.node-red
    npm uninstall node-red-contrib-automatanexus-hvac-vibration 2>/dev/null || true
    cd - > /dev/null
fi

# List remaining files
echo
echo -e "${YELLOW}Remaining files in current directory:${NC}"
ls -la | grep -v "^total" | grep -v "^d" | grep -v ".git" | grep -v ".py$" | grep -v ".sh$" | grep -v ".md$" | grep -v ".txt$" | grep -v ".html$" | grep -v ".json$" | grep -v ".png$"

echo
echo -e "${GREEN}${BOLD}Cleanup complete!${NC}"
echo
echo "The following have been removed:"
echo "  ✓ System service and configuration"
echo "  ✓ All CSV data files"
echo "  ✓ Python cache and compiled files"
echo "  ✓ Configuration and database files"
echo "  ✓ Desktop shortcuts"
echo "  ✓ Installation directories"
echo
echo -e "${BOLD}Only source code files remain.${NC}"