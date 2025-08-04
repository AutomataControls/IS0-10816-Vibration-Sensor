#!/bin/bash
# Direct build script for Raspberry Pi - bypasses Tauri CLI issues on ARM

echo "======================================================"
echo "  AutomataNexus Vibration Monitor - Pi Direct Build"
echo "======================================================"

# Check if running on ARM
if [[ $(uname -m) != arm* ]] && [[ $(uname -m) != aarch64 ]]; then
    echo "Warning: Not running on ARM architecture ($(uname -m))"
fi

# Install Rust if not present
if ! command -v cargo &> /dev/null; then
    echo "Installing Rust..."
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
    source $HOME/.cargo/env
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
    librsvg2-dev

# Find the project root and navigate to Rust project
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"
cd "$PROJECT_ROOT/src-tauri"

# Build directly with cargo
echo "Building with cargo (this may take a while)..."
cargo build --release

# Check if build succeeded
if [ -f "target/release/automatanexus-vibration-monitor" ]; then
    echo ""
    echo "✅ Build successful!"
    echo ""
    echo "Binary location: src-tauri/target/release/automatanexus-vibration-monitor"
    echo ""
    echo "Creating distributable package..."
    
    # Create package directory
    mkdir -p ../dist
    
    # Copy files for distribution
    cp target/release/automatanexus-vibration-monitor ../dist/
    cp ../dev-pi/install-rpi-binary.sh ../dist/
    cp ../dev-pi/automata-nexus-logo.png ../dist/
    
    # Create tarball
    cd ../dist
    tar -czf automatanexus-vibration-monitor-rpi-$(uname -m).tar.gz \
        automatanexus-vibration-monitor \
        install-rpi-binary.sh \
        automata-nexus-logo.png
    
    echo "📦 Package created: dist/automatanexus-vibration-monitor-rpi-$(uname -m).tar.gz"
    echo ""
    echo "This package can be distributed to users!"
else
    echo "❌ Build failed. Check error messages above."
    exit 1
fi