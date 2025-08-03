#!/bin/bash
################################################################################
# AutomataNexus Vibration Monitor - Dependency Installer
# Installs all required dependencies before main installation
################################################################################

echo "Installing all dependencies for AutomataNexus Vibration Monitor"
echo "=============================================================="
echo

# Update package list
echo "Updating package list..."
sudo apt update

# Install all required packages
echo "Installing system packages..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-tk \
    python3-pil \
    python3-pil.imagetk \
    python3-numpy \
    python3-scipy \
    python3-pandas \
    python3-flask \
    python3-flask-cors \
    python3-serial \
    python3-dotenv \
    git \
    curl \
    sqlite3

# Fix npm conflict
echo "Fixing npm/nodejs conflicts..."
sudo apt remove -y npm nodejs-legacy 2>/dev/null || true
sudo apt install -y nodejs npm

# Install/upgrade pip packages (skip Pillow since we have it from apt)
echo "Installing Python packages via pip..."
sudo pip3 install --upgrade pip
sudo pip3 install --upgrade pyserial flask flask-cors numpy

# Test imports
echo
echo "Testing Python imports..."
python3 -c "
import sys
print('Python version:', sys.version)
try:
    import tkinter
    print('✓ tkinter')
except: print('✗ tkinter')
try:
    from PIL import Image, ImageTk
    print('✓ PIL with ImageTk')
except: print('✗ PIL with ImageTk')
try:
    import serial
    print('✓ pyserial')
except: print('✗ pyserial')
try:
    import flask
    print('✓ flask')
except: print('✗ flask')
try:
    import numpy
    print('✓ numpy')
except: print('✗ numpy')
"

echo
echo "Dependencies installed! Now run ./install.sh"