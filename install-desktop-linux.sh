#!/bin/bash
# Install AutomataNexus Vibration Monitor as a desktop application on Linux

echo "========================================"
echo "AutomataNexus Vibration Monitor"
echo "Linux Desktop Installation"
echo "========================================"
echo

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Update paths in the desktop file
sed -i "s|/home/Automata/automatanexus-node-red-dev|$SCRIPT_DIR|g" vibration-monitor.desktop

# Copy desktop file to applications directory
echo "Installing desktop shortcut..."
mkdir -p ~/.local/share/applications
cp vibration-monitor.desktop ~/.local/share/applications/

# Copy icon to local icons directory
echo "Installing application icon..."
mkdir -p ~/.local/share/icons
cp IS0-10816-Vibration-Monitor-UI/src-tauri/icons/icon.png ~/.local/share/icons/automatanexus-vibration-monitor.png

# Make the Python script executable
chmod +x vibration-monitor-desktop.py
chmod +x multi_port_vibration_monitor.py

# Update desktop database
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database ~/.local/share/applications
fi

# Create a startup script that ensures proper environment
cat > start-vibration-monitor.sh << 'EOF'
#!/bin/bash
# Start AutomataNexus Vibration Monitor

# Kill any existing instances
pkill -f "multi_port_vibration_monitor.py"

# Change to the application directory
cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Start the application
python3 vibration-monitor-desktop.py
EOF

chmod +x start-vibration-monitor.sh

# Create systemd service for auto-start (optional)
echo
read -p "Do you want to enable auto-start on boot? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    cat > vibration-monitor.service << EOF
[Unit]
Description=AutomataNexus Vibration Monitor
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$SCRIPT_DIR
ExecStart=/usr/bin/python3 $SCRIPT_DIR/multi_port_vibration_monitor.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    echo "Installing systemd service..."
    sudo cp vibration-monitor.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable vibration-monitor.service
    echo "Service installed. Use 'sudo systemctl start vibration-monitor' to start now."
fi

echo
echo "========================================"
echo "Installation Complete!"
echo "========================================"
echo
echo "You can now:"
echo "1. Find 'AutomataNexus Vibration Monitor' in your applications menu"
echo "2. Run './start-vibration-monitor.sh' from the terminal"
echo "3. Access the web interface at http://localhost:5000"
echo
echo "The monitoring system will automatically detect USB-RS485 adapters"
echo "at /dev/ttyUSB0, /dev/ttyUSB1, /dev/ttyUSB2"
echo