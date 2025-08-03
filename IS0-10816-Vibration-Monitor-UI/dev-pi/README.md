# Raspberry Pi Build Instructions

## Quick Build on Your Pi

1. **Copy this entire project to your Pi**
2. **SSH into your Pi and navigate to the project**
3. **Run the build script**:
```bash
cd IS0-10816-Vibration-Monitor-UI
chmod +x dev-pi/build-rpi.sh
./dev-pi/build-rpi.sh
```

4. **After build completes, create the distributable package**:
```bash
cd dev-pi
tar -czf automatanexus-vibration-monitor-rpi.tar.gz \
  ../src-tauri/target/release/automatanexus-vibration-monitor \
  install-rpi-binary.sh \
  automata-nexus-logo.png
```

5. **The `automatanexus-vibration-monitor-rpi.tar.gz` file is what users download**

## For End Users
Users just need to:
1. Download the `.tar.gz` file
2. Extract: `tar -xzf automatanexus-vibration-monitor-rpi.tar.gz`
3. Run: `./install-rpi-binary.sh`
4. Click the desktop icon!

No compilation needed by end users!