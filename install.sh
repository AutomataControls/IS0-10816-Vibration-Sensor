#!/bin/bash
# AutomataNexus Vibration Monitor - Master Installer
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
        if ! python3 -c "import PIL" 2>/dev/null; then
            echo "Installing image processing library..."
            sudo apt install -y python3-pil python3-pil.imagetk 2>/dev/null || true
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