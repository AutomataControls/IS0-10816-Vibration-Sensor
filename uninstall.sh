#!/bin/bash
################################################################################
# AutomataNexus Vibration Monitor - Professional Uninstaller
# Enterprise-Grade Component Removal with Safety Checks
################################################################################
#
# © 2025 AutomataNexus AI & AutomataControls. All rights reserved.
#
# COMMERCIAL LICENSE NOTICE:
# This software is commercially licensed, not open source. For licensing inquiries,
# contact DevOps@automatacontrols.com. See COMMERCIAL.md for full license terms.
################################################################################

# Color codes for professional output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Function to print colored output
print_header() {
    echo -e "${CYAN}${BOLD}$1${NC}"
    echo -e "${CYAN}$(printf '=%.0s' {1..60})${NC}"
}

print_step() {
    echo -e "${BLUE}▸${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Main header
clear
print_header "AutomataNexus Vibration Monitor - Professional Uninstaller"
echo -e "${BOLD}Version:${NC} 3.0.0"
echo -e "${BOLD}License:${NC} Commercial (See COMMERCIAL.md)"
echo

# Warning message
echo -e "${YELLOW}${BOLD}WARNING:${NC} This will permanently remove the following components:"
echo -e "  • Vibration monitor system service"
echo -e "  • Application files from /opt/automatanexus-vibration-monitor"
echo -e "  • Configuration files and settings"
echo -e "  • Database with historical vibration data"
echo -e "  • Node-RED integration package"
echo -e "  • Desktop shortcuts and menu entries"
echo -e "  • Log files and temporary data"
echo

# Interactive component selection
echo -e "${BOLD}Select components to remove:${NC}"
echo

# Default all to yes
REMOVE_SERVICE="y"
REMOVE_FILES="y"
REMOVE_CONFIG="y"
REMOVE_DATABASE="y"
REMOVE_NODERED="y"
REMOVE_DESKTOP="y"
REMOVE_LOGS="y"

read -p "Remove system service? [Y/n]: " response
[[ "$response" =~ ^[Nn]$ ]] && REMOVE_SERVICE="n"

read -p "Remove application files? [Y/n]: " response
[[ "$response" =~ ^[Nn]$ ]] && REMOVE_FILES="n"

read -p "Remove configuration files? [Y/n]: " response
[[ "$response" =~ ^[Nn]$ ]] && REMOVE_CONFIG="n"

read -p "Remove database (cannot be recovered)? [Y/n]: " response
[[ "$response" =~ ^[Nn]$ ]] && REMOVE_DATABASE="n"

read -p "Remove Node-RED package? [Y/n]: " response
[[ "$response" =~ ^[Nn]$ ]] && REMOVE_NODERED="n"

read -p "Remove desktop shortcuts? [Y/n]: " response
[[ "$response" =~ ^[Nn]$ ]] && REMOVE_DESKTOP="n"

read -p "Remove log files? [Y/n]: " response
[[ "$response" =~ ^[Nn]$ ]] && REMOVE_LOGS="n"

echo
echo -e "${BOLD}Final confirmation:${NC}"
read -p "Proceed with uninstallation? (y/N): " confirm

if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    print_warning "Uninstallation cancelled by user"
    exit 0
fi

echo
print_header "Beginning Uninstallation Process"
echo

# Progress tracking
TOTAL_STEPS=0
CURRENT_STEP=0

# Count selected steps
[[ "$REMOVE_SERVICE" == "y" ]] && ((TOTAL_STEPS++))
[[ "$REMOVE_FILES" == "y" ]] && ((TOTAL_STEPS++))
[[ "$REMOVE_CONFIG" == "y" ]] && ((TOTAL_STEPS++))
[[ "$REMOVE_DATABASE" == "y" ]] && ((TOTAL_STEPS++))
[[ "$REMOVE_NODERED" == "y" ]] && ((TOTAL_STEPS++))
[[ "$REMOVE_DESKTOP" == "y" ]] && ((TOTAL_STEPS++))
[[ "$REMOVE_LOGS" == "y" ]] && ((TOTAL_STEPS++))

# Function to show progress
show_progress() {
    ((CURRENT_STEP++))
    local percentage=$((CURRENT_STEP * 100 / TOTAL_STEPS))
    echo -e "${BOLD}Progress: [$CURRENT_STEP/$TOTAL_STEPS] ${percentage}%${NC}"
}

# Stop the service if selected
if [[ "$REMOVE_SERVICE" == "y" ]]; then
    print_step "Stopping vibration monitor service..."
    if sudo systemctl stop vibration-monitor 2>/dev/null; then
        print_success "Service stopped"
    else
        print_warning "Service was not running"
    fi
    
    if sudo systemctl disable vibration-monitor 2>/dev/null; then
        print_success "Service disabled"
    fi
    
    sudo rm -f /etc/systemd/system/vibration-monitor.service
    sudo systemctl daemon-reload
    print_success "Service removed"
    show_progress
    echo
fi

# Remove application files if selected
if [[ "$REMOVE_FILES" == "y" ]]; then
    print_step "Removing application files..."
    removed=0
    
    # Check multiple possible locations
    if [ -d "/opt/automatanexus-vibration-monitor" ]; then
        sudo rm -rf /opt/automatanexus-vibration-monitor
        ((removed++))
    fi
    
    if [ -d "/opt/automatanexus/IS0-10816-Vibration-Sensor" ]; then
        sudo rm -rf /opt/automatanexus/IS0-10816-Vibration-Sensor
        ((removed++))
    fi
    
    # Check if we're in the installation directory
    if [[ "$PWD" == *"IS0-10816-Vibration-Sensor"* ]]; then
        print_warning "Currently in installation directory - cannot remove"
        print_step "Cleaning up data files instead..."
        # Remove all CSV files
        rm -f *.csv 2>/dev/null
        # Remove cache and compiled files
        rm -rf __pycache__ 2>/dev/null
        # Remove config files
        rm -f equipment_config.json sensor_config.json 2>/dev/null
        # Remove service files
        rm -f vibration-monitor.service 2>/dev/null
        # Remove desktop files
        rm -f vibration-monitor.desktop 2>/dev/null
        print_success "Cleaned up data and config files"
    elif [ $removed -eq 0 ]; then
        print_warning "No installation directories found"
    else
        print_success "Application files removed"
    fi
    
    show_progress
    echo
fi

# Remove configuration if selected
if [[ "$REMOVE_CONFIG" == "y" ]]; then
    print_step "Removing configuration files..."
    removed=0
    
    if [ -f ~/.vibration_monitor_config.json ]; then
        rm -f ~/.vibration_monitor_config.json
        ((removed++))
    fi
    
    if [ $removed -gt 0 ]; then
        print_success "Configuration files removed"
    else
        print_warning "No configuration files found"
    fi
    show_progress
    echo
fi

# Remove database if selected
if [[ "$REMOVE_DATABASE" == "y" ]]; then
    print_step "Removing database files..."
    removed=0
    
    if [ -f ~/vibration_monitor.db ]; then
        rm -f ~/vibration_monitor.db
        ((removed++))
    fi
    
    if [ -f /opt/automatanexus-vibration-monitor/vibration_monitor.db ]; then
        sudo rm -f /opt/automatanexus-vibration-monitor/vibration_monitor.db
        ((removed++))
    fi
    
    if [ -f /opt/automatanexus/IS0-10816-Vibration-Sensor/vibration_monitor.db ]; then
        sudo rm -f /opt/automatanexus/IS0-10816-Vibration-Sensor/vibration_monitor.db
        ((removed++))
    fi
    
    # Check current directory
    if [ -f vibration_monitor.db ]; then
        rm -f vibration_monitor.db
        ((removed++))
    fi
    
    if [ $removed -gt 0 ]; then
        print_success "Database files removed"
    else
        print_warning "No database files found"
    fi
    show_progress
    echo
fi

# Remove Node-RED package if selected
if [[ "$REMOVE_NODERED" == "y" ]]; then
    print_step "Removing Node-RED package..."
    
    if command -v npm &> /dev/null; then
        # Check global installation
        if npm list -g node-red-contrib-automatanexus-hvac-vibration &> /dev/null; then
            print_step "Removing global Node-RED package..."
            sudo npm uninstall -g node-red-contrib-automatanexus-hvac-vibration
            print_success "Global package removed"
        fi
        
        # Check local installation
        if [ -d ~/.node-red ]; then
            cd ~/.node-red
            if npm list node-red-contrib-automatanexus-hvac-vibration &> /dev/null; then
                print_step "Removing local Node-RED package..."
                npm uninstall node-red-contrib-automatanexus-hvac-vibration
                print_success "Local package removed"
            fi
            cd - > /dev/null
        fi
    else
        print_warning "npm not found - skipping Node-RED package removal"
    fi
    show_progress
    echo
fi

# Remove desktop shortcuts if selected
if [[ "$REMOVE_DESKTOP" == "y" ]]; then
    print_step "Removing desktop shortcuts..."
    removed=0
    
    if [ -f ~/Desktop/vibration-monitor.desktop ]; then
        rm -f ~/Desktop/vibration-monitor.desktop
        ((removed++))
    fi
    
    if [ -f ~/.local/share/applications/vibration-monitor.desktop ]; then
        rm -f ~/.local/share/applications/vibration-monitor.desktop
        ((removed++))
    fi
    
    if [ $removed -gt 0 ]; then
        print_success "Desktop shortcuts removed"
    else
        print_warning "No desktop shortcuts found"
    fi
    show_progress
    echo
fi

# Remove log files if selected
if [[ "$REMOVE_LOGS" == "y" ]]; then
    print_step "Removing log files..."
    removed=0
    
    if [ -d /var/log/vibration-monitor ]; then
        sudo rm -rf /var/log/vibration-monitor
        ((removed++))
    fi
    
    if [ -f ~/vibration_monitor.log ]; then
        rm -f ~/vibration_monitor.log
        ((removed++))
    fi
    
    if [ $removed -gt 0 ]; then
        print_success "Log files removed"
    else
        print_warning "No log files found"
    fi
    show_progress
    echo
fi

# Clean up PATH
print_step "Cleaning environment..."
sed -i '/automatanexus-vibration-monitor/d' ~/.bashrc 2>/dev/null || true
sed -i '/automatanexus-vibration-monitor/d' ~/.profile 2>/dev/null || true
print_success "Environment cleaned"

echo
print_header "Uninstallation Complete"
echo

echo -e "${GREEN}${BOLD}Successfully removed selected components:${NC}"
[[ "$REMOVE_SERVICE" == "y" ]] && echo -e "  ${GREEN}✓${NC} System service"
[[ "$REMOVE_FILES" == "y" ]] && echo -e "  ${GREEN}✓${NC} Application files"
[[ "$REMOVE_CONFIG" == "y" ]] && echo -e "  ${GREEN}✓${NC} Configuration files"
[[ "$REMOVE_DATABASE" == "y" ]] && echo -e "  ${GREEN}✓${NC} Database files"
[[ "$REMOVE_NODERED" == "y" ]] && echo -e "  ${GREEN}✓${NC} Node-RED package"
[[ "$REMOVE_DESKTOP" == "y" ]] && echo -e "  ${GREEN}✓${NC} Desktop shortcuts"
[[ "$REMOVE_LOGS" == "y" ]] && echo -e "  ${GREEN}✓${NC} Log files"

echo
echo -e "${BOLD}To reinstall AutomataNexus Vibration Monitor:${NC}"
echo -e "${CYAN}git clone https://github.com/AutomataControls/IS0-10816-Vibration-Sensor.git${NC}"
echo -e "${CYAN}cd IS0-10816-Vibration-Sensor${NC}"
echo -e "${CYAN}./install.sh${NC}"
echo
echo -e "${BOLD}Thank you for using AutomataNexus Vibration Monitor!${NC}"