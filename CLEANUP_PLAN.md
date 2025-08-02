# Repository Cleanup Plan

## Files to Keep (Essential)

### Core Application
- `multi_port_vibration_monitor.py` - Main monitoring system
- `monitoring-app.html` - Web interface
- `vibration-monitor-desktop.py` - Desktop launcher
- `requirements.txt` - Python dependencies

### Installation
- `install.sh` - Master installer
- `install-on-pi.sh` - Pi-specific installer
- `install-gui.py` - GUI installer
- `install-desktop-linux.sh` - Desktop integration
- `create-icon.py` - Icon generator

### Node-RED
- `node-red-contrib-automatanexus-hvac-vibration/` - Custom node
- `node-red-examples.json` - Example flows

### Desktop App
- `IS0-10816-Vibration-Monitor-UI/` - Tauri application
- `vibration-monitor.desktop` - Desktop entry

### Documentation
- `README.md` - Main readme
- `LICENSE` - License file
- `automata-nexus-logo.png` - Logo

## Files to Move to docs/
- `ISO-10816-Motor-Vibration-Guide.md`
- `NODE_RED_INTEGRATION.md`
- `RASPBERRY_PI_SETUP.md`
- `QUICK_START_PI.md`
- `QUICK_START.md`
- `INSTALL.md`
- `COMMERCIAL.md`

## Files to Move to tools/
- `diagnose_sensor.py` - Diagnostic utility
- `change_sensor_address.py` - Address changer
- `program_sensor_address.py` - Address programmer
- `program_address_sdk_method.py` - SDK method
- `scan_all_sensors.py` - Scanner utility

## Files to Archive/Delete

### Old Versions (archive/old-versions/)
- `universal_vibration_monitor.py` - Replaced by multi_port version
- `universal_sensor_config_gui.py` - Replaced by web interface
- `web_interface.html` - Old interface
- `update_web_interface.py` - Old updater
- `web-ui.html` - Redundant
- `simple-redirect.html` - Not needed
- `start-all.sh` - Old starter
- `start-all-simple.sh` - Old starter

### Test Scripts (archive/test-scripts/)
- `test_individual_ports.py`
- `test_save_methods.py`
- `test-parser-api.js`

### Development Scripts (archive/development/)
- `setup-dependencies.sh`
- `setup-raspberry-pi.sh`
- `setup-venv.sh`
- `create_hvac_package.sh`
- `pi-quick-install.sh` - Replaced by install.sh
- `fix-ui.sh` - One-time fix
- `update-nr.sh` - Old updater

### Windows Scripts (archive/windows-scripts/)
- `force-update.cmd`
- `install-vibration-package.cmd`
- `publish-update.cmd`
- `update-node-red.cmd`
- `update-to-2.0.1.cmd`
- `start-all-windows.bat`

## Recommended Actions

1. **Run cleanup script**:
   ```bash
   chmod +x cleanup-repo.sh
   ./cleanup-repo.sh
   ```

2. **Review archive folder**:
   ```bash
   ls -la archive/
   ```

3. **If satisfied, remove archive**:
   ```bash
   rm -rf archive/
   ```

4. **Update main README**:
   ```bash
   mv CLEAN_README.md README.md
   ```

5. **Commit changes**:
   ```bash
   git add -A
   git commit -m "Clean up repository structure
   
   - Organized documentation into docs/
   - Moved tools to tools/
   - Archived old and redundant files
   - Updated README with clean structure"
   ```

## Final Structure
```
IS0-10816-Vibration-Sensor/
├── Core Files (7)
├── Installation Scripts (5)
├── Node-RED (2 items)
├── Desktop App (2 items)
├── docs/ (7 files)
├── tools/ (5 files)
└── Config files (3)

Total: ~25 active files (down from 60+)
```