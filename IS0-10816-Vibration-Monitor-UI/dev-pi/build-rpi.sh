#!/bin/bash
# Build script for Raspberry Pi (ARM processors)
# Run this ON the Raspberry Pi itself

echo "AutomataNexus Vibration Monitor - Raspberry Pi Build"
echo "====================================================="

# Check if running on ARM
if [[ $(uname -m) != arm* ]] && [[ $(uname -m) != aarch64 ]]; then
    echo "Warning: Not running on ARM architecture ($(uname -m))"
    echo "This script should be run directly on the Raspberry Pi"
fi

# Install Rust if not present
if ! command -v cargo &> /dev/null; then
    echo "Installing Rust..."
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
    source $HOME/.cargo/env
fi

# Install Node.js if not present
if ! command -v node &> /dev/null; then
    echo "Installing Node.js..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt-get install -y nodejs
fi

# Install system dependencies
echo "Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y \
    libwebkit2gtk-4.0-dev \
    build-essential \
    curl \
    wget \
    libssl-dev \
    libgtk-3-dev \
    libayatana-appindicator3-dev \
    librsvg2-dev \
    libjavascriptcoregtk-4.0-dev \
    libsoup2.4-dev

# Install Tauri CLI
echo "Installing dependencies..."
npm install

# Build the app
echo "Building for Raspberry Pi..."
npm run build

echo ""
echo "Build complete! The application bundle is located at:"
echo "src-tauri/target/release/bundle/"
echo ""
echo "To run the app directly: ./src-tauri/target/release/automatanexus-vibration-monitor"