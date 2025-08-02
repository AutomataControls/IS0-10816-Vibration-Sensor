# AutomataNexus Vibration Monitor
## Professional ISO 10816-3 Industrial Monitoring System

![AutomataNexus Logo](automata-nexus-logo.png)

[![License](https://img.shields.io/badge/license-Commercial-blue.svg)](LICENSE)
[![ISO](https://img.shields.io/badge/ISO-10816--3-green.svg)](docs/ISO-10816-Motor-Vibration-Guide.md)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org)
[![Node-RED](https://img.shields.io/badge/Node--RED-2.0+-red.svg)](https://nodered.org)

## 🚀 Quick Start

### Raspberry Pi Installation (Recommended)
```bash
wget https://raw.githubusercontent.com/AutomataControls/IS0-10816-Vibration-Sensor/main/install.sh
chmod +x install.sh
./install.sh
```

The installer automatically:
- ✅ Detects GUI/CLI environment
- ✅ Installs all dependencies
- ✅ Creates desktop shortcuts
- ✅ Sets up auto-start service
- ✅ Configures SQLite database

## 📋 Features

- **Multi-Port Monitoring** - Handle sensors with same Modbus address using separate USB adapters
- **ISO 10816-3 Compliance** - Automatic vibration severity zones (A-D)
- **7-Day Database** - SQLite with automatic retention management
- **Real-Time Web Interface** - Modern responsive dashboard
- **Node-RED Integration** - REST API with custom parser node
- **Desktop Application** - Native Linux app with system tray
- **Equipment Profiles** - Customizable for different motor types

## 🔧 System Requirements

- Raspberry Pi 3B+ or newer (4B recommended)
- Python 3.8+
- 1-5 USB-to-RS485 adapters
- WitMotion WTVB01-485 sensors

## 📁 Repository Structure

```
IS0-10816-Vibration-Sensor/
├── multi_port_vibration_monitor.py    # Main monitoring application
├── monitoring-app.html                # Web dashboard interface
├── vibration-monitor-desktop.py       # Desktop launcher
├── install.sh                         # Master installer (GUI/CLI)
├── install-on-pi.sh                  # Raspberry Pi CLI installer
├── install-gui.py                    # GUI installer with progress
├── node-red-contrib-*/               # Node-RED custom nodes
├── node-red-examples.json            # Example flows
├── docs/                             # Documentation
│   ├── RASPBERRY_PI_SETUP.md        # Detailed Pi setup
│   ├── NODE_RED_INTEGRATION.md      # Node-RED guide
│   └── ISO-10816-Motor-Vibration-Guide.md
├── tools/                            # Utility scripts
│   ├── diagnose_sensor.py
│   └── change_sensor_address.py
└── IS0-10816-Vibration-Monitor-UI/   # Tauri desktop app

```

## 🌐 Web Interface

Access at: `http://localhost:5000/monitoring-app.html`

### Features:
- Real-time sensor readings
- Vibration trend graphs
- Equipment configuration
- ISO zone indicators
- Alert notifications

## 📊 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/readings` | Current sensor values |
| GET | `/api/metrics/history` | Historical data (7 days) |
| GET | `/api/metrics/summary` | Statistical summaries |
| GET | `/api/metrics/alerts` | Zone C/D events |
| GET | `/api/status` | System status |
| POST | `/api/configure` | Save sensor config |

## 🔌 Node-RED Integration

```javascript
// Function node example
msg.url = "http://localhost:5000/api/readings";
msg.method = "GET";
return msg;
```

Import `node-red-examples.json` for complete flows including:
- Real-time monitoring
- Historical trends
- Alert automation
- Dashboard widgets

## 📈 ISO 10816-3 Zones

| Zone | Condition | 15-50 HP | 3-15 HP |
|------|-----------|----------|---------|
| A | Good | 0-2.3 mm/s | 0-1.4 mm/s |
| B | Acceptable | 2.3-4.6 mm/s | 1.4-2.8 mm/s |
| C | Unsatisfactory | 4.6-7.1 mm/s | 2.8-4.5 mm/s |
| D | Unacceptable | >7.1 mm/s | >4.5 mm/s |

## 🛠️ Troubleshooting

### No sensors detected
```bash
ls /dev/ttyUSB*  # Check USB devices
sudo usermod -a -G dialout $USER  # Add permissions
```

### Service management
```bash
sudo systemctl status vibration-monitor
sudo journalctl -u vibration-monitor -f
```

### Database location
```
/opt/automatanexus/IS0-10816-Vibration-Sensor/vibration_metrics.db
```

## 📞 Support

- **Email**: DevOps@automatacontrols.com
- **Documentation**: [Full Docs](docs/)
- **Issues**: [GitHub Issues](https://github.com/AutomataControls/IS0-10816-Vibration-Sensor/issues)

## 📄 License

This software is commercially licensed by AutomataNexus AI & AutomataControls.
See [LICENSE](LICENSE) for details.

---
© 2025 AutomataNexus AI & AutomataControls | Building Intelligence Through Automation