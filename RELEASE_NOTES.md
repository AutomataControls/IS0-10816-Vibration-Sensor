# Release Notes

## v3.0.0-alpha.1 - Database & UI Update (2025-01-02)

### 🎉 New Features
- **SQLite Database** - 7-day automatic data retention
- **Professional GUI Installer** - Progress bar with branding
- **Node-RED Database API** - Historical data endpoints
- **Improved Web Dashboard** - Trend graphs and tooltips
- **Repository Cleanup** - Streamlined from 60+ to ~25 files

### 📊 Database Features
- Automatic hourly aggregates
- Query API endpoints:
  - `/api/metrics/history` - Historical data
  - `/api/metrics/summary` - Statistics
  - `/api/metrics/alerts` - Zone C/D events
- 7-day retention with daily cleanup

### 🔧 Improvements
- Fixed monitoring-app.html to work standalone
- Added icon support with fallback
- Enhanced tab icons visibility
- Better error handling
- Improved documentation structure

### 📦 Installation
```bash
wget https://raw.githubusercontent.com/AutomataControls/IS0-10816-Vibration-Sensor/main/install.sh
chmod +x install.sh
./install.sh
```

### 💥 Breaking Changes
- Requires SQLite3
- New API endpoints structure
- Configuration now in monitoring-app.html

---

## v2.2.0 - Multi-Port Support (2025-01-01)

### Features
- Multi-port monitoring for sensors at same address
- Web-based equipment configuration
- Desktop application support
- Gravity compensation improvements

### Changes
- Node-RED parser updated to handle API data
- Equipment names preserved from configuration
- ISO 10816-3 standards implementation

---

## v2.0.0 - Node-RED Integration (2024-12-31)

### Features
- Custom Node-RED parser node
- REST API endpoints
- Real-time monitoring dashboard
- CSV logging

### Initial Implementation
- WTVB01-485 sensor support
- Modbus RTU protocol
- Basic web interface