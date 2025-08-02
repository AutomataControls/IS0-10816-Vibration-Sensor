#!/usr/bin/env python3
"""
Generate all required icon sizes for Tauri from the source logo
Uses Pillow for cross-platform compatibility
"""

import os
import sys
from PIL import Image

def generate_icons():
    """Generate all required icon sizes from source logo"""
    
    source_file = "source-logo.png"
    
    if not os.path.exists(source_file):
        print(f"Error: {source_file} not found!")
        print("Please ensure the logo is in the current directory")
        return False
    
    try:
        # Open the source image
        img = Image.open(source_file)
        
        # Convert to RGBA if not already
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # Generate PNG icons
        print("Generating PNG icons...")
        
        # Standard sizes
        sizes = {
            "32x32.png": (32, 32),
            "128x128.png": (128, 128),
            "128x128@2x.png": (256, 256),
            "icon.png": (512, 512)
        }
        
        for filename, size in sizes.items():
            resized = img.resize(size, Image.Resampling.LANCZOS)
            resized.save(filename, "PNG")
            print(f"  Created {filename}")
        
        # Generate ICO for Windows
        print("\nGenerating Windows ICO...")
        icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        ico_images = []
        
        for size in icon_sizes:
            resized = img.resize(size, Image.Resampling.LANCZOS)
            ico_images.append(resized)
        
        ico_images[0].save("icon.ico", format="ICO", sizes=icon_sizes, append_images=ico_images[1:])
        print("  Created icon.ico")
        
        # For ICNS (macOS), we'll create a placeholder since it requires macOS tools
        print("\nCreating placeholder ICNS...")
        img.resize((512, 512), Image.Resampling.LANCZOS).save("icon.icns", "PNG")
        print("  Created icon.icns (placeholder)")
        
        print("\nIcon generation complete!")
        
        # List generated files
        print("\nGenerated files:")
        for ext in ['*.png', '*.ico', '*.icns']:
            for file in sorted([f for f in os.listdir('.') if f.endswith(ext[1:])]):
                size = os.path.getsize(file)
                print(f"  {file}: {size:,} bytes")
        
        return True
        
    except Exception as e:
        print(f"Error generating icons: {e}")
        return False

if __name__ == "__main__":
    # Check if Pillow is installed
    try:
        from PIL import Image
    except ImportError:
        print("Pillow is required but not installed. Please install it:")
        print("pip install Pillow")
        sys.exit(1)
    
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    success = generate_icons()
    sys.exit(0 if success else 1)