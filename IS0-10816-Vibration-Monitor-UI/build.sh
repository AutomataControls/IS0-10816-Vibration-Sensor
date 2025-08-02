#!/bin/bash
# AutomataNexus Vibration Monitor UI Build Script

echo "🚀 Building AutomataNexus Vibration Monitor Desktop App..."

# Check if Rust is installed
if ! command -v cargo &> /dev/null; then
    echo "❌ Rust is not installed. Please install from https://rustup.rs/"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 16+"
    exit 1
fi

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Create placeholder icons if they don't exist
if [ ! -f "src-tauri/icons/icon.png" ]; then
    echo "🎨 Creating placeholder icons..."
    # Create a simple gradient icon using ImageMagick if available
    if command -v convert &> /dev/null; then
        convert -size 512x512 gradient:'#14b8a6-#f97316' src-tauri/icons/icon.png
        convert src-tauri/icons/icon.png -resize 32x32 src-tauri/icons/32x32.png
        convert src-tauri/icons/icon.png -resize 128x128 src-tauri/icons/128x128.png
        convert src-tauri/icons/icon.png -resize 256x256 src-tauri/icons/128x128@2x.png
    else
        echo "⚠️  ImageMagick not found. Please add icon files manually."
        echo "   Required: icon.png, 32x32.png, 128x128.png, 128x128@2x.png"
        # Create empty files as placeholders
        touch src-tauri/icons/icon.png
        touch src-tauri/icons/32x32.png
        touch src-tauri/icons/128x128.png
        touch src-tauri/icons/128x128@2x.png
        touch src-tauri/icons/icon.ico
        touch src-tauri/icons/icon.icns
    fi
fi

# Build the application
echo "🔨 Building Tauri application..."
npm run build

echo "✅ Build complete! Check src-tauri/target/release/bundle/"