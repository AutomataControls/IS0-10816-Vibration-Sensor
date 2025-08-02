#!/bin/bash
# Publish Node-RED package to npm

echo "Publishing Node-RED Package (Alpha)"
echo "==================================="
echo

cd node-red-contrib-automatanexus-hvac-vibration

# Check current version
echo "Current version:"
grep '"version"' package.json
echo

# Publish with alpha tag
echo "Publishing to npm with alpha tag..."
npm publish --tag alpha

echo
echo "Package published!"
echo
echo "To install alpha version:"
echo "npm install node-red-contrib-automatanexus-hvac-vibration@alpha"
echo
echo "View on npm:"
echo "https://www.npmjs.com/package/node-red-contrib-automatanexus-hvac-vibration"