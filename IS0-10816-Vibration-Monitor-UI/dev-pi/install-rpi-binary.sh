#!/bin/bash
# AutomataNexus Vibration Monitor - Raspberry Pi Installer
# This script is included in the download package - users just run this!

echo "======================================================"
echo "  AutomataNexus Vibration Monitor Installer"
echo "  Professional Industrial Monitoring System"
echo "======================================================"
echo ""
echo "© 2025 AutomataNexus AI & AutomataControls"
echo ""

APP_NAME="AutomataNexus Vibration Monitor"
INSTALL_DIR="$HOME/.local/share/automatanexus-vibration-monitor"
DESKTOP_DIR="$HOME/Desktop"
APPS_DIR="$HOME/.local/share/applications"

# Check if binary exists in current directory
if [ ! -f "./automatanexus-vibration-monitor" ]; then
    echo "Error: Application binary not found!"
    echo "Please extract the full archive first."
    exit 1
fi

# Create directories
echo "Creating directories..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$APPS_DIR"
mkdir -p "$DESKTOP_DIR"

# Install application
echo "Installing application..."
cp automatanexus-vibration-monitor "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR/automatanexus-vibration-monitor"

# Copy logo
if [ -f "./automata-nexus-logo.png" ]; then
    cp automata-nexus-logo.png "$INSTALL_DIR/icon.png"
else
    echo "Warning: Logo not found, desktop icon will use default"
fi

# Create desktop entry file
DESKTOP_FILE="$APPS_DIR/automatanexus-vibration-monitor.desktop"
echo "Creating application menu entry..."
cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=AutomataNexus Vibration Monitor
Comment=Professional Industrial Equipment Monitoring
Exec=$INSTALL_DIR/automatanexus-vibration-monitor
Icon=$INSTALL_DIR/icon.png
Terminal=false
Categories=Development;Engineering;
StartupNotify=true
EOF

chmod +x "$DESKTOP_FILE"

# Create desktop shortcut
echo "Creating desktop shortcut..."
cp "$DESKTOP_FILE" "$DESKTOP_DIR/" 2>/dev/null || true
chmod +x "$DESKTOP_DIR/automatanexus-vibration-monitor.desktop" 2>/dev/null || true

# Mark as trusted for GNOME
if command -v gio &> /dev/null; then
    gio set "$DESKTOP_DIR/automatanexus-vibration-monitor.desktop" metadata::trusted true 2>/dev/null || true
fi

# Create uninstaller
cat > "$INSTALL_DIR/uninstall.sh" << EOF
#!/bin/bash
echo "Uninstalling AutomataNexus Vibration Monitor..."
rm -rf "$INSTALL_DIR"
rm -f "$APPS_DIR/automatanexus-vibration-monitor.desktop"
rm -f "$DESKTOP_DIR/automatanexus-vibration-monitor.desktop"
echo "Uninstallation complete!"
EOF
chmod +x "$INSTALL_DIR/uninstall.sh"

echo ""
echo "======================================================"
echo "✅ Installation Complete!"
echo "======================================================"
echo ""
echo "The application has been installed with:"
echo "  • Desktop shortcut created"
echo "  • Application menu entry added"
echo ""
echo "To launch: Click the desktop icon or find in application menu"
echo "To uninstall: Run $INSTALL_DIR/uninstall.sh"
echo ""
echo "Thank you for choosing AutomataNexus!"