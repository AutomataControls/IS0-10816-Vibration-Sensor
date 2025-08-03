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

# Always install dependencies first
echo "Installing required dependencies..."
sudo apt update
sudo apt install -y \
    python3-tk \
    python3-pil \
    python3-pil.imagetk \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    tk-dev

# Reinstall PIL packages to ensure proper setup
sudo apt install --reinstall -y python3-pil python3-pil.imagetk

# Check if we have a display
if [ -n "$DISPLAY" ]; then
    echo "Display detected. Checking GUI requirements..."
    
    # Test if imports work
    if python3 -c "import tkinter; from PIL import Image, ImageTk" 2>/dev/null; then
        echo "GUI requirements satisfied. Starting GUI installer..."
        
        # Make sure GUI installer is executable
        chmod +x install-gui.py
        
        # Run GUI installer
        python3 install-gui.py
    else
        echo "GUI requirements not met. Using CLI installer..."
        bash install-on-pi.sh
    fi
else
    echo "No display detected. Running CLI installer..."
    bash install-on-pi.sh
fi