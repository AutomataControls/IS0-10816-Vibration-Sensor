# Quick Start Guide - Raspberry Pi

## 🚀 5-Minute Setup

### 1. Download and Run Installer
```bash
wget https://raw.githubusercontent.com/AutomataControls/IS0-10816-Vibration-Sensor/main/install-on-pi.sh
chmod +x install-on-pi.sh
./install-on-pi.sh
```

### 2. Reboot
```bash
sudo reboot
```

### 3. Access Web Interface
- **Local**: http://localhost:5000/monitoring-app.html
- **Remote**: http://[YOUR-PI-IP]:5000/monitoring-app.html

### 4. Configure Sensors
1. Click "Configuration" tab
2. Click "Scan for USB Ports"
3. Fill in equipment details
4. Save each sensor
5. Go to "Control" tab
6. Click "Start Monitoring"

## 📊 What You'll See

- **Live sensor data** with color-coded zones:
  - 🟢 Zone A: Good
  - 🟡 Zone B: Acceptable  
  - 🟠 Zone C: Unsatisfactory
  - 🔴 Zone D: Unacceptable

- **Real-time trend graph** showing vibration velocity
- **Tooltips** on hover for metric explanations
- **Auto-saves** configuration between restarts

## 🔧 Quick Commands

**Check status:**
```bash
sudo systemctl status vibration-monitor
```

**View logs:**
```bash
sudo journalctl -u vibration-monitor -f
```

**Restart service:**
```bash
sudo systemctl restart vibration-monitor
```

**Manual run (for testing):**
```bash
cd /opt/automatanexus/IS0-10816-Vibration-Sensor
python3 multi_port_vibration_monitor.py
```

## 🔌 Wiring

```
Sensor → RS485 Adapter → USB Port
  A+ ——————— A+
  B- ——————— B-
  GND ———— GND
  VCC ———— 5-24V
```

## ⚡ Tips

- Allow 30 seconds after startup for sensor calibration
- Sensors must be on stable surface during calibration
- Each sensor needs its own USB adapter (all at address 0x50)
- Data logs to CSV files automatically
- Configuration persists through reboots

## 🆘 Troubleshooting

1. **No sensors found**: Check USB connections with `ls /dev/ttyUSB*`
2. **Permission denied**: Logout/login after installation (dialout group)
3. **High readings when stationary**: Wait for calibration, check mounting
4. **Can't access web**: Check with `sudo systemctl status vibration-monitor`

---
© 2025 AutomataNexus | ISO 10816-3 Compliant