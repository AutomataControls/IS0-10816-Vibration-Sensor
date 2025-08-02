# Raspberry Pi Installation Guide
## AutomataNexus Vibration Monitoring System

This guide will help you install the vibration monitoring system on a fresh Raspberry Pi.

## Prerequisites

### Hardware Requirements
- Raspberry Pi 3B+ or newer (4B recommended)
- MicroSD card (16GB minimum, 32GB recommended)
- USB-to-RS485 adapters (1-5 units)
- WitMotion WTVB01-485 sensors (1-5 units)
- Power supply for Raspberry Pi
- HDMI cable and monitor (for initial setup)
- Keyboard and mouse (for initial setup)

### Software Requirements
- Raspberry Pi OS (64-bit recommended)
- Internet connection for initial setup

## Step 1: Prepare Raspberry Pi OS

1. Download Raspberry Pi Imager from https://www.raspberrypi.com/software/
2. Flash Raspberry Pi OS (64-bit) to your SD card
3. Enable SSH and set up WiFi (optional) using Imager settings
4. Insert SD card and boot your Raspberry Pi
5. Complete initial setup wizard

## Step 2: Quick Installation

### Option A: Automated Installation (Recommended)

1. Open Terminal on your Raspberry Pi
2. Download and run the installation script:

```bash
# Download the installation script
wget https://raw.githubusercontent.com/AutomataControls/IS0-10816-Vibration-Sensor/main/install-on-pi.sh

# Make it executable
chmod +x install-on-pi.sh

# Run the installer
./install-on-pi.sh
```

3. The script will automatically:
   - Update your system
   - Install all dependencies
   - Clone the repository
   - Set up auto-start service
   - Create desktop shortcuts
   - Configure everything for you

4. Reboot when complete:
```bash
sudo reboot
```

### Option B: Manual Installation

If you prefer manual installation or the script fails:

1. **Update system:**
```bash
sudo apt update && sudo apt upgrade -y
```

2. **Install dependencies:**
```bash
sudo apt install -y python3 python3-pip python3-venv git nodejs npm chromium-browser
```

3. **Install Python packages:**
```bash
sudo pip3 install --break-system-packages pyserial flask flask-cors numpy
```

4. **Clone repository:**
```bash
sudo mkdir -p /opt/automatanexus
sudo chown $USER:$USER /opt/automatanexus
cd /opt/automatanexus
git clone https://github.com/AutomataControls/IS0-10816-Vibration-Sensor.git
cd IS0-10816-Vibration-Sensor
```

5. **Add user to dialout group:**
```bash
sudo usermod -a -G dialout $USER
```

6. **Create systemd service:**
```bash
sudo nano /etc/systemd/system/vibration-monitor.service
```

Add the following content:
```ini
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
```

7. **Enable service:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable vibration-monitor.service
sudo systemctl start vibration-monitor.service
```

## Step 3: Connect Your Sensors

1. **Connect USB-to-RS485 adapters** to Raspberry Pi USB ports
2. **Wire sensors** to RS485 adapters:
   - A+ to A+ (typically labeled)
   - B- to B- (typically labeled)
   - Power connections as per sensor requirements
3. **Note USB port assignments** - they will appear as:
   - /dev/ttyUSB0
   - /dev/ttyUSB1
   - /dev/ttyUSB2
   - etc.

## Step 4: Access the Monitoring System

### Via Desktop (if using Raspberry Pi with GUI):
1. Look for "Vibration Monitor" icon on desktop
2. Double-click to launch

### Via Web Browser:
1. Open Chromium browser
2. Navigate to: `http://localhost:5000/monitoring-app.html`

### From Another Computer:
1. Find Raspberry Pi IP address: `hostname -I`
2. Open browser on other computer
3. Navigate to: `http://[PI-IP-ADDRESS]:5000/monitoring-app.html`

## Step 5: Configure Sensors

1. Open the monitoring interface
2. Click on "Configuration" tab
3. Click "Scan for USB Ports"
4. For each detected sensor, enter:
   - Equipment Name (e.g., "Cooling_Tower_1")
   - Equipment Type
   - Motor HP (3-50)
   - Voltage
   - Phase
5. Click "Save Configuration" for each sensor
6. Go to "Control" tab
7. Click "Start Monitoring"

## Troubleshooting

### Check Service Status:
```bash
sudo systemctl status vibration-monitor
```

### View Logs:
```bash
sudo journalctl -u vibration-monitor -f
```

### Test USB Ports:
```bash
ls -la /dev/ttyUSB*
```

### Test Sensor Connection:
```bash
# Stop the service first
sudo systemctl stop vibration-monitor

# Run manually to see output
cd /opt/automatanexus/IS0-10816-Vibration-Sensor
python3 multi_port_vibration_monitor.py
```

### Common Issues:

1. **"Permission denied" on serial ports:**
   - Make sure user is in dialout group
   - Logout and login again after adding to group

2. **No sensors detected:**
   - Check USB connections
   - Verify RS485 wiring (A+/B-)
   - Check sensor power supply

3. **Web interface not loading:**
   - Check if service is running
   - Check firewall settings
   - Verify port 5000 is not in use

4. **Sensors showing high vibration when stationary:**
   - Ensure sensors are on stable surface
   - Allow 30 seconds for calibration
   - Check mounting orientation

## Performance Optimization

For Raspberry Pi 3B+ or older:

1. **Disable unnecessary services:**
```bash
sudo systemctl disable bluetooth
sudo systemctl disable hciuart
```

2. **Increase swap size:**
```bash
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# Change CONF_SWAPSIZE=100 to CONF_SWAPSIZE=1024
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

3. **Reduce GPU memory:**
```bash
sudo raspi-config
# Advanced Options > Memory Split > Set to 16
```

## Maintenance

### Update the software:
```bash
cd /opt/automatanexus/IS0-10816-Vibration-Sensor
git pull
sudo systemctl restart vibration-monitor
```

### Backup configuration:
```bash
cp equipment_config.json ~/equipment_config_backup.json
```

### Export data:
Data is automatically logged to CSV files in:
```
/opt/automatanexus/IS0-10816-Vibration-Sensor/vibration_log_*.csv
```

## Node-RED Integration

If you want to integrate with Node-RED:

1. Install Node-RED (if not already installed):
```bash
bash <(curl -sL https://raw.githubusercontent.com/node-red/linux-installers/master/deb/update-nodejs-and-nodered)
```

2. Install the custom parser node:
```bash
cd ~/.node-red
npm install /opt/automatanexus/IS0-10816-Vibration-Sensor/node-red-contrib-automatanexus-hvac-vibration
```

3. Restart Node-RED:
```bash
node-red-restart
```

4. Use HTTP Request node to fetch from: `http://localhost:5000/api/readings`
5. Connect to the AutomataNexus Industrial Vibration Parser node

## Support

For issues or questions:
- GitHub Issues: https://github.com/AutomataControls/IS0-10816-Vibration-Sensor/issues
- Check the logs first: `sudo journalctl -u vibration-monitor -f`
- Ensure all connections are secure and sensors have power

## License

© 2025 AutomataNexus AI & AutomataControls
Professional Industrial Monitoring System