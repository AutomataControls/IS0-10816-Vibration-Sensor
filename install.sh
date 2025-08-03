#!/bin/bash
################################################################################
# AutomataNexus Vibration Monitor - Master Installer
# Enterprise-Grade ISO 10816-3 Compliant Vibration Analysis Platform
################################################################################
#
# © 2025 AutomataNexus AI & AutomataControls. All rights reserved.
#
# COMMERCIAL LICENSE NOTICE:
# This software is commercially licensed, not open source. For licensing inquiries,
# contact DevOps@automatacontrols.com. See COMMERCIAL.md for full license terms.
#
# Automatically chooses GUI or CLI installation

echo "AutomataNexus Vibration Monitor Installer"
echo "========================================="
echo

# Check if we have a display
if [ -n "$DISPLAY" ]; then
    echo "Display detected. Checking for GUI requirements..."
    
    # Check if tkinter is available
    if python3 -c "import tkinter" 2>/dev/null; then
        echo "Starting GUI installer..."
        
        # Install PIL if needed (for logo handling)
        if ! python3 -c "from PIL import ImageTk" 2>/dev/null; then
            echo "Installing image processing libraries..."
            sudo apt update
            sudo apt install -y python3-pil python3-pil.imagetk
            
            # If still not working, try pip
            if ! python3 -c "from PIL import ImageTk" 2>/dev/null; then
                echo "Installing via pip..."
                sudo pip3 install --upgrade Pillow
            fi
        fi
        
        # Make sure GUI installer is executable
        chmod +x install-gui.py
        
        # Run GUI installer
        python3 install-gui.py
    else
        echo "GUI libraries not found. Installing..."
        sudo apt install -y python3-tk python3-pil python3-pil.imagetk
        
        # Try again
        if python3 -c "import tkinter" 2>/dev/null; then
            python3 install-gui.py
        else
            echo "GUI installation failed. Falling back to CLI installer..."
            bash install-on-pi.sh
        fi
    fi
else
    echo "No display detected. Running CLI installer..."
    bash install-on-pi.sh
fi