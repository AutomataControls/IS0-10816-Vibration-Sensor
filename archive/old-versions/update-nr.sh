#!/bin/bash
echo "Updating to bug fix version 2.0.1"
echo "=================================="
echo ""

# Navigate to Node-RED directory
cd /mnt/c/Users/*/.node-red

echo "Current directory: $(pwd)"
echo ""

echo "Updating to version 2.0.1..."
npm update node-red-contrib-automatanexus-hvac-vibration

echo ""
echo "Update complete!"
echo "Please restart Node-RED manually."
echo ""