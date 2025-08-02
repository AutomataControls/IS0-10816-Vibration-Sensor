#!/usr/bin/env python3
"""
Update the universal_vibration_monitor.py to include the full web interface
"""

import re

# Read the current file
with open('universal_vibration_monitor.py', 'r') as f:
    content = f.read()

# Find the serve_web_interface function
pattern = r'(@app\.route\(\'/\'\)\s*def serve_web_interface\(\):\s*""".*?""")\s*return """.*?"""'

# The new web interface HTML
new_interface = r'''\1
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AutomataNexus Vibration Monitor</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        .font-ultralight { font-weight: 200; }
        body {
            background: linear-gradient(135deg, #f0fffe 0%, #e6fffa 25%, #fef7ed 50%, #eff6ff 75%, #f0f9ff 100%);
            min-height: 100vh;
        }
        .glass-card {
            background: rgba(255, 255, 255, 0.7);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.3);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            border-radius: 16px;
        }
        .status-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
        .status-dot.connected { background: #10b981; }
        .status-dot.disconnected { background: #ef4444; }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        .alert-normal { background: rgba(16, 185, 129, 0.1); border-left: 4px solid #10b981; }
        .alert-warning { background: rgba(245, 158, 11, 0.1); border-left: 4px solid #f59e0b; }
        .alert-critical { background: rgba(249, 115, 22, 0.1); border-left: 4px solid #f97316; }
        .alert-emergency { background: rgba(239, 68, 68, 0.1); border-left: 4px solid #ef4444; }
    </style>
</head>
<body class="font-ultralight">
    <div class="container mx-auto px-4 py-8">
        <!-- Header -->
        <div class="glass-card p-6 mb-8">
            <div class="flex justify-between items-center">
                <div>
                    <h1 class="text-3xl font-ultralight text-gray-800">AutomataNexus Vibration Monitor</h1>
                    <p class="text-gray-600">Enterprise Industrial Monitoring System</p>
                </div>
                <div class="flex items-center gap-2">
                    <div class="status-dot connected" id="connectionDot"></div>
                    <span id="connectionStatus">Connected</span>
                </div>
            </div>
        </div>

        <!-- System Status -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <div class="glass-card p-4">
                <h3 class="text-gray-600">System Status</h3>
                <p class="text-2xl font-light" id="systemStatus">RUNNING</p>
            </div>
            <div class="glass-card p-4">
                <h3 class="text-gray-600">Active Sensors</h3>
                <p class="text-2xl font-light" id="activeSensors">0</p>
            </div>
            <div class="glass-card p-4">
                <h3 class="text-gray-600">Total Readings</h3>
                <p class="text-2xl font-light" id="totalReadings">0</p>
            </div>
            <div class="glass-card p-4">
                <h3 class="text-gray-600">Uptime</h3>
                <p class="text-2xl font-light" id="uptime">00:00:00</p>
            </div>
        </div>

        <!-- Control Buttons -->
        <div class="glass-card p-6 mb-8">
            <div class="flex gap-4">
                <button onclick="refreshData()" class="px-6 py-2 bg-teal-500 text-white rounded-lg hover:bg-teal-600 transition-colors">
                    🔄 Refresh
                </button>
                <button onclick="exportData()" class="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors">
                    📊 Export Data
                </button>
            </div>
        </div>

        <!-- Sensor Grid -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8" id="sensorGrid">
            <div class="glass-card p-6">
                <p class="text-gray-600">Loading sensors...</p>
            </div>
        </div>

        <!-- Charts -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div class="glass-card p-6">
                <h3 class="text-xl mb-4">Vibration Trend</h3>
                <canvas id="vibrationChart" height="200"></canvas>
            </div>
            <div class="glass-card p-6">
                <h3 class="text-xl mb-4">Temperature Trend</h3>
                <canvas id="temperatureChart" height="200"></canvas>
            </div>
        </div>
    </div>

    <script>
        const API_BASE = window.location.origin + '/api';
        let charts = {};
        let updateInterval;

        // Initialize charts
        function initCharts() {
            const chartConfig = {
                type: 'line',
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        y: { beginAtZero: true }
                    }
                }
            };

            charts.vibration = new Chart(document.getElementById('vibrationChart'), {
                ...chartConfig,
                data: {
                    labels: [],
                    datasets: [{
                        label: 'RMS Acceleration (g)',
                        data: [],
                        borderColor: '#f97316',
                        backgroundColor: 'rgba(249, 115, 22, 0.1)',
                        tension: 0.4
                    }]
                }
            });

            charts.temperature = new Chart(document.getElementById('temperatureChart'), {
                ...chartConfig,
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Temperature (°F)',
                        data: [],
                        borderColor: '#0ea5e9',
                        backgroundColor: 'rgba(14, 165, 233, 0.1)',
                        tension: 0.4
                    }]
                }
            });
        }

        // Load system status
        async function loadSystemStatus() {
            try {
                const response = await fetch(`${API_BASE}/status`);
                const status = await response.json();
                
                document.getElementById('systemStatus').textContent = status.running ? 'RUNNING' : 'STOPPED';
                document.getElementById('activeSensors').textContent = status.active_sensors ? status.active_sensors.length : 0;
                document.getElementById('totalReadings').textContent = status.total_readings || 0;
                
                if (status.start_time) {
                    updateUptime(status.start_time);
                }
            } catch (error) {
                updateConnectionStatus(false);
            }
        }

        // Load sensor data
        async function loadSensorData() {
            try {
                const response = await fetch(`${API_BASE}/readings`);
                const data = await response.json();
                displaySensors(data);
                updateCharts(data);
                updateConnectionStatus(true);
            } catch (error) {
                console.error('Failed to load data:', error);
                updateConnectionStatus(false);
            }
        }

        // Update connection status
        function updateConnectionStatus(connected) {
            const dot = document.getElementById('connectionDot');
            const status = document.getElementById('connectionStatus');
            
            if (connected) {
                dot.classList.remove('disconnected');
                dot.classList.add('connected');
                status.textContent = 'Connected';
            } else {
                dot.classList.remove('connected');
                dot.classList.add('disconnected');
                status.textContent = 'Disconnected';
            }
        }

        // Display sensors
        function displaySensors(readings) {
            const grid = document.getElementById('sensorGrid');
            
            if (Object.keys(readings).length === 0) {
                grid.innerHTML = '<div class="glass-card p-6 col-span-full"><p class="text-gray-600 text-center">No sensor data available</p></div>';
                return;
            }
            
            grid.innerHTML = '';

            Object.entries(readings).forEach(([id, reading]) => {
                const card = document.createElement('div');
                card.className = `glass-card p-6 alert-${reading.alert_level.toLowerCase()}`;
                
                card.innerHTML = `
                    <div class="flex justify-between items-start mb-4">
                        <h3 class="text-xl">${reading.name}</h3>
                        <span class="px-3 py-1 rounded-full text-xs font-medium bg-${getAlertColor(reading.alert_level)}-500 text-white">
                            ${reading.alert_level}
                        </span>
                    </div>
                    <div class="space-y-3">
                        <div class="flex justify-between">
                            <span class="text-gray-600">Temperature:</span>
                            <span class="font-medium">${reading.temperature_f.toFixed(1)}°F</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-600">RMS Acceleration:</span>
                            <span class="font-medium">${reading.metrics.rms_acceleration.toFixed(4)}g</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-600">Velocity:</span>
                            <span class="font-medium">${reading.metrics.velocity_mms.toFixed(2)} mm/s</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-600">ISO Zone:</span>
                            <span class="font-medium text-lg">${reading.metrics.iso_zone}</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-600">Frequency:</span>
                            <span class="font-medium">${reading.metrics.dominant_frequency.toFixed(1)} Hz</span>
                        </div>
                    </div>
                    <div class="mt-4 pt-4 border-t border-gray-200">
                        <div class="text-xs text-gray-500">
                            X: ${reading.acceleration.x.toFixed(3)}g, 
                            Y: ${reading.acceleration.y.toFixed(3)}g, 
                            Z: ${reading.acceleration.z.toFixed(3)}g
                        </div>
                    </div>
                `;
                
                grid.appendChild(card);
            });
        }

        // Get alert color
        function getAlertColor(level) {
            const colors = {
                'NORMAL': 'green',
                'WARNING': 'yellow',
                'CRITICAL': 'orange',
                'EMERGENCY': 'red'
            };
            return colors[level] || 'gray';
        }

        // Update charts
        function updateCharts(readings) {
            const time = new Date().toLocaleTimeString();
            
            Object.values(readings).forEach((reading, idx) => {
                if (idx === 0) { // Use first sensor for charts
                    // Update vibration chart
                    charts.vibration.data.labels.push(time);
                    charts.vibration.data.datasets[0].data.push(reading.metrics.rms_acceleration);
                    if (charts.vibration.data.labels.length > 20) {
                        charts.vibration.data.labels.shift();
                        charts.vibration.data.datasets[0].data.shift();
                    }
                    charts.vibration.update('none');

                    // Update temperature chart
                    charts.temperature.data.labels.push(time);
                    charts.temperature.data.datasets[0].data.push(reading.temperature_f);
                    if (charts.temperature.data.labels.length > 20) {
                        charts.temperature.data.labels.shift();
                        charts.temperature.data.datasets[0].data.shift();
                    }
                    charts.temperature.update('none');
                }
            });
        }

        // Update uptime
        function updateUptime(startTime) {
            const start = new Date(startTime);
            const now = new Date();
            const diff = now - start;
            
            const hours = Math.floor(diff / 3600000);
            const minutes = Math.floor((diff % 3600000) / 60000);
            const seconds = Math.floor((diff % 60000) / 1000);
            
            document.getElementById('uptime').textContent = 
                `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        }

        // Control functions
        function refreshData() {
            loadSystemStatus();
            loadSensorData();
        }

        function exportData() {
            window.open(`${API_BASE}/export/csv`, '_blank');
        }

        // Initialize
        initCharts();
        loadSystemStatus();
        loadSensorData();
        
        // Auto-refresh
        updateInterval = setInterval(() => {
            loadSystemStatus();
            loadSensorData();
        }, 2000);
    </script>
</body>
</html>
    """'''

# Replace the function
content = re.sub(pattern, new_interface, content, flags=re.DOTALL)

# Write the updated file
with open('universal_vibration_monitor.py', 'w') as f:
    f.write(content)

print("✅ Web interface updated successfully!")
print("The full dashboard is now built into the Python server.")
print("Just go to http://[IP]:5000 to see it!")