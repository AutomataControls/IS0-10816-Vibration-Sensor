# AutomataNexus Vibration Monitor UI

Professional desktop application for industrial vibration monitoring with ISO 10816 compliance.

## 🚀 Features

- **Real-time Dashboard** - Live sensor data visualization
- **Multi-sensor Support** - Monitor up to 32 sensors simultaneously  
- **ISO 10816 Zones** - Automatic severity classification
- **Alert Management** - Configurable thresholds and notifications
- **Data Export** - CSV, JSON, PDF reports
- **Cross-platform** - Windows, macOS, Linux

## 🛠️ Development

### Prerequisites
- Node.js 16+
- Rust 1.70+
- Platform-specific build tools

### Setup
```bash
# Install dependencies
npm install

# Run in development mode
npm run dev

# Build for production
npm run build
```

### Build Targets
```bash
# Windows (.exe, .msi)
npm run build:windows

# macOS (.app, .dmg)
npm run build:macos

# Linux (.deb, .AppImage)
npm run build:linux

# All platforms
npm run build:all
```

## 📦 Distribution

Built applications will be in `src-tauri/target/release/bundle/`

### Windows
- `AutomataNexus Vibration Monitor.exe` - Installer
- `AutomataNexus Vibration Monitor.msi` - MSI package

### macOS  
- `AutomataNexus Vibration Monitor.app` - Application bundle
- `AutomataNexus Vibration Monitor.dmg` - Disk image

### Linux
- `automatanexus-vibration-monitor.deb` - Debian package
- `automatanexus-vibration-monitor.AppImage` - Universal package

## 🔧 Configuration

The app connects to the monitoring API at `http://localhost:5000`. 
To change the endpoint, modify `API_BASE` in `src/index.html`.

## 📝 License

Commercial software - © 2025 AutomataNexus AI & AutomataControls

For licensing: DevOps@automatacontrols.com