#!/bin/bash
# Quick install script to run ON the Raspberry Pi

echo "🍓 AutomataNexus Vibration Monitor - Pi Quick Install"
echo "===================================================="

# Update system
echo "Updating system packages..."
sudo apt-get update

# Install all required packages in one go
echo "Installing required packages..."
sudo apt-get install -y \
    git \
    python3-numpy \
    python3-scipy \
    python3-pandas \
    python3-flask \
    python3-flask-cors \
    python3-serial \
    python3-dotenv \
    python3-rpi.gpio

# Clone repository
echo "Cloning repository..."
cd ~
if [ ! -d "IS0-10816-Vibration-Sensor" ]; then
    git clone https://github.com/AutomataControls/IS0-10816-Vibration-Sensor.git
fi

cd IS0-10816-Vibration-Sensor

# Add user to dialout group
echo "Adding user to dialout group for serial access..."
sudo usermod -a -G dialout $USER

# Create systemd service
echo "Creating systemd service..."
sudo tee /etc/systemd/system/vibration-monitor.service > /dev/null << EOF
[Unit]
Description=AutomataNexus Vibration Monitor
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$HOME/IS0-10816-Vibration-Sensor
ExecStart=/usr/bin/python3 $HOME/IS0-10816-Vibration-Sensor/universal_vibration_monitor.py
Restart=always
RestartSec=10
Environment="PATH=/usr/bin:/usr/local/bin"

[Install]
WantedBy=multi-user.target
EOF

# Enable service
sudo systemctl daemon-reload
sudo systemctl enable vibration-monitor.service

echo ""
echo "✅ Installation complete!"
echo ""
echo "⚠️  IMPORTANT: You need to:"
echo "1. Log out and back in (for serial port access)"
echo "2. Connect your RS485 adapter"
echo "3. Run: sudo systemctl start vibration-monitor.service"
echo ""
echo "To test manually: python3 ~/IS0-10816-Vibration-Sensor/universal_vibration_monitor.py"
echo "Web interface will be at: http://$(hostname -I | awk '{print $1}'):5000"