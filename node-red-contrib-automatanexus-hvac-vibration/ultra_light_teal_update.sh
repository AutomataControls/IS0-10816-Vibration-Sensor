#!/bin/bash
# Update AutomataNexus HVAC Node to Ultra Light Teal
# (c) 2025 AutomataNexus AI & AutomataControls

echo "🎨 Updating AutomataNexus HVAC Node to Ultra Light Teal..."

# Navigate to package directory
cd /mnt/d/opt/automatanexus-node-red-dev/node-red-contrib-automatanexus-hvac-vibration

# Backup original
cp hvac-vibration-parser.html hvac-vibration-parser.html.backup

# Ultra Light Teal Color Options:
echo "🎨 Ultra Light Teal Color Options:"
echo "   #AFEEEE - Pale Turquoise (very light)"
echo "   #B0E0E6 - Powder Blue (light teal)" 
echo "   #E0FFFF - Light Cyan (ultra light)"
echo "   #F0FFFF - Azure (very pale teal)"
echo "   #CCFFFF - Very Light Cyan"
echo ""

# Set ultra light teal color
ULTRA_LIGHT_TEAL="#AFEEEE"  # Pale Turquoise - perfect for HVAC!

# Replace the color in HTML file
sed -i "s/color: '#00A86B'/color: '$ULTRA_LIGHT_TEAL'/" hvac-vibration-parser.html

echo "✅ Node color updated to Ultra Light Teal: $ULTRA_LIGHT_TEAL"
echo ""

# Verify the change
echo "🔍 Verifying color change..."
grep "color:" hvac-vibration-parser.html

echo ""
echo "🚀 To publish the color change:"
echo "   npm version patch"
echo "   npm publish"
echo "   # Users will see new color on next install/update"
echo ""
echo "🎨 Ultra Light Teal is perfect for HVAC - clean, professional, and distinctive!"
