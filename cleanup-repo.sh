#!/bin/bash
# Repository cleanup script
# Organizes files into proper structure

echo "==================================="
echo "AutomataNexus Repository Cleanup"
echo "==================================="
echo

# Create archive directories
echo "Creating archive directories..."
mkdir -p archive/old-versions
mkdir -p archive/test-scripts
mkdir -p archive/development
mkdir -p archive/windows-scripts
mkdir -p tools
mkdir -p docs

# Move documentation to docs folder
echo "Organizing documentation..."
mv ISO-10816-Motor-Vibration-Guide.md docs/ 2>/dev/null
mv NODE_RED_INTEGRATION.md docs/ 2>/dev/null
mv QUICK_START_PI.md docs/ 2>/dev/null
mv RASPBERRY_PI_SETUP.md docs/ 2>/dev/null
mv QUICK_START.md docs/ 2>/dev/null
mv INSTALL.md docs/ 2>/dev/null
mv COMMERCIAL.md docs/ 2>/dev/null

# Move tools to tools folder
echo "Organizing tools..."
mv diagnose_sensor.py tools/ 2>/dev/null
mv change_sensor_address.py tools/ 2>/dev/null
mv program_sensor_address.py tools/ 2>/dev/null
mv program_address_sdk_method.py tools/ 2>/dev/null
mv scan_all_sensors.py tools/ 2>/dev/null

# Archive old/redundant files
echo "Archiving old files..."

# Old versions and test files
mv universal_vibration_monitor.py archive/old-versions/ 2>/dev/null
mv universal_sensor_config_gui.py archive/old-versions/ 2>/dev/null
mv web_interface.html archive/old-versions/ 2>/dev/null
mv update_web_interface.py archive/old-versions/ 2>/dev/null
mv web-ui.html archive/old-versions/ 2>/dev/null
mv simple-redirect.html archive/old-versions/ 2>/dev/null

# Test scripts
mv test_individual_ports.py archive/test-scripts/ 2>/dev/null
mv test_save_methods.py archive/test-scripts/ 2>/dev/null
mv test-parser-api.js archive/test-scripts/ 2>/dev/null

# Development/setup scripts
mv setup-dependencies.sh archive/development/ 2>/dev/null
mv setup-raspberry-pi.sh archive/development/ 2>/dev/null
mv setup-venv.sh archive/development/ 2>/dev/null
mv create_hvac_package.sh archive/development/ 2>/dev/null
mv pi-quick-install.sh archive/development/ 2>/dev/null
mv fix-ui.sh archive/development/ 2>/dev/null

# Windows-specific scripts
mv force-update.cmd archive/windows-scripts/ 2>/dev/null
mv install-vibration-package.cmd archive/windows-scripts/ 2>/dev/null
mv publish-update.cmd archive/windows-scripts/ 2>/dev/null
mv update-node-red.cmd archive/windows-scripts/ 2>/dev/null
mv update-to-2.0.1.cmd archive/windows-scripts/ 2>/dev/null
mv start-all-windows.bat archive/windows-scripts/ 2>/dev/null

# Old start scripts
mv start-all.sh archive/old-versions/ 2>/dev/null
mv start-all-simple.sh archive/old-versions/ 2>/dev/null
mv update-nr.sh archive/old-versions/ 2>/dev/null

# Create clean file list
echo
echo "Main application files:"
echo "======================"
ls -1 *.py 2>/dev/null | grep -E "(multi_port_vibration_monitor|vibration-monitor-desktop|create-icon|install-gui)" || echo "None"

echo
echo "Installation scripts:"
echo "===================="
ls -1 *.sh 2>/dev/null | grep -E "(install\.sh|install-on-pi|install-desktop-linux)" || echo "None"

echo
echo "Web interface:"
echo "============="
ls -1 *.html 2>/dev/null | grep "monitoring-app" || echo "None"

echo
echo "Configuration:"
echo "============="
ls -1 *.json *.txt *.desktop 2>/dev/null || echo "None"

echo
echo "Node-RED:"
echo "========="
ls -1d node-red-* 2>/dev/null || echo "None"

echo
echo "Documentation (docs/):"
echo "===================="
ls -1 docs/ 2>/dev/null || echo "None"

echo
echo "Tools (tools/):"
echo "=============="
ls -1 tools/ 2>/dev/null || echo "None"

echo
echo "==================================="
echo "Cleanup complete!"
echo "==================================="
echo
echo "Recommended next steps:"
echo "1. Review archive/ folder contents"
echo "2. Delete archive/ if files are truly not needed"
echo "3. Update README.md to reflect new structure"
echo "4. Commit cleaned repository"