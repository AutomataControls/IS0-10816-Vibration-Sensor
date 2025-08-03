#!/bin/bash
################################################################################
# AutomataNexus Vibration Monitor - Network Information
################################################################################

echo "=========================================="
echo "AutomataNexus Vibration Monitor"
echo "Network Access Information"
echo "=========================================="
echo ""

# Get network interfaces and IPs
echo "Network Interfaces:"
echo "------------------"
ip -4 addr show | grep -E "inet " | grep -v "127.0.0.1" | awk '{print $NF ": " $2}'

echo ""
echo "Access URLs:"
echo "------------"

# Get primary IP (usually the first non-localhost IP)
PRIMARY_IP=$(hostname -I | awk '{print $1}')

if [ -n "$PRIMARY_IP" ]; then
    echo "Primary: http://$PRIMARY_IP:5000/monitoring-app.html"
    
    # Show all IPs
    for ip in $(hostname -I); do
        if [ "$ip" != "$PRIMARY_IP" ]; then
            echo "Alternative: http://$ip:5000/monitoring-app.html"
        fi
    done
else
    echo "No network connection detected"
fi

echo ""
echo "Note: Access from any device on your network using the URLs above"
echo ""

# Check if service is running
if systemctl is-active --quiet vibration-monitor; then
    echo "✓ Vibration Monitor service is running"
else
    echo "✗ Vibration Monitor service is not running"
    echo "  Start it by clicking the desktop icon"
fi

echo ""