# Installation Guide

## Table of Contents
1. [System Requirements](#system-requirements)
2. [Hardware Setup](#hardware-setup)
3. [Software Installation](#software-installation)
4. [Desktop Application Setup](#desktop-application-setup)
5. [Node-RED Integration](#node-red-integration)
6. [Configuration](#configuration)
7. [Verification](#verification)
8. [Troubleshooting](#troubleshooting)

## System Requirements

### Hardware
- Raspberry Pi 4 (recommended) or any Linux system
- Multiple USB ports (one per sensor)
- USB-to-RS485 adapters (one per sensor)
- WTVB01-485 vibration sensors

### Software
- Raspbian OS / Ubuntu / Debian
- Python 3.8 or higher
- Node-RED 2.0+ (for automation)
- Git

## Hardware Setup

### 1. Connect USB-RS485 Adapters
```bash
# Before connecting, check existing USB devices
ls /dev/ttyUSB*

# Connect your USB-RS485 adapters one at a time
# After connecting each, verify it appears:
ls /dev/ttyUSB*
# You should see /dev/ttyUSB0, /dev/ttyUSB1, etc.
```

### 2. Wire Sensors to Adapters
Each WTVB01-485 sensor connects to its own USB-RS485 adapter:

```
Sensor 1 (0x50) ─── USB Adapter 1 (/dev/ttyUSB0)
Sensor 2 (0x50) ─── USB Adapter 2 (/dev/ttyUSB1)  
Sensor 3 (0x50) ─── USB Adapter 3 (/dev/ttyUSB2)
```

**Wiring:**
- Sensor A+ → Adapter A+
- Sensor B- → Adapter B-
- Sensor GND → Adapter GND
- Sensor VCC (12-24V) → External power supply

## Software Installation

### 1. Clone Repository
```bash
cd /home/Automata
git clone https://github.com/yourusername/ISO-10816-Vibration-Sensor.git automatanexus-node-red-dev
cd automatanexus-node-red-dev
```

### 2. Install Python Dependencies
```bash
# Update package list
sudo apt update

# Install Python and pip if not already installed
sudo apt install python3 python3-pip

# Install required Python packages
pip3 install flask flask-cors pyserial numpy

# For desktop icon generation
pip3 install Pillow
```

### 3. Set Serial Port Permissions
```bash
# Add user to dialout group for serial port access
sudo usermod -a -G dialout $USER

# IMPORTANT: Logout and login for changes to take effect
```

## Desktop Application Setup

### 1. Generate Application Icons
```bash
cd IS0-10816-Vibration-Monitor-UI/src-tauri/icons
python3 generate-icons-python.py
```

### 2. Install Desktop Application
```bash
cd /home/Automata/automatanexus-node-red-dev
chmod +x install-desktop-linux.sh
./install-desktop-linux.sh
```

This will:
- Create desktop shortcut
- Add to applications menu
- Create start script
- Optionally enable auto-start on boot

### 3. Launch Application
Choose one of these methods:
- Click "AutomataNexus Vibration Monitor" in applications menu
- Double-click desktop icon
- Run from terminal: `./start-vibration-monitor.sh`

## Node-RED Integration

### 1. Install Node-RED (if not installed)
```bash
# Install Node.js and npm
curl -sL https://deb.nodesource.com/setup_16.x | sudo -E bash -
sudo apt install -y nodejs

# Install Node-RED
sudo npm install -g --unsafe-perm node-red

# Start Node-RED
node-red
```

### 2. Install Vibration Parser Node
```bash
cd ~/.node-red
npm install node-red-contrib-automatanexus-hvac-vibration@2.2.0
node-red-restart
```

### 3. Import Example Flow
1. Open Node-RED: http://localhost:1880
2. Menu → Import → Clipboard
3. Paste this flow:

```json
[{
    "id": "inject-1",
    "type": "inject",
    "name": "Poll Every 5s",
    "props": [{"p": "payload"}],
    "repeat": "5",
    "crontab": "",
    "once": true,
    "topic": ""
}, {
    "id": "function-1",
    "type": "function",
    "name": "Set API URL",
    "func": "msg.url = 'http://localhost:5000/api/data';\nreturn msg;",
    "outputs": 1
}, {
    "id": "http-1",
    "type": "http request",
    "name": "Get Sensor Data",
    "method": "GET",
    "ret": "obj",
    "url": ""
}, {
    "id": "parser-1",
    "type": "industrial-vibration-parser",
    "name": "Parse Vibration Data",
    "outputFormat": "standard",
    "globalVars": true,
    "globalPrefix": "vibration"
}, {
    "id": "debug-1",
    "type": "debug",
    "name": "Parsed Output",
    "active": true,
    "console": false,
    "complete": "payload"
}]
```

4. Wire nodes: Inject → Function → HTTP Request → Parser → Debug
5. Deploy flow

## Configuration

### 1. Access Web Interface
Open browser to: http://localhost:5000

### 2. Configure Equipment
1. Click "Equipment Configuration"
2. For each detected USB port:
   - **Equipment Name**: Enter descriptive name (e.g., "Cooling_Tower_1")
   - **Equipment Type**: Select from dropdown
   - **HP**: Motor horsepower (3-50)
   - **Voltage**: Select voltage (208/230/460/480)
   - **Phase**: Single or Three phase
   - **RPM**: Nominal speed (default 1800)
   - **Mounting**: Rigid or Flexible
3. Click "Save Configuration" for each sensor

### 3. Start Monitoring
Click "Start Monitoring" button after all sensors are configured

### 4. Configuration File
Settings are saved to `equipment_config.json`:
```json
{
  "/dev/ttyUSB0": {
    "equipment_name": "Cooling_Tower_1",
    "equipment_type": "cooling_tower_motor",
    "hp": 50,
    "voltage": 480,
    "phase": 3,
    "rpm": 1800,
    "mounting": "rigid"
  }
}
```

## Verification

### 1. Check Sensor Communication
```bash
# View monitoring output
python3 multi_port_vibration_monitor.py

# You should see:
# [OK] 10:01:35 | Cooling_Tower_1 | RMS: 0.0246g | Velocity: 1.28mm/s | ISO Zone: A | Temp: 77.0°F
```

### 2. Test API
```bash
# Get sensor data
curl http://localhost:5000/api/data

# Get equipment configuration  
curl http://localhost:5000/api/equipment_config

# Scan for USB ports
curl http://localhost:5000/api/scan_ports
```

### 3. Verify Node-RED Integration
- Check debug node output in Node-RED
- Verify global variables are set
- Monitor for any error messages

## Troubleshooting

### No USB Devices Found
```bash
# Check USB devices
lsusb
dmesg | grep ttyUSB

# Verify adapters are recognized
ls -la /dev/ttyUSB*

# Check permissions
groups $USER  # Should include 'dialout'
```

### Permission Denied on Serial Port
```bash
# Add to dialout group
sudo usermod -a -G dialout $USER

# Logout and login again!

# Temporary fix (until reboot):
sudo chmod 666 /dev/ttyUSB*
```

### Sensors Not Responding
1. Check wiring connections
2. Verify 12-24V power to sensors
3. Confirm all sensors at address 0x50
4. Test with single sensor first

### High Vibration Readings on Bench
- Normal due to gravity vector
- Software includes automatic compensation
- Place sensors on stable surface
- Readings normalize when mounted on equipment

### Desktop Icon Not Appearing
```bash
# Update desktop database
update-desktop-database ~/.local/share/applications

# Check desktop file
cat ~/.local/share/applications/vibration-monitor.desktop

# Make executable
chmod +x ~/Desktop/*.desktop
```

### Service Won't Start
```bash
# Check service status
sudo systemctl status vibration-monitor

# View logs
sudo journalctl -u vibration-monitor -f

# Restart service
sudo systemctl restart vibration-monitor
```

### Node-RED Parser Issues
```bash
# Check Node-RED logs
node-red-log

# Reinstall parser
cd ~/.node-red
npm uninstall node-red-contrib-automatanexus-hvac-vibration
npm install node-red-contrib-automatanexus-hvac-vibration@2.2.0
node-red-restart
```

## Next Steps

1. Mount sensors on equipment
2. Configure alert thresholds
3. Set up email notifications
4. Create monitoring dashboards
5. Schedule reports

For additional support: DevOps@automatacontrols.com