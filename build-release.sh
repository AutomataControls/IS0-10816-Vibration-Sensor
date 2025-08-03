#!/bin/bash
################################################################################
# Build Release Package for AutomataNexus Vibration Monitor
# Creates a clean distribution with only necessary files
################################################################################

echo "Building AutomataNexus Vibration Monitor Release Package"
echo "======================================================="
echo

VERSION="3.0.0"
RELEASE_DIR="automatanexus-vibration-monitor-$VERSION"

# Create release directory
rm -rf $RELEASE_DIR
mkdir -p $RELEASE_DIR

# Copy only essential files for end users
echo "Copying essential files..."

# Core application files
cp multi_port_vibration_monitor.py $RELEASE_DIR/
cp monitoring-app.html $RELEASE_DIR/

# Logo
cp automata-nexus-logo.png $RELEASE_DIR/

# Installation files
cp install.sh $RELEASE_DIR/
cp install-gui.py $RELEASE_DIR/
cp install-on-pi.sh $RELEASE_DIR/

# Uninstall files  
cp uninstall.sh $RELEASE_DIR/
cp uninstall-gui.py $RELEASE_DIR/
cp uninstall-master.sh $RELEASE_DIR/

# Documentation (required for licensing)
cp README.md $RELEASE_DIR/
cp LICENSE.md $RELEASE_DIR/
cp COMMERCIAL.md $RELEASE_DIR/
cp EULA.md $RELEASE_DIR/

# Node-RED integration (optional but useful)
mkdir -p $RELEASE_DIR/node-red-contrib-automatanexus-hvac-vibration
cp -r node-red-contrib-automatanexus-hvac-vibration/* $RELEASE_DIR/node-red-contrib-automatanexus-hvac-vibration/

# Create a simple start script
cat > $RELEASE_DIR/start-monitor.sh << 'EOF'
#!/bin/bash
# Start the vibration monitor
cd "$(dirname "$0")"
python3 multi_port_vibration_monitor.py
EOF
chmod +x $RELEASE_DIR/start-monitor.sh

# Create requirements file with only runtime dependencies
cat > $RELEASE_DIR/requirements.txt << 'EOF'
pyserial>=3.5
flask>=1.1.2
flask-cors>=3.0.9
numpy>=1.19.5
EOF

# Create installation instructions
cat > $RELEASE_DIR/INSTALL.txt << 'EOF'
AutomataNexus Vibration Monitor - Installation Instructions
=========================================================

1. Easy Installation:
   Run: ./install.sh
   This will guide you through the installation process.

2. Manual Installation:
   - Install dependencies: pip3 install -r requirements.txt
   - Run directly: python3 multi_port_vibration_monitor.py
   - Access web interface: http://localhost:5000/monitoring-app.html

3. Uninstallation:
   Run: ./uninstall-master.sh

For support: DevOps@automatacontrols.com
For licensing: See COMMERCIAL.md
EOF

# Create archive
echo "Creating release archive..."
tar -czf $RELEASE_DIR.tar.gz $RELEASE_DIR/
zip -r $RELEASE_DIR.zip $RELEASE_DIR/

echo
echo "Release package created:"
echo "  - $RELEASE_DIR.tar.gz (for Linux)"
echo "  - $RELEASE_DIR.zip (for Windows users)"
echo
echo "Contents:"
ls -la $RELEASE_DIR/
echo
echo "Total files: $(find $RELEASE_DIR -type f | wc -l)"