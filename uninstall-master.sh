#!/bin/bash
################################################################################
# AutomataNexus Vibration Monitor - Master Uninstaller
# Automatically chooses GUI or CLI uninstallation
################################################################################
#
# © 2025 AutomataNexus AI & AutomataControls. All rights reserved.
#
# COMMERCIAL LICENSE NOTICE:
# This software is commercially licensed, not open source. For licensing inquiries,
# contact DevOps@automatacontrols.com. See COMMERCIAL.md for full license terms.
################################################################################

echo "AutomataNexus Vibration Monitor Uninstaller"
echo "==========================================="
echo

# Check if we have a display
if [ -n "$DISPLAY" ]; then
    echo "Display detected. Checking for GUI requirements..."
    
    # Check if tkinter is available
    if python3 -c "import tkinter" 2>/dev/null; then
        echo "Starting GUI uninstaller..."
        
        # Make sure GUI uninstaller is executable
        chmod +x uninstall-gui.py
        
        # Run GUI uninstaller
        python3 uninstall-gui.py
    else
        echo "GUI libraries not found. Falling back to CLI uninstaller..."
        echo
        
        # Make sure CLI uninstaller is executable
        chmod +x uninstall.sh
        
        # Run CLI uninstaller
        ./uninstall.sh
    fi
else
    echo "No display detected. Starting CLI uninstaller..."
    echo
    
    # Make sure CLI uninstaller is executable
    chmod +x uninstall.sh
    
    # Run CLI uninstaller
    ./uninstall.sh
fi