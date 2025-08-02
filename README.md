# ISO-10816-Vibration-Sensor

<div align="center">

![AutomataNexus Logo](automata-nexus-logo.png)

# Enterprise Vibration Monitoring System

[![ISO 10816](https://img.shields.io/badge/ISO-10816%20Compliant-brightgreen)](https://www.iso.org/standard/50528.html)
[![Sensors](https://img.shields.io/badge/Sensors-WTVB01--485-blue)](https://www.wit-motion.com/)
[![Node-RED](https://img.shields.io/badge/Node--RED-v2.2.0-red)](https://nodered.org/)
[![Python](https://img.shields.io/badge/Python-3.8+-yellow)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-Commercial-orange)](#license)
[![API](https://img.shields.io/badge/API-REST-purple)](https://en.wikipedia.org/wiki/REST)
[![Modbus](https://img.shields.io/badge/Protocol-Modbus%20RTU-teal)](https://modbus.org/)

**Professional Industrial Equipment Health Monitoring**

*Multi-Port Support | Real-time Analysis | Desktop Application*

</div>

---

## 🏭 Overview

Enterprise-grade vibration monitoring system implementing **ISO 10816** standards for rotating machinery health assessment. Features **multi-port monitoring** to handle WTVB01-485 sensors that share the same Modbus address (0x50) by using separate USB-RS485 adapters.

### 🎯 Key Features

- **Multi-Port Monitoring** - Supports multiple USB-RS485 adapters for sensors with same address
- **ISO 10816 Compliance** - Automatic severity zones (A-D) based on machine class and HP rating
- **Equipment Configuration** - Web-based setup with custom names and specifications
- **Desktop Application** - Native Linux application with system tray integration
- **Real-time Analysis** - RMS, velocity, temperature with gravity compensation
- **Node-RED Integration** - Enhanced v2.2.0 parser with API support
- **Persistent Configuration** - Saves equipment settings between restarts
- **Auto-Discovery** - Automatically detects USB-RS485 adapters

## 🔧 Technical Specifications

### Supported Equipment (3-50 HP Motors)
- 🌬️ Cooling Tower Motors
- 💧 Centrifugal & Circulation Pumps  
- 🔩 Compressors (Reciprocating/Screw/Scroll)
- ⚡ Fan Motors & General Purpose Motors
- 📦 HVAC Equipment

### Measurement Capabilities
| Parameter | Range | Units |
|-----------|-------|-------|
| Acceleration | ±16 | g |
| Vibration Velocity | 0-50 | mm/s RMS |
| Temperature | -40 to +85 | °C |
| Frequency | 0-500 | Hz |
| Gravity Compensation | Auto | - |

### ISO 10816-3 Implementation
- **Group II**: 15-50 HP motors (higher thresholds)
- **Group III/IV**: 3-15 HP motors (lower thresholds)
- Automatic classification based on equipment type and power

## 📡 System Architecture

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────────┐
│ WTVB01-485 @0x50│────▶│USB0 Adapter  │────▶│                 │
└─────────────────┘     └──────────────┘     │                 │
                                             │  Multi-Port     │
┌─────────────────┐     ┌──────────────┐     │  Python Monitor │
│ WTVB01-485 @0x50│────▶│USB1 Adapter  │────▶│                 │
└─────────────────┘     └──────────────┘     │                 │
                                             └────────┬────────┘
┌─────────────────┐     ┌──────────────┐              │
│ WTVB01-485 @0x50│────▶│USB2 Adapter  │              │
└─────────────────┘     └──────────────┘              │
                                                      │
                                              ┌───────▼────────┐
                                              │  Flask REST API │
                                              └───────┬────────┘
                                                      │
                    ┌─────────────────────────────────┼─────────────────┐
                    │                                 │                 │
              ┌─────▼──────┐               ┌─────────▼────────┐ ┌──────▼──────┐
              │Web Dashboard│               │Node-RED v2.2.0   │ │Desktop App  │
              └────────────┘               └──────────────────┘ └─────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Raspberry Pi or Linux system
- Python 3.8+
- Node-RED 2.0+
- Multiple USB-RS485 adapters (one per sensor)
- WTVB01-485 sensors (all at address 0x50)

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/ISO-10816-Vibration-Sensor.git
cd ISO-10816-Vibration-Sensor

# Install Python dependencies
pip install flask flask-cors pyserial numpy

# Install as desktop application (Linux)
chmod +x install-desktop-linux.sh
./install-desktop-linux.sh

# For Node-RED integration
cd ~/.node-red
npm install node-red-contrib-automatanexus-hvac-vibration@2.2.0
node-red-restart
```

### Hardware Setup

1. **Connect Sensors** - One WTVB01-485 sensor per USB-RS485 adapter
2. **Plug in Adapters** - Connect to USB ports (will appear as /dev/ttyUSB0, ttyUSB1, etc.)
3. **No Address Change Needed** - All sensors can remain at default 0x50

### Running the System

#### Option 1: Desktop Application (Recommended)
- Click the AutomataNexus Vibration Monitor icon in your applications menu
- Or run: `./start-vibration-monitor.sh`

#### Option 2: Command Line
```bash
python3 multi_port_vibration_monitor.py
```

#### Option 3: System Service
```bash
sudo systemctl start vibration-monitor
sudo systemctl enable vibration-monitor  # For auto-start
```

### Web Interface Configuration

1. Open http://localhost:5000
2. Click "Equipment Configuration"
3. For each detected USB port:
   - Enter equipment name (e.g., "Cooling_Tower_1")
   - Select equipment type
   - Enter motor specifications (HP, voltage, phase)
   - Click "Save Configuration"
4. Click "Start Monitoring" when all sensors are configured

## 🌐 REST API

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/equipment_config` | Get all equipment configurations |
| POST | `/api/save_equipment_config` | Save equipment configuration |
| GET | `/api/scan_ports` | Scan for USB-RS485 adapters |
| GET | `/api/data` | Get latest sensor readings |
| POST | `/api/start` | Start monitoring |
| POST | `/api/stop` | Stop monitoring |

### Example API Response
```json
{
  "Cooling_Tower_1": {
    "temperature_f": 77.0,
    "rms_acceleration": 0.0246,
    "velocity_mms": 1.28,
    "iso_zone": "A",
    "alert_level": "NORMAL",
    "hp": 50,
    "voltage": 480,
    "phase": 3
  }
}
```

## 📊 Node-RED Integration

### Updated v2.2.0 Features
- Direct monitoring API support
- Automatic equipment detection
- Preserves API configuration
- No internal mapping override

### Installation
```bash
cd ~/.node-red
npm install node-red-contrib-automatanexus-hvac-vibration@2.2.0
node-red-restart
```

### Example Flow for API Integration
```javascript
// Function node to fetch from monitoring API
msg.url = "http://localhost:5000/api/data";
return msg;
```

Connect: Inject → Function → HTTP Request (GET) → Industrial Parser → Debug

### Parser Output Structure
```json
{
  "timestamp": "2025-08-02T10:00:00.000Z",
  "equipment_name": "Cooling_Tower_1",
  "equipment_type": "COOLING_TOWER",
  "equipment_power": {
    "hp": 50,
    "kw": 37.3
  },
  "temperature": {
    "fahrenheit": 77.0,
    "celsius": 25.0
  },
  "vibration": {
    "velocity_mms": 1.28,
    "rms_acceleration_g": 0.0246
  },
  "iso_zone": "A",
  "equipment_condition": "EXCELLENT",
  "alerts": []
}
```

## 🎯 ISO 10816-3 Vibration Limits

### Group II (15-50 HP) - Medium Motors
| Zone | Velocity (mm/s RMS) | Condition | Action |
|------|---------------------|-----------|--------|
| A | 0-2.3 | Good | Normal operation |
| B | 2.3-4.6 | Acceptable | Monitor regularly |
| C | 4.6-7.1 | Unsatisfactory | Schedule maintenance |
| D | >7.1 | Unacceptable | Immediate action |

### Group III/IV (3-15 HP) - Small Motors & Pumps
| Zone | Velocity (mm/s RMS) | Condition | Action |
|------|---------------------|-----------|--------|
| A | 0-1.4 | Good | Normal operation |
| B | 1.4-2.8 | Acceptable | Monitor regularly |
| C | 2.8-4.5 | Unsatisfactory | Schedule maintenance |
| D | >4.5 | Unacceptable | Immediate action |

## 📁 Configuration Files

### equipment_config.json
Automatically created and maintained by the web interface:
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

## 🛠️ Troubleshooting

### Sensors Not Detected
- Check USB connections: `ls /dev/ttyUSB*`
- Verify permissions: `sudo usermod -a -G dialout $USER`
- Logout and login after adding to dialout group

### All Sensors at 0x50
- This is expected! Use separate USB adapters for each sensor
- The software handles multiple adapters automatically

### High Vibration on Bench
- Gravity compensation is automatic
- Ensure sensors are on stable surface
- Check for electromagnetic interference

## 🛡️ Commercial License

This software is commercially licensed by **AutomataNexus AI & AutomataControls**.

### License Terms
- ✅ Commercial use with valid license
- ✅ Internal modifications allowed
- ❌ Redistribution prohibited
- ❌ Reverse engineering prohibited

**For licensing inquiries**: DevOps@automatacontrols.com

## 📞 Support

- 📧 **Email**: DevOps@automatacontrols.com
- 🌐 **Website**: https://automatanexus.com
- 📚 **Documentation**: See ISO-10816-Motor-Vibration-Guide.md

## 🔄 Recent Updates

### v2.2.0 (2025-08-02)
- Multi-port monitoring support
- Web-based equipment configuration
- Node-RED parser API integration
- Desktop application for Linux
- Gravity compensation improvements

---

<div align="center">

**© 2025 AutomataNexus AI & AutomataControls**

*Building Intelligence Through Automation*

</div>