#!/bin/bash
# Quick fix for UI issues

echo "Fixing UI issues..."

# Create a working index.html without the sensor-config.js conflict
cd IS0-10816-Vibration-Monitor-UI/src

# Backup original
cp index.html index.html.backup

# Remove the problematic sensor-config.js include temporarily
sed -i '/<script src="sensor-config.js"><\/script>/d' index.html

# Fix the showTab function to work properly
sed -i 's/event.target.classList.add/event.currentTarget.classList.add/g' index.html

echo "UI fixes applied!"
echo "Please refresh your browser (Ctrl+F5)"