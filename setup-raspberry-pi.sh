#!/bin/bash
# Complete Raspberry Pi Setup for AutomataNexus Vibration Monitor
# For Raspberry Pi OS Bullseye 32-bit

echo "🍓 Raspberry Pi Setup for AutomataNexus Vibration Monitor"
echo "========================================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${YELLOW}This script will guide you through the complete setup.${NC}"
echo -e "${YELLOW}Run these commands on your Raspberry Pi.${NC}"
echo ""

echo -e "${BLUE}Step 1: Update System${NC}"
echo "sudo apt-get update && sudo apt-get upgrade -y"
echo ""

echo -e "${BLUE}Step 2: Install Git${NC}"
echo "sudo apt-get install -y git"
echo ""

echo -e "${BLUE}Step 3: Clone the Repository${NC}"
echo "cd ~"
echo "git clone https://github.com/AutomataControls/IS0-10816-Vibration-Sensor.git"
echo "cd IS0-10816-Vibration-Sensor"
echo ""

echo -e "${BLUE}Step 4: Install Python Dependencies${NC}"
echo "# Install system packages (no pip needed!)"
echo "sudo apt-get install -y python3-numpy python3-scipy python3-pandas \\"
echo "  python3-flask python3-flask-cors python3-serial python3-dotenv \\"
echo "  python3-rpi.gpio"
echo ""

echo -e "${BLUE}Step 5: Set Serial Port Permissions${NC}"
echo "# Add user to dialout group for serial access"
echo "sudo usermod -a -G dialout \$USER"
echo "# Log out and back in for group changes to take effect"
echo ""

echo -e "${BLUE}Step 6: Enable Serial Port${NC}"
echo "# Run raspi-config"
echo "sudo raspi-config"
echo "# Navigate to: Interface Options > Serial Port"
echo "# - Login shell over serial: NO"
echo "# - Serial port hardware: YES"
echo ""

echo -e "${BLUE}Step 7: Install Node-RED (Optional)${NC}"
echo "# For Node-RED integration"
echo "bash <(curl -sL https://raw.githubusercontent.com/node-red/linux-installers/master/deb/update-nodejs-and-nodered)"
echo "# Then install the custom node:"
echo "cd ~/.node-red"
echo "npm install node-red-contrib-automatanexus-hvac-vibration"
echo ""

echo -e "${BLUE}Step 8: Create Startup Service${NC}"
echo "# Create systemd service file"
echo "sudo nano /etc/systemd/system/vibration-monitor.service"
echo ""
echo "# Add this content:"
cat << 'EOF'
[Unit]
Description=AutomataNexus Vibration Monitor
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/IS0-10816-Vibration-Sensor
ExecStart=/usr/bin/python3 /home/pi/IS0-10816-Vibration-Sensor/universal_vibration_monitor.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo ""
echo "# Enable and start service:"
echo "sudo systemctl enable vibration-monitor.service"
echo "sudo systemctl start vibration-monitor.service"
echo ""

echo -e "${BLUE}Step 9: Check Serial Port${NC}"
echo "# List serial ports to find your RS485 adapter"
echo "ls -la /dev/tty*"
echo "# Common ports: /dev/ttyUSB0, /dev/ttyAMA0, /dev/serial0"
echo ""

echo -e "${BLUE}Step 10: Test the System${NC}"
echo "# Run manually first"
echo "cd ~/IS0-10816-Vibration-Sensor"
echo "python3 universal_vibration_monitor.py"
echo ""
echo "# Check service status"
echo "sudo systemctl status vibration-monitor.service"
echo ""

echo -e "${GREEN}Hardware Connections:${NC}"
echo "1. Connect RS485 USB adapter to Pi USB port"
echo "2. Wire sensors to RS485 adapter:"
echo "   - A+ to sensor A+"
echo "   - B- to sensor B-"
echo "   - GND to sensor GND"
echo "   - 5V to sensor VCC (if powered via adapter)"
echo "3. Add 120Ω termination resistors at bus ends"
echo ""

echo -e "${GREEN}Access the Web Interface:${NC}"
echo "http://raspberrypi.local:5000"
echo "or"
echo "http://[PI-IP-ADDRESS]:5000"