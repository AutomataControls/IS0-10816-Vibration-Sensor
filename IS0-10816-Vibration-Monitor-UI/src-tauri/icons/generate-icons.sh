#!/bin/bash
# Generate all required icon sizes for Tauri from the source logo

# Check if ImageMagick is installed
if ! command -v convert &> /dev/null; then
    echo "ImageMagick is required but not installed. Please install it:"
    echo "sudo apt-get install imagemagick"
    exit 1
fi

# Generate PNG icons
echo "Generating PNG icons..."
convert source-logo.png -resize 32x32 32x32.png
convert source-logo.png -resize 128x128 128x128.png
convert source-logo.png -resize 256x256 128x128@2x.png
convert source-logo.png -resize 512x512 icon.png

# Generate ICO for Windows
echo "Generating Windows ICO..."
convert source-logo.png -resize 16x16 icon-16.png
convert source-logo.png -resize 32x32 icon-32.png
convert source-logo.png -resize 48x48 icon-48.png
convert source-logo.png -resize 64x64 icon-64.png
convert source-logo.png -resize 128x128 icon-128.png
convert source-logo.png -resize 256x256 icon-256.png
convert icon-16.png icon-32.png icon-48.png icon-64.png icon-128.png icon-256.png icon.ico
rm icon-16.png icon-32.png icon-48.png icon-64.png icon-128.png icon-256.png

# Generate ICNS for macOS (if on Mac)
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Generating macOS ICNS..."
    mkdir icon.iconset
    convert source-logo.png -resize 16x16 icon.iconset/icon_16x16.png
    convert source-logo.png -resize 32x32 icon.iconset/icon_16x16@2x.png
    convert source-logo.png -resize 32x32 icon.iconset/icon_32x32.png
    convert source-logo.png -resize 64x64 icon.iconset/icon_32x32@2x.png
    convert source-logo.png -resize 128x128 icon.iconset/icon_128x128.png
    convert source-logo.png -resize 256x256 icon.iconset/icon_128x128@2x.png
    convert source-logo.png -resize 256x256 icon.iconset/icon_256x256.png
    convert source-logo.png -resize 512x512 icon.iconset/icon_256x256@2x.png
    convert source-logo.png -resize 512x512 icon.iconset/icon_512x512.png
    convert source-logo.png -resize 1024x1024 icon.iconset/icon_512x512@2x.png
    iconutil -c icns icon.iconset
    rm -rf icon.iconset
else
    echo "Skipping ICNS generation (not on macOS)"
    # Create a placeholder for Linux/Windows builds
    cp icon.png icon.icns
fi

echo "Icon generation complete!"
ls -la *.png *.ico *.icns 2>/dev/null