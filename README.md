# AutomataNexus Vibration Monitor
## Professional ISO 10816-3 Industrial Monitoring System

![AutomataNexus Logo](automata-nexus-logo.png)

> **⚠️ ALPHA RELEASE v3.1.0-alpha**  
> This release includes API security, calibration system, and BMS integration features.

[![License](https://img.shields.io/badge/license-Commercial-blue.svg)](LICENSE)
[![ISO](https://img.shields.io/badge/ISO-10816--3-green.svg)](docs/ISO-10816-Motor-Vibration-Guide.md)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org)
[![Security](https://img.shields.io/badge/Security-JWT_Auth-orange.svg)](docs/API_SECURITY.md)

## 🚀 Quick Start

### GUI Installation (Recommended)
```bash
# Clone repository
git clone https://github.com/AutomataControls/IS0-10816-Vibration-Sensor.git
cd IS0-10816-Vibration-Sensor

# Run GUI installer
python3 install-gui.py
```

### CLI Installation
```bash
wget https://raw.githubusercontent.com/AutomataControls/IS0-10816-Vibration-Sensor/main/install.sh
chmod +x install.sh
./install.sh
```

The installer automatically:
- ✅ Detects GUI/CLI environment
- ✅ Installs all dependencies
- ✅ Creates desktop shortcuts with service control
- ✅ Configures SQLite database with 7-day retention
- ✅ Sets up API security with password protection
- ✅ Creates systemd service (manual start via desktop icon)

## 📋 Features

### Core Monitoring
- **Multi-Port Monitoring** - Handle sensors with same Modbus address using separate USB adapters
- **ISO 10816-3 Compliance** - Automatic vibration severity zones (A-D)
- **7-Day Database** - SQLite with automatic retention management
- **Real-Time Web Interface** - Modern responsive dashboard accessible network-wide
- **Equipment Profiles** - Customizable for different motor types

### Advanced Features
- **Sensor Calibration** - Zero-point calibration and scaling factors for each sensor
- **API Security** - JWT token authentication with configurable passwords
- **BMS Integration** - Send metrics to Building Management Systems via InfluxDB protocol
- **Background Operation** - "Keep Running" option to close browser while service continues
- **Network Access** - Monitor from any device on your network
- **Single Save Operation** - "Save All Configurations" button for all sensors at once

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

Access locally: `http://localhost:5000/monitoring-app.html`  
Access from network: `http://<raspberry-pi-ip>:5000/monitoring-app.html`

### Dashboard Features:
- **Real-time Monitoring** - Live sensor readings with auto-refresh
- **Vibration Trends** - 24-hour trend graphs for each sensor
- **Equipment Configuration** - Configure motor specs for each sensor
- **ISO Zone Indicators** - Color-coded severity zones (A-D)
- **Alert Notifications** - Real-time alerts for zone C/D conditions
- **Calibration Tab** - Zero-point calibration and scaling adjustments
- **BMS Integration** - Link to Building Management System

### Security Features:
- JWT token authentication (when enabled)
- Password protection set during installation
- 24-hour token expiry with refresh capability

## 📊 API Endpoints

### Public Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/login` | Authenticate and receive JWT token |
| GET | `/api/auth/check` | Verify authentication status |

### Protected Endpoints (require authentication when enabled)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/readings` | Current sensor values with calibration applied |
| GET | `/api/metrics/history` | Historical data (7 days) |
| GET | `/api/metrics/summary` | Statistical summaries |
| GET | `/api/metrics/alerts` | Zone C/D events |
| GET | `/api/status` | System status and sensor health |
| POST | `/api/configure` | Save sensor configuration |
| GET | `/api/calibration/<port>` | Get calibration settings |
| POST | `/api/calibration` | Update calibration settings |
| POST | `/api/calibration/zero/<port>` | Perform zero-point calibration |
| POST | `/api/bms/configure` | Configure BMS integration |
| GET | `/api/bms/status` | BMS connection status |
| POST | `/api/bms/toggle` | Enable/disable BMS sending |

### Authentication Header
```
Authorization: Bearer <your-jwt-token>
```

## 🔌 Integration Options

### Node-RED Integration
```javascript
// Function node example with authentication
msg.url = "http://localhost:5000/api/readings";
msg.method = "GET";
msg.headers = {
    "Authorization": "Bearer " + flow.get("vibration_token")
};
return msg;
```

Import `node-red-examples.json` for complete flows including:
- Real-time monitoring with authentication
- Historical trends visualization
- Alert automation for zone C/D
- Dashboard widgets

### BMS Integration (InfluxDB Line Protocol)
The system can send metrics directly to your Building Management System using InfluxDB line protocol format:

```
vibration_metrics,location=<location>,system=<sensor_name>,equipment_type=<type>,equipment_hp=<hp> velocity_rms=<value>,acceleration_peak=<value>,temperature=<value>,iso_zone="<zone>",alert_active=<0|1> <timestamp>
```

Each sensor sends individual metrics with:
- **system**: The configured equipment name for that sensor
- **location**: Your facility location name
- **Real-time values**: Velocity, acceleration, temperature
- **ISO compliance**: Current zone (A-D) and alert status

Configure via the "Link to BMS" button in the web interface.

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
# Logout and login for group changes to take effect
```

### Service management
```bash
# Service is NOT auto-started on boot
# Use desktop icon to start/stop service

# Check service status
sudo systemctl status vibration-monitor

# View service logs
sudo journalctl -u vibration-monitor -f

# Manual service control (if needed)
sudo systemctl start vibration-monitor
sudo systemctl stop vibration-monitor
```

### Network access issues
```bash
# Find Raspberry Pi IP address
hostname -I

# Check firewall (if enabled)
sudo ufw status
sudo ufw allow 5000/tcp  # If needed
```

### Authentication issues
- Default: Authentication is disabled
- If enabled during install, use the password you set
- Token expires after 24 hours
- Check .env file for configuration

### Database location
```
/opt/automatanexus/IS0-10816-Vibration-Sensor/vibration_metrics.db
```

### Configuration files
```
/opt/automatanexus/IS0-10816-Vibration-Sensor/.env  # API keys and BMS config
/opt/automatanexus/IS0-10816-Vibration-Sensor/equipment_config.json  # Sensor settings
```

## 📞 Support

- **Email**: DevOps@automatacontrols.com
- **Documentation**: [Full Docs](docs/)
- **Issues**: [GitHub Issues](https://github.com/AutomataControls/IS0-10816-Vibration-Sensor/issues)

## 📄 License

This software is commercially licensed by AutomataNexus AI & AutomataControls.
See [LICENSE](LICENSE) for details.

## 📝 Changelog

### v3.1.0-alpha (Latest)
- ✨ Added sensor calibration system with zero-point and scaling
- 🔐 Implemented JWT authentication with password protection
- 🏢 Added BMS integration with InfluxDB line protocol
- 🌐 Enabled network-wide access to monitoring interface
- 💾 Added "Save All Configurations" button
- 🏃 Added "Keep Running" button for background operation
- 🔧 Fixed GUI installer to handle installation from cloned repo
- 🖱️ Desktop icon now controls service lifecycle
- 📊 Individual sensor metrics sent to BMS with configured names

### v3.0.0-alpha.1
- 🗄️ SQLite database with 7-day retention
- 📈 Historical data API endpoints
- 🚨 Alert tracking and summaries

### v2.2.0
- 🔌 Multi-port sensor support
- 📱 Responsive web interface
- 🏭 ISO 10816-3 compliance

---
© 2025 AutomataNexus AI & AutomataControls | Building Intelligence Through Automation