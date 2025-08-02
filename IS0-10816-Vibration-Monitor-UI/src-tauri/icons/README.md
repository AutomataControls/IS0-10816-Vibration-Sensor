# App Icons

Place the following icon files here:
- `32x32.png` - 32x32 pixels
- `128x128.png` - 128x128 pixels
- `128x128@2x.png` - 256x256 pixels
- `icon.icns` - macOS icon
- `icon.ico` - Windows icon
- `icon.png` - Linux icon (512x512)

You can generate these from your automata-nexus-logo.png using:
- https://www.icoconverter.com/ for .ico files
- https://cloudconvert.com/png-to-icns for .icns files
- Or use ImageMagick:
  ```bash
  convert automata-nexus-logo.png -resize 32x32 32x32.png
  convert automata-nexus-logo.png -resize 128x128 128x128.png
  convert automata-nexus-logo.png -resize 256x256 128x128@2x.png
  convert automata-nexus-logo.png -resize 512x512 icon.png
  ```