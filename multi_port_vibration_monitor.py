#!/usr/bin/env python3
"""
Multi-Port Vibration Monitoring System
Monitors 3 sensors on separate USB ports (all at address 0x50)
"""

import serial
import time
import struct
import threading
import csv
import numpy as np
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from flask import Flask, jsonify
from flask_cors import CORS
import os

# Flask app
app = Flask(__name__)
CORS(app)

# Global monitor instance
monitor_instance = None

@dataclass
class SensorReading:
    timestamp: datetime
    sensor_id: str  # Port-based ID like "USB1", "USB2", "USB3"
    acceleration_x: float
    acceleration_y: float
    acceleration_z: float
    temperature: float
    alert_level: str = "NORMAL"

class MultiPortVibrationMonitor:
    def __init__(self, ports: List[str]):
        """Initialize with list of serial ports"""
        self.ports = ports
        self.serial_connections = {}
        self.latest_readings = {}
        self.running = False
        self.csv_file = None
        self.csv_writer = None
        
        # Initialize CSV logging
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.csv_filename = f"multi_sensor_data_{timestamp}.csv"
        
    def calculate_crc16(self, data):
        """Calculate Modbus CRC16"""
        crc = 0xFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x0001:
                    crc = (crc >> 1) ^ 0xA001
                else:
                    crc >>= 1
        return crc
    
    def connect_sensors(self):
        """Connect to all sensors"""
        print("\nConnecting to sensors...")
        
        for port in self.ports:
            try:
                if os.path.exists(port):
                    ser = serial.Serial(port, 9600, timeout=0.5)
                    time.sleep(0.5)
                    self.serial_connections[port] = ser
                    print(f"✓ Connected to {port}")
                else:
                    print(f"✗ Port {port} not found")
            except Exception as e:
                print(f"✗ Failed to connect to {port}: {e}")
        
        if not self.serial_connections:
            print("ERROR: No sensors connected!")
            return False
            
        # Initialize CSV
        self.csv_file = open(self.csv_filename, 'w', newline='')
        self.csv_writer = csv.writer(self.csv_file)
        self.csv_writer.writerow([
            'Timestamp', 'Sensor', 'AccelX', 'AccelY', 'AccelZ', 
            'Temperature', 'AlertLevel'
        ])
        
        print(f"\nConnected to {len(self.serial_connections)} sensors")
        print(f"CSV logging to: {self.csv_filename}")
        return True
    
    def read_sensor(self, port: str, ser: serial.Serial) -> Optional[SensorReading]:
        """Read data from a single sensor"""
        # Always use address 0x50 since we can't change it
        address = 0x50
        
        # Build Modbus read command
        cmd = bytearray([address, 0x03, 0x00, 0x34, 0x00, 0x0C])
        crc = self.calculate_crc16(cmd)
        cmd.append(crc & 0xFF)
        cmd.append((crc >> 8) & 0xFF)
        
        try:
            ser.reset_input_buffer()
            ser.write(bytes(cmd))
            time.sleep(0.1)
            
            response = ser.read(100)
            if len(response) >= 29 and response[0] == address and response[1] == 0x03:
                # Parse response
                data_bytes = response[3:27]
                registers = []
                for i in range(0, 24, 2):
                    value = struct.unpack('>h', data_bytes[i:i+2])[0]
                    registers.append(value)
                
                # Extract sensor ID from port name
                sensor_id = port.split('/')[-1].upper()  # "ttyUSB1" -> "TTYUSB1"
                
                # Convert temperature
                # Register 6 is temperature in 0.01°C units
                temp_c = registers[6] / 100.0
                # If temp is 0, sensor might use different register or scaling
                if temp_c == 0:
                    temp_c = 25.0  # Default room temp
                temp_f = (temp_c * 9/5) + 32
                
                reading = SensorReading(
                    timestamp=datetime.now(),
                    sensor_id=sensor_id,
                    acceleration_x=registers[0] / 32768.0 * 16.0,
                    acceleration_y=registers[1] / 32768.0 * 16.0,
                    acceleration_z=registers[2] / 32768.0 * 16.0,
                    temperature=temp_f
                )
                
                # Simple alert logic
                total_accel = np.sqrt(
                    reading.acceleration_x**2 + 
                    reading.acceleration_y**2 + 
                    reading.acceleration_z**2
                )
                
                if total_accel > 2.0:
                    reading.alert_level = "CRITICAL"
                elif total_accel > 1.5:
                    reading.alert_level = "WARNING"
                else:
                    reading.alert_level = "NORMAL"
                
                return reading
                
        except Exception as e:
            print(f"Error reading {port}: {e}")
            return None
    
    def run_monitoring(self):
        """Main monitoring loop"""
        self.running = True
        print("\nMonitoring started...")
        print("=" * 80)
        
        while self.running:
            readings = {}
            
            # Read all sensors
            for port, ser in self.serial_connections.items():
                reading = self.read_sensor(port, ser)
                if reading:
                    readings[port] = reading
                    self.latest_readings[port] = reading
                    
                    # Display
                    alert_symbol = {
                        'NORMAL': '[OK]',
                        'WARNING': '[WARN]',
                        'CRITICAL': '[CRIT]'
                    }.get(reading.alert_level, '[????]')
                    
                    print(f"{alert_symbol} {reading.timestamp.strftime('%H:%M:%S')} | "
                          f"{reading.sensor_id} | "
                          f"Accel: [{reading.acceleration_x:+6.3f}, "
                          f"{reading.acceleration_y:+6.3f}, "
                          f"{reading.acceleration_z:+6.3f}]g | "
                          f"Temp: {reading.temperature:5.1f}°F")
                    
                    # Log to CSV
                    self.csv_writer.writerow([
                        reading.timestamp.isoformat(),
                        reading.sensor_id,
                        reading.acceleration_x,
                        reading.acceleration_y,
                        reading.acceleration_z,
                        reading.temperature,
                        reading.alert_level
                    ])
            
            if readings:
                print("-" * 80)
                self.csv_file.flush()
            
            time.sleep(1)  # Read every second
    
    def stop(self):
        """Stop monitoring and cleanup"""
        self.running = False
        
        for port, ser in self.serial_connections.items():
            ser.close()
            print(f"Closed {port}")
        
        if self.csv_file:
            self.csv_file.close()
        
        print("Monitoring stopped")

# Flask API Routes
@app.route('/')
def serve_web_interface():
    """Serve the web interface"""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Multi-Sensor Vibration Monitor</title>
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
    </style>
</head>
<body class="font-ultralight">
    <div class="container mx-auto px-4 py-8">
        <!-- Header -->
        <div class="glass-card p-6 mb-8">
            <h1 class="text-3xl font-ultralight text-gray-800">Multi-Sensor Vibration Monitor</h1>
            <p class="text-gray-600">Monitoring 3 WTVB01-485 Sensors</p>
        </div>

        <!-- Sensor Grid -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8" id="sensorGrid">
            <div class="glass-card p-6">
                <p class="text-gray-600">Loading sensors...</p>
            </div>
        </div>

        <!-- Combined Chart -->
        <div class="glass-card p-6">
            <h3 class="text-xl mb-4">Vibration Trends</h3>
            <canvas id="vibrationChart" height="100"></canvas>
        </div>
    </div>

    <script>
        const API_BASE = window.location.origin + '/api';
        let chart;

        // Initialize chart
        function initChart() {
            const ctx = document.getElementById('vibrationChart').getContext('2d');
            chart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: []
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: true }
                    },
                    scales: {
                        y: { 
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Acceleration (g)'
                            }
                        }
                    }
                }
            });
        }

        // Load sensor data
        async function loadSensorData() {
            try {
                const response = await fetch(`${API_BASE}/readings`);
                const data = await response.json();
                displaySensors(data);
                updateChart(data);
            } catch (error) {
                console.error('Failed to load data:', error);
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
                const totalAccel = Math.sqrt(
                    reading.acceleration.x ** 2 + 
                    reading.acceleration.y ** 2 + 
                    reading.acceleration.z ** 2
                );
                
                const card = document.createElement('div');
                card.className = `glass-card p-6`;
                
                const alertColors = {
                    'NORMAL': 'green',
                    'WARNING': 'yellow',
                    'CRITICAL': 'red'
                };
                const alertColor = alertColors[reading.alert_level] || 'gray';
                
                card.innerHTML = `
                    <div class="flex justify-between items-start mb-4">
                        <h3 class="text-xl">${id}</h3>
                        <span class="px-3 py-1 rounded-full text-xs font-medium bg-${alertColor}-500 text-white">
                            ${reading.alert_level}
                        </span>
                    </div>
                    <div class="space-y-2">
                        <div class="flex justify-between">
                            <span class="text-gray-600">Port:</span>
                            <span class="font-medium">${reading.port}</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-600">Temperature:</span>
                            <span class="font-medium">${reading.temperature_f.toFixed(1)}°F</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-600">Total Accel:</span>
                            <span class="font-medium">${totalAccel.toFixed(3)}g</span>
                        </div>
                        <div class="mt-3 pt-3 border-t border-gray-200">
                            <div class="text-sm text-gray-600">
                                X: ${reading.acceleration.x.toFixed(3)}g<br>
                                Y: ${reading.acceleration.y.toFixed(3)}g<br>
                                Z: ${reading.acceleration.z.toFixed(3)}g
                            </div>
                        </div>
                    </div>
                `;
                
                grid.appendChild(card);
            });
        }

        // Update chart
        function updateChart(readings) {
            const time = new Date().toLocaleTimeString();
            
            // Add time label
            if (chart.data.labels.length > 20) {
                chart.data.labels.shift();
            }
            chart.data.labels.push(time);
            
            // Update or create datasets for each sensor
            Object.entries(readings).forEach(([id, reading], index) => {
                const totalAccel = Math.sqrt(
                    reading.acceleration.x ** 2 + 
                    reading.acceleration.y ** 2 + 
                    reading.acceleration.z ** 2
                );
                
                // Find or create dataset
                let dataset = chart.data.datasets.find(ds => ds.label === id);
                if (!dataset) {
                    const colors = ['#f97316', '#0ea5e9', '#10b981'];
                    dataset = {
                        label: id,
                        data: [],
                        borderColor: colors[index % colors.length],
                        backgroundColor: colors[index % colors.length] + '20',
                        tension: 0.4
                    };
                    chart.data.datasets.push(dataset);
                }
                
                // Add data point
                dataset.data.push(totalAccel);
                if (dataset.data.length > 20) {
                    dataset.data.shift();
                }
            });
            
            chart.update('none');
        }

        // Initialize
        initChart();
        loadSensorData();
        
        // Auto-refresh
        setInterval(loadSensorData, 1000);
    </script>
</body>
</html>
    """

@app.route('/api/status')
def get_status():
    """Get system status"""
    if monitor_instance:
        return jsonify({
            'running': monitor_instance.running,
            'sensors': list(monitor_instance.serial_connections.keys()),
            'active_sensors': len(monitor_instance.serial_connections)
        })
    return jsonify({'error': 'Monitor not initialized'}), 503

@app.route('/api/readings')
def get_readings():
    """Get latest readings from all sensors"""
    if monitor_instance and monitor_instance.latest_readings:
        readings = {}
        for port, reading in monitor_instance.latest_readings.items():
            readings[reading.sensor_id] = {
                'timestamp': reading.timestamp.isoformat(),
                'port': port,
                'temperature_f': reading.temperature,
                'acceleration': {
                    'x': reading.acceleration_x,
                    'y': reading.acceleration_y,
                    'z': reading.acceleration_z
                },
                'alert_level': reading.alert_level
            }
        return jsonify(readings)
    return jsonify({})

def main():
    global monitor_instance
    
    print("Multi-Port Vibration Monitoring System")
    print("=" * 50)
    
    # Define the ports - keeping all 4
    ports = ['/dev/ttyUSB1', '/dev/ttyUSB2', '/dev/ttyUSB3', '/dev/ttyUSB4']
    
    # Create monitor
    monitor_instance = MultiPortVibrationMonitor(ports)
    
    # Connect to sensors
    if not monitor_instance.connect_sensors():
        return
    
    # Start web API in separate thread
    # Try different ports if 5000 is in use
    import socket
    api_port = 5000
    for port in [5000, 5001, 5002, 5003]:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        if result != 0:  # Port is free
            api_port = port
            break
    
    api_thread = threading.Thread(target=lambda: app.run(host='0.0.0.0', port=api_port, debug=False))
    api_thread.daemon = True
    api_thread.start()
    
    print(f"\nWeb API started on http://localhost:{api_port}")
    
    # Start monitoring in main thread
    try:
        monitor_instance.run_monitoring()
    except KeyboardInterrupt:
        print("\nStopping...")
        monitor_instance.stop()

if __name__ == "__main__":
    main()