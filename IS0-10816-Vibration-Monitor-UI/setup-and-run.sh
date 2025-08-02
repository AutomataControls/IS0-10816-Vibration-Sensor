#!/bin/bash
# Complete setup script for AutomataNexus Vibration Monitor Desktop App

echo "🚀 AutomataNexus Vibration Monitor Desktop App Setup"
echo "===================================================="

# Check if running on Windows/WSL
if grep -qi microsoft /proc/version 2>/dev/null; then
    echo "📍 Detected: Running on Windows WSL"
    echo ""
fi

# Check Rust installation
if ! command -v cargo &> /dev/null; then
    echo "❌ Rust is not installed"
    echo ""
    echo "Please install Rust first:"
    echo "  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"
    echo ""
    echo "After installing Rust, run this script again."
    exit 1
else
    echo "✅ Rust is installed: $(cargo --version)"
fi

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed"
    echo "Please install Node.js 16+ first"
    exit 1
else
    echo "✅ Node.js is installed: $(node --version)"
fi

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
npm install

# Check for Python backend
echo ""
echo "🔍 Checking for backend API..."
if curl -s http://localhost:5000/api/status > /dev/null 2>&1; then
    echo "✅ Backend API is running at http://localhost:5000"
else
    echo "⚠️  Backend API not detected at http://localhost:5000"
    echo ""
    echo "To start the backend:"
    echo "  1. cd to your vibration sensor directory"
    echo "  2. python universal_vibration_monitor.py"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create icon placeholders if missing
if [ ! -f "src-tauri/icons/icon.png" ] || [ ! -s "src-tauri/icons/icon.png" ]; then
    echo ""
    echo "🎨 Creating placeholder icons..."
    
    # Create a simple SVG icon
    cat > src-tauri/icons/icon.svg << 'EOF'
<svg width="512" height="512" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#14b8a6;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#f97316;stop-opacity:1" />
    </linearGradient>
  </defs>
  <rect width="512" height="512" rx="100" fill="url(#grad)"/>
  <text x="256" y="300" text-anchor="middle" fill="white" font-size="200" font-family="Arial">AN</text>
</svg>
EOF

    # Convert SVG to PNG if ImageMagick is available
    if command -v convert &> /dev/null; then
        convert -background none src-tauri/icons/icon.svg -resize 512x512 src-tauri/icons/icon.png
        convert src-tauri/icons/icon.png -resize 32x32 src-tauri/icons/32x32.png
        convert src-tauri/icons/icon.png -resize 128x128 src-tauri/icons/128x128.png
        convert src-tauri/icons/icon.png -resize 256x256 "src-tauri/icons/128x128@2x.png"
        
        # Create ICO for Windows
        convert src-tauri/icons/icon.png -resize 256x256 src-tauri/icons/icon.ico
        
        echo "✅ Icons created"
    else
        echo "⚠️  ImageMagick not found - using placeholder files"
        # Create empty files
        echo "" > src-tauri/icons/icon.png
        echo "" > src-tauri/icons/32x32.png
        echo "" > src-tauri/icons/128x128.png
        echo "" > "src-tauri/icons/128x128@2x.png"
        echo "" > src-tauri/icons/icon.ico
        echo "" > src-tauri/icons/icon.icns
    fi
fi

echo ""
echo "🚀 Starting Tauri development server..."
echo "===================================="
echo ""
echo "The desktop app will open in a new window."
echo "Press Ctrl+C to stop the development server."
echo ""

# Run the development server
npm run dev