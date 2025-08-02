# Quick Start Guide

## 🚀 5-Minute Setup

### 1. Hardware Connection
```
Sensor 1 → USB Adapter 1 → Raspberry Pi USB Port 1
Sensor 2 → USB Adapter 2 → Raspberry Pi USB Port 2  
Sensor 3 → USB Adapter 3 → Raspberry Pi USB Port 3
```

### 2. Install & Run
```bash
# Clone and enter directory
git clone [repository-url] && cd automatanexus-node-red-dev

# Install dependencies
pip3 install flask flask-cors pyserial numpy

# Add user to serial group (then logout/login!)
sudo usermod -a -G dialout $USER

# Run the monitor
python3 multi_port_vibration_monitor.py
```

### 3. Configure via Web
1. Open http://localhost:5000
2. Click "Equipment Configuration"
3. Fill in details for each sensor
4. Click "Start Monitoring"

### 4. Node-RED Integration
```bash
cd ~/.node-red
npm install node-red-contrib-automatanexus-hvac-vibration@2.2.0
node-red-restart
```

## 📊 What You'll See

```
=== Multi-Port Vibration Monitor Started ===
Monitoring ports: /dev/ttyUSB0, /dev/ttyUSB1, /dev/ttyUSB2

[OK] 10:01:35 | Cooling_Tower_1 | RMS: 0.0246g | Velocity: 1.28mm/s | ISO Zone: A | Temp: 77.0°F
[OK] 10:01:35 | Cooling_Tower_2 | RMS: 0.0189g | Velocity: 0.98mm/s | ISO Zone: A | Temp: 79.2°F
[WARN] 10:01:35 | Cooling_Tower_3 | RMS: 0.0856g | Velocity: 4.45mm/s | ISO Zone: C | Temp: 85.5°F
```

## 🔧 Common Commands

```bash
# Start monitoring
python3 multi_port_vibration_monitor.py

# Check USB ports
ls /dev/ttyUSB*

# View API data
curl http://localhost:5000/api/data

# Desktop app
./start-vibration-monitor.sh

# System service
sudo systemctl start vibration-monitor
sudo systemctl status vibration-monitor
```

## ⚡ ISO 10816 Zones

| Zone | Status | Action |
|------|--------|--------|
| **A** | ✅ Good | Normal operation |
| **B** | 🟡 Acceptable | Monitor regularly |
| **C** | 🟠 Unsatisfactory | Schedule maintenance |
| **D** | 🔴 Unacceptable | Immediate action |

## 🆘 Quick Fixes

**No sensors detected?**
```bash
ls /dev/ttyUSB*  # Check USB devices
sudo chmod 666 /dev/ttyUSB*  # Quick permission fix
```

**High readings on bench?**
- Normal! Gravity compensation is automatic
- Readings normalize when mounted

**Need help?**
- Full guide: [INSTALL.md](INSTALL.md)
- Email: DevOps@automatacontrols.com