#!/bin/bash
# Fix PIL ImageTk import issue on Raspberry Pi

echo "Fixing PIL ImageTk import issue..."
echo "================================"
echo

# Install required development packages for PIL
echo "Installing image library dependencies..."
sudo apt install -y \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libopenjp2-7-dev \
    libtiff5-dev \
    tk-dev \
    tcl-dev \
    libharfbuzz-dev \
    libfribidi-dev \
    libxcb1-dev

# Reinstall python3-pil.imagetk
echo "Reinstalling PIL packages..."
sudo apt install --reinstall -y python3-pil python3-pil.imagetk

# Test the import
echo
echo "Testing PIL import..."
python3 -c "
try:
    from PIL import Image, ImageTk
    print('✓ PIL ImageTk import successful!')
except Exception as e:
    print('✗ PIL ImageTk import failed:', e)
"

echo
echo "If the import still fails, the GUI installer will fall back to CLI mode."
echo "You can now run: ./install.sh"