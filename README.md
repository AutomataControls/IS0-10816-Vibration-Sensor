# ISO-10816-Vibration-Sensor

<div align="center">

![AutomataNexus Logo](automata-nexus-logo.png)

# Enterprise Vibration Monitoring System

[![ISO 10816](https://img.shields.io/badge/ISO-10816%20Compliant-brightgreen)](https://www.iso.org/standard/50528.html)
[![Sensors](https://img.shields.io/badge/Sensors-WTVB01--485-blue)](https://www.wit-motion.com/)
[![Node-RED](https://img.shields.io/badge/Node--RED-Compatible-red)](https://nodered.org/)
[![Python](https://img.shields.io/badge/Python-3.8+-yellow)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-Commercial-orange)](#license)
[![API](https://img.shields.io/badge/API-REST-purple)](https://en.wikipedia.org/wiki/REST)
[![Modbus](https://img.shields.io/badge/Protocol-Modbus%20RTU-teal)](https://modbus.org/)

**Professional Industrial Equipment Health Monitoring**

*Predictive Maintenance | Real-time Analysis | Web Dashboard*

</div>

---

## 🏭 Overview

Enterprise-grade vibration monitoring system implementing **ISO 10816** standards for rotating machinery health assessment. Monitor up to **32 sensors** simultaneously with real-time analysis, automated alerts, and comprehensive web interface.

### 🎯 Key Features

- **ISO 10816 Compliance** - Automatic severity zones (A-D) based on machine class
- **Multi-Sensor Network** - RS485/Modbus RTU supporting 1-32 sensors
- **Real-time Analysis** - RMS, peak, crest factor, frequency spectrum
- **Web Dashboard** - Modern responsive interface with REST API
- **Node-RED Integration** - Custom nodes for automation workflows
- **Predictive Maintenance** - Early fault detection and trending
- **Data Export** - CSV logging with comprehensive metrics

## 🔧 Technical Specifications

### Supported Equipment
- 🌬️ HVAC Fans & Blowers
- 💧 Centrifugal Pumps  
- 🔩 Compressors (Reciprocating/Screw)
- ⚡ Motors & Generators
- 🔄 Turbines & Gearboxes
- ❄️ Cooling Towers
- 📦 Conveyors & Crushers

### Measurement Capabilities
| Parameter | Range | Units |
|-----------|-------|-------|
| Acceleration | ±16 | g |
| Angular Velocity | ±2000 | °/s |
| Temperature | -40 to +85 | °C |
| Vibration Velocity | 0-50 | mm/s RMS |
| Frequency Analysis | 0-500 | Hz |

### ISO 10816 Machine Classes
- **Class I**: Small machines (<15kW)
- **Class II**: Medium machines (15-75kW)  
- **Class III**: Large rigid foundation (>75kW)
- **Class IV**: Large soft foundation (>75kW)

## 📡 System Architecture

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────┐
│ WTVB01-485 x32 │────▶│ RS485/Modbus │────▶│Python Monitor│
└─────────────────┘     └──────────────┘     └──────┬───────┘
                                                     │
                                              ┌──────▼───────┐
                                              │  Flask API   │
                                              └──────┬───────┘
                                                     │
                        ┌────────────────────────────┼────────────────┐
                        │                            │                │
                  ┌─────▼─────┐            ┌────────▼──────┐  ┌──────▼─────┐
                  │Web Dashboard│           │Node-RED Flows │  │Data Export │
                  └───────────┘            └───────────────┘  └────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node-RED 2.0+
- RS485 USB adapter
- WTVB01-485 sensors

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/ISO-10816-Vibration-Sensor.git
cd ISO-10816-Vibration-Sensor

# Install Python dependencies
pip install -r requirements.txt

# Install Node-RED package
cd ~/.node-red
npm install node-red-contrib-automatanexus-hvac-vibration

# Start monitoring system
python universal_vibration_monitor.py
```

### Basic Configuration

1. **Connect Sensors** - Wire WTVB01-485 sensors to RS485 network
2. **Set Addresses** - Use `change_sensor_address.py` to assign unique addresses
3. **Configure Equipment** - Define sensor locations and machine specifications
4. **Start Monitoring** - Access web interface at `http://localhost:5000`

## 🌐 Web API

### REST Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/status` | System status and statistics |
| GET | `/api/sensors` | All sensor configurations |
| GET | `/api/sensors/{id}` | Specific sensor details |
| GET | `/api/readings` | Latest sensor readings |
| GET | `/api/alerts` | Active alerts and warnings |
| GET | `/api/thresholds` | Alert threshold settings |
| POST | `/api/control/start` | Start monitoring |
| POST | `/api/control/stop` | Stop monitoring |

### Example Response

```json
{
  "0x50": {
    "timestamp": "2025-01-15T10:30:45.123456",
    "name": "Tower_1_Motor",
    "temperature_f": 85.1,
    "acceleration": {
      "x": 0.0293,
      "y": -0.0488,
      "z": 0.9844
    },
    "metrics": {
      "rms_acceleration": 0.0123,
      "velocity_mms": 2.45,
      "iso_zone": "B",
      "dominant_frequency": 59.8
    },
    "alert_level": "NORMAL"
  }
}
```

## 📊 Node-RED Integration

### Available Nodes

- **industrial-vibration-parser** - Parse raw sensor data with ISO classification
- **hvac-vibration-parser** - Specialized HVAC equipment monitoring

### Example Flow

```json
[{"id":"example1","type":"industrial-vibration-parser","name":"Motor Monitor","sensorMappings":[{"address":"0x50","name":"Pump_1","type":"CENTRIFUGAL_PUMP","powerHP":50}]}]
```

## 🛡️ Commercial License

This software is commercially licensed by **AutomataNexus AI & AutomataControls**.

### License Types

| License | Sensors | Support | Updates | Price |
|---------|---------|---------|---------|-------|
| **Professional** | Up to 10 | Email | 1 Year | Contact Sales |
| **Business** | Up to 32 | Priority | 2 Years | Contact Sales |
| **Enterprise** | Unlimited | 24/7 | Lifetime | Contact Sales |

### Terms of Use

- ✅ Commercial use with valid license
- ✅ Internal modifications allowed
- ❌ Redistribution prohibited
- ❌ Reverse engineering prohibited
- ❌ Open source derivatives prohibited

**For licensing inquiries**: DevOps@automatacontrols.com

## 📞 Support

- 📧 **Email**: DevOps@automatacontrols.com
- 🌐 **Website**: https://automatanexus.com
- 📱 **Phone**: Contact sales for priority support

## ⚠️ Disclaimer

This software is provided under commercial license terms. Unauthorized use, copying, or distribution is strictly prohibited and may result in legal action.

---

<div align="center">

**© 2025 AutomataNexus AI & AutomataControls**

*Building Intelligence Through Automation*

</div>