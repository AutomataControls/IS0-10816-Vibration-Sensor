#!/bin/bash
# AutomataNexus Vibration Monitor Installation Script
# For fresh Raspberry Pi OS installation

set -e  # Exit on error

echo "=============================================="
echo "AutomataNexus Vibration Monitor Installer"
echo "For Raspberry Pi with fresh OS"
echo "=============================================="
echo

# Update system
echo "1. Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install required system packages
echo "2. Installing required system packages..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    curl \
    nodejs \
    npm \
    chromium-browser \
    sqlite3 \
    python3-tk \
    python3-pil \
    python3-pil.imagetk \
    python3-numpy \
    python3-scipy \
    python3-pandas \
    python3-flask \
    python3-flask-cors \
    python3-serial \
    python3-dotenv

# Install any missing Python packages via pip
echo "3. Installing additional Python dependencies..."
sudo pip3 install --break-system-packages \
    pyserial \
    flask \
    flask-cors \
    numpy \
    Pillow

# Create application directory
echo "4. Creating application directory..."
sudo mkdir -p /opt/automatanexus
sudo chown $USER:$USER /opt/automatanexus
cd /opt/automatanexus

# Clone the repository
echo "5. Cloning repository..."
git clone https://github.com/AutomataControls/IS0-10816-Vibration-Sensor.git
cd IS0-10816-Vibration-Sensor

# Make scripts executable
chmod +x *.sh
chmod +x *.py

# Create icon from logo or use fallback
echo "Creating application icon..."
python3 create-icon.py || echo "Using fallback icon"

# Create systemd service for auto-start
echo "6. Creating systemd service..."
sudo tee /etc/systemd/system/vibration-monitor.service > /dev/null << 'EOF'
[Unit]
Description=AutomataNexus Vibration Monitor
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/opt/automatanexus/IS0-10816-Vibration-Sensor
ExecStart=/usr/bin/python3 /opt/automatanexus/IS0-10816-Vibration-Sensor/multi_port_vibration_monitor.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable service
echo "7. Enabling auto-start service..."
sudo systemctl daemon-reload
sudo systemctl enable vibration-monitor.service

# Add user to dialout group for serial port access
echo "8. Adding user to dialout group..."
sudo usermod -a -G dialout $USER

# Create desktop shortcut
echo "9. Creating desktop shortcut..."
mkdir -p ~/Desktop
cat > ~/Desktop/vibration-monitor.desktop << 'EOF'
[Desktop Entry]
Type=Application
Name=Vibration Monitor
Comment=AutomataNexus Vibration Monitoring System
Icon=/opt/automatanexus/IS0-10816-Vibration-Sensor/icon.png
Exec=chromium-browser --app=http://localhost:5000/monitoring-app.html
Terminal=false
Categories=Utility;
EOF

chmod +x ~/Desktop/vibration-monitor.desktop

# Create monitoring app launcher script
echo "10. Creating launcher script..."
cat > /opt/automatanexus/IS0-10816-Vibration-Sensor/launch-monitor.sh << 'EOF'
#!/bin/bash
# Launch monitoring app in browser
sleep 5  # Wait for service to start
chromium-browser --app=http://localhost:5000/monitoring-app.html &
EOF

chmod +x /opt/automatanexus/IS0-10816-Vibration-Sensor/launch-monitor.sh

# Set up auto-launch on boot (optional)
echo "11. Setting up auto-launch..."
mkdir -p ~/.config/autostart
cat > ~/.config/autostart/vibration-monitor-ui.desktop << 'EOF'
[Desktop Entry]
Type=Application
Name=Vibration Monitor UI
Exec=/opt/automatanexus/IS0-10816-Vibration-Sensor/launch-monitor.sh
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
EOF

echo
echo "=============================================="
echo "Installation Complete!"
echo "=============================================="
echo
echo "Next steps:"
echo "1. Reboot your Raspberry Pi: sudo reboot"
echo "2. After reboot, the monitoring service will start automatically"
echo "3. Access the web interface at: http://localhost:5000/monitoring-app.html"
echo "4. Or click the 'Vibration Monitor' icon on your desktop"
echo
echo "To check service status: sudo systemctl status vibration-monitor"
echo "To view logs: sudo journalctl -u vibration-monitor -f"
echo
echo "Make sure your USB-to-RS485 adapters are connected before rebooting!"
echo