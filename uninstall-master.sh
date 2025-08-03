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
    
    # Check if tkinter and PIL are available
    if python3 -c "import tkinter" 2>/dev/null; then
        # Try to run GUI uninstaller
        echo "Starting GUI uninstaller..."
        
        # Make sure GUI uninstaller is executable
        chmod +x uninstall-gui.py
        
        # Try to run GUI uninstaller, fall back to CLI if it fails
        if ! python3 uninstall-gui.py 2>/dev/null; then
            echo "GUI uninstaller failed to start. Falling back to CLI uninstaller..."
            echo
            
            # Make sure CLI uninstaller is executable
            chmod +x uninstall.sh
            
            # Run CLI uninstaller
            ./uninstall.sh
        fi
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