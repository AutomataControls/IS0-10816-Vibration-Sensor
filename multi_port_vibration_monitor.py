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
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import sqlite3
import json

# Flask app
app = Flask(__name__)
CORS(app)

# Global monitor instance
monitor_instance = None

# Equipment types and their ISO 10816 classifications
EQUIPMENT_TYPES = {
    "cooling_tower_motor": "Cooling Tower Motor",
    "centrifugal_pump": "Centrifugal Pump", 
    "reciprocating_compressor": "Reciprocating Compressor",
    "screw_compressor": "Screw Compressor",
    "scroll_compressor": "Scroll Compressor",
    "circulation_pump": "Circulation Pump",
    "fan_motor": "Fan Motor",
    "general_motor": "General Purpose Motor"
}

@dataclass
class EquipmentConfig:
    port: str
    equipment_name: str  # User-defined name like "Cooling_Tower_1"
    equipment_type: str
    hp: float
    voltage: int
    phase: int  # 1 or 3
    rpm: int = 1800  # default
    mounting: str = "rigid"  # rigid or flexible
    
    def get_iso_thresholds(self) -> Dict[str, float]:
        """Get ISO 10816-3 thresholds based on equipment type and power"""
        # Based on comprehensive guide for 3-50 HP motors
        
        # Determine motor group based on HP and type
        if self.hp < 15:  # Small motors (3-15 HP)
            # Group III/IV - Smaller limits for pumps and integral units
            if self.equipment_type in ["centrifugal_pump", "circulation_pump"]:
                return {
                    "zone_ab": 1.4,   # A/B boundary (Good/Acceptable)
                    "zone_bc": 2.8,   # B/C boundary (Acceptable/Unsatisfactory)
                    "zone_cd": 4.5    # C/D boundary (Unsatisfactory/Unacceptable)
                }
            else:
                # Standard small motors
                return {
                    "zone_ab": 1.4,
                    "zone_bc": 2.8,
                    "zone_cd": 4.5
                }
        else:  # Medium motors (15-50 HP)
            # Group II - Standard industrial machines
            if self.equipment_type == "cooling_tower_motor":
                # Cooling towers often have higher acceptable vibration
                return {
                    "zone_ab": 2.3,   # A/B boundary
                    "zone_bc": 4.6,   # B/C boundary
                    "zone_cd": 7.1    # C/D boundary
                }
            elif self.equipment_type in ["centrifugal_pump", "circulation_pump"]:
                # Group III - Pumps with separate drivers
                return {
                    "zone_ab": 1.4,
                    "zone_bc": 2.8,
                    "zone_cd": 4.5
                }
            else:
                # Group II - Standard medium motors
                return {
                    "zone_ab": 2.3,
                    "zone_bc": 4.6,
                    "zone_cd": 7.1
                }

@dataclass
class SensorReading:
    timestamp: datetime
    sensor_id: str  # Port-based ID like "USB1", "USB2", "USB3"
    acceleration_x: float
    acceleration_y: float
    acceleration_z: float
    temperature: float
    alert_level: str = "NORMAL"
    rms_acceleration: float = 0.0
    velocity_mms: float = 0.0
    iso_zone: str = "A"

class MultiPortVibrationMonitor:
    def __init__(self, ports: List[str]):
        """Initialize with list of serial ports"""
        self.ports = ports
        self.serial_connections = {}
        self.latest_readings = {}
        self.running = False
        self.csv_file = None
        self.csv_writer = None
        self.equipment_configs = {}  # Port -> equipment configuration
        self.configured = False
        self.config_file = "equipment_config.json"
        
        # Initialize CSV logging
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.csv_filename = f"multi_sensor_data_{timestamp}.csv"
        
        # Load saved configuration if exists
        self.load_configuration()
        
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
            'Timestamp', 'Equipment', 'Type', 'HP', 'AccelX', 'AccelY', 'AccelZ', 
            'RMS_Accel', 'Velocity_mms', 'ISO_Zone', 'Temperature', 'AlertLevel'
        ])
        
        # Initialize database
        self.init_database()
        
        print(f"\nConnected to {len(self.serial_connections)} sensors")
        print(f"CSV logging to: {self.csv_filename}")
        print(f"Database: vibration_metrics.db")
        return True
    
    def init_database(self):
        """Initialize SQLite database for metrics storage"""
        self.db_path = "vibration_metrics.db"
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create metrics table if not exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sensor_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                sensor_id TEXT NOT NULL,
                equipment_name TEXT,
                equipment_type TEXT,
                hp REAL,
                temperature_f REAL,
                accel_x REAL,
                accel_y REAL,
                accel_z REAL,
                rms_acceleration REAL,
                velocity_mms REAL,
                iso_zone TEXT,
                alert_level TEXT
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON sensor_metrics(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sensor_id ON sensor_metrics(sensor_id)')
        
        # Create hourly aggregates table for efficient querying
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS hourly_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hour_timestamp DATETIME NOT NULL,
                sensor_id TEXT NOT NULL,
                equipment_name TEXT,
                avg_temperature REAL,
                avg_rms_acceleration REAL,
                avg_velocity REAL,
                max_rms_acceleration REAL,
                max_velocity REAL,
                min_rms_acceleration REAL,
                min_velocity REAL,
                zone_a_count INTEGER DEFAULT 0,
                zone_b_count INTEGER DEFAULT 0,
                zone_c_count INTEGER DEFAULT 0,
                zone_d_count INTEGER DEFAULT 0,
                sample_count INTEGER,
                UNIQUE(hour_timestamp, sensor_id)
            )
        ''')
        
        # Clean up old data (older than 7 days)
        cursor.execute('''
            DELETE FROM sensor_metrics 
            WHERE timestamp < datetime('now', '-7 days')
        ''')
        
        cursor.execute('''
            DELETE FROM hourly_metrics 
            WHERE hour_timestamp < datetime('now', '-7 days')
        ''')
        
        conn.commit()
        conn.close()
        
        # Schedule daily cleanup
        self.schedule_cleanup()
    
    def schedule_cleanup(self):
        """Schedule daily database cleanup"""
        def cleanup():
            while self.running:
                time.sleep(86400)  # Wait 24 hours
                try:
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM sensor_metrics WHERE timestamp < datetime('now', '-7 days')")
                    cursor.execute("DELETE FROM hourly_metrics WHERE hour_timestamp < datetime('now', '-7 days')")
                    deleted = cursor.rowcount
                    conn.commit()
                    conn.close()
                    print(f"Database cleanup: Removed {deleted} old records")
                except Exception as e:
                    print(f"Database cleanup error: {e}")
        
        cleanup_thread = threading.Thread(target=cleanup, daemon=True)
        cleanup_thread.start()
    
    def save_to_database(self, reading: SensorReading, equipment_config: Optional[EquipmentConfig] = None):
        """Save sensor reading to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO sensor_metrics (
                    timestamp, sensor_id, equipment_name, equipment_type, hp,
                    temperature_f, accel_x, accel_y, accel_z,
                    rms_acceleration, velocity_mms, iso_zone, alert_level
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                reading.timestamp.isoformat(),
                reading.sensor_id,
                equipment_config.equipment_name if equipment_config else reading.sensor_id,
                equipment_config.equipment_type if equipment_config else 'unknown',
                equipment_config.hp if equipment_config else 0,
                reading.temperature,
                reading.acceleration_x,
                reading.acceleration_y,
                reading.acceleration_z,
                reading.rms_acceleration,
                reading.velocity_mms,
                reading.iso_zone,
                reading.alert_level
            ))
            
            # Update hourly aggregates
            hour_timestamp = reading.timestamp.replace(minute=0, second=0, microsecond=0)
            
            # Check if hourly record exists
            cursor.execute('''
                SELECT id FROM hourly_metrics 
                WHERE hour_timestamp = ? AND sensor_id = ?
            ''', (hour_timestamp.isoformat(), reading.sensor_id))
            
            if cursor.fetchone():
                # Update existing record
                zone_col = f"zone_{reading.iso_zone.lower()}_count"
                cursor.execute(f'''
                    UPDATE hourly_metrics SET
                        avg_temperature = (avg_temperature * sample_count + ?) / (sample_count + 1),
                        avg_rms_acceleration = (avg_rms_acceleration * sample_count + ?) / (sample_count + 1),
                        avg_velocity = (avg_velocity * sample_count + ?) / (sample_count + 1),
                        max_rms_acceleration = MAX(max_rms_acceleration, ?),
                        max_velocity = MAX(max_velocity, ?),
                        min_rms_acceleration = MIN(min_rms_acceleration, ?),
                        min_velocity = MIN(min_velocity, ?),
                        {zone_col} = {zone_col} + 1,
                        sample_count = sample_count + 1
                    WHERE hour_timestamp = ? AND sensor_id = ?
                ''', (
                    reading.temperature,
                    reading.rms_acceleration,
                    reading.velocity_mms,
                    reading.rms_acceleration,
                    reading.velocity_mms,
                    reading.rms_acceleration,
                    reading.velocity_mms,
                    hour_timestamp.isoformat(),
                    reading.sensor_id
                ))
            else:
                # Create new hourly record
                cursor.execute('''
                    INSERT INTO hourly_metrics (
                        hour_timestamp, sensor_id, equipment_name,
                        avg_temperature, avg_rms_acceleration, avg_velocity,
                        max_rms_acceleration, max_velocity,
                        min_rms_acceleration, min_velocity,
                        zone_a_count, zone_b_count, zone_c_count, zone_d_count,
                        sample_count
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    hour_timestamp.isoformat(),
                    reading.sensor_id,
                    equipment_config.equipment_name if equipment_config else reading.sensor_id,
                    reading.temperature,
                    reading.rms_acceleration,
                    reading.velocity_mms,
                    reading.rms_acceleration,
                    reading.velocity_mms,
                    reading.rms_acceleration,
                    reading.velocity_mms,
                    1 if reading.iso_zone == 'A' else 0,
                    1 if reading.iso_zone == 'B' else 0,
                    1 if reading.iso_zone == 'C' else 0,
                    1 if reading.iso_zone == 'D' else 0,
                    1
                ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Database save error: {e}")
    
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
                
                # Use equipment name if configured, otherwise use port
                if port in self.equipment_configs:
                    sensor_id = self.equipment_configs[port].equipment_name
                else:
                    sensor_id = port.split('/')[-1].upper()  # "ttyUSB1" -> "TTYUSB1"
                
                # Convert temperature
                # Register 6 is temperature in 0.01°C units
                temp_c = registers[6] / 100.0
                # If temp is 0, sensor might use different register or scaling
                if temp_c == 0:
                    temp_c = 25.0  # Default room temp
                temp_f = (temp_c * 9/5) + 32
                
                # Note: One axis will show ~1g due to gravity when stationary
                raw_x = registers[0] / 32768.0 * 16.0
                raw_y = registers[1] / 32768.0 * 16.0
                raw_z = registers[2] / 32768.0 * 16.0
                
                reading = SensorReading(
                    timestamp=datetime.now(),
                    sensor_id=sensor_id,
                    acceleration_x=raw_x,
                    acceleration_y=raw_y,
                    acceleration_z=raw_z,
                    temperature=temp_f
                )
                
                # Debug: Show raw values for each sensor on first read
                if port not in self.latest_readings:
                    print(f"\nDEBUG {sensor_id} raw accel: X={raw_x:.3f}g, Y={raw_y:.3f}g, Z={raw_z:.3f}g")
                
                # Calculate vibration RMS (subtract gravity component)
                # Total acceleration magnitude should be ~1g when stationary
                total_magnitude = np.sqrt(
                    reading.acceleration_x**2 + 
                    reading.acceleration_y**2 + 
                    reading.acceleration_z**2
                )
                
                # For stationary sensor, total should be close to 1g
                # The vibration is the deviation from 1g
                if 0.9 < total_magnitude < 1.2:
                    # Sensor is relatively stationary
                    # Vibration is approximately the deviation from 1g
                    vibration_magnitude = abs(total_magnitude - 1.0)
                    reading.rms_acceleration = vibration_magnitude
                else:
                    # High acceleration - might be actual vibration
                    # Use simple high-pass filter approach
                    # Remove DC component by subtracting mean expected gravity
                    gravity_vector_magnitude = 1.0
                    
                    # Normalize the acceleration vector
                    if total_magnitude > 0:
                        norm_x = reading.acceleration_x / total_magnitude
                        norm_y = reading.acceleration_y / total_magnitude
                        norm_z = reading.acceleration_z / total_magnitude
                        
                        # Subtract gravity component
                        vib_x = reading.acceleration_x - norm_x * gravity_vector_magnitude
                        vib_y = reading.acceleration_y - norm_y * gravity_vector_magnitude
                        vib_z = reading.acceleration_z - norm_z * gravity_vector_magnitude
                        
                        reading.rms_acceleration = np.sqrt(vib_x**2 + vib_y**2 + vib_z**2) / np.sqrt(3)
                    else:
                        reading.rms_acceleration = 0.0
                
                # Convert to velocity using typical machinery frequency
                accel_ms2 = reading.rms_acceleration * 9.81
                assumed_freq = 30.0  # Hz
                reading.velocity_mms = (accel_ms2 / (2 * np.pi * assumed_freq)) * 1000
                
                # Apply ISO 10816-3 zones based on equipment configuration
                if port in self.equipment_configs:
                    thresholds = self.equipment_configs[port].get_iso_thresholds()
                    
                    if reading.rms_acceleration < 0.01:  # Less than 0.01g is essentially stationary
                        reading.iso_zone = "A"
                        reading.alert_level = "NORMAL"
                    elif reading.velocity_mms <= thresholds["zone_ab"]:
                        reading.iso_zone = "A"  # Good
                        reading.alert_level = "NORMAL"
                    elif reading.velocity_mms <= thresholds["zone_bc"]:
                        reading.iso_zone = "B"  # Satisfactory
                        reading.alert_level = "NORMAL"
                    elif reading.velocity_mms <= thresholds["zone_cd"]:
                        reading.iso_zone = "C"  # Unsatisfactory
                        reading.alert_level = "WARNING"
                    else:
                        reading.iso_zone = "D"  # Unacceptable
                        reading.alert_level = "CRITICAL"
                else:
                    # Default thresholds if not configured
                    if reading.rms_acceleration < 0.01:
                        reading.iso_zone = "A"
                        reading.alert_level = "NORMAL"
                    elif reading.velocity_mms <= 1.8:
                        reading.iso_zone = "A"
                        reading.alert_level = "NORMAL"
                    elif reading.velocity_mms <= 4.5:
                        reading.iso_zone = "B"
                        reading.alert_level = "NORMAL"
                    elif reading.velocity_mms <= 11.0:
                        reading.iso_zone = "C"
                        reading.alert_level = "WARNING"
                    else:
                        reading.iso_zone = "D"
                        reading.alert_level = "CRITICAL"
                
                return reading
                
        except Exception as e:
            print(f"Error reading {port}: {e}")
            return None
    
    def run_monitoring(self):
        """Main monitoring loop"""
        self.running = True
        print("\nMonitoring started...")
        print("=" * 80)
        print("Gravity compensation: ON")
        print("ISO 10816-3 Vibration Standards for 3-50 HP Motors:")
        print("  Group II (15-50 HP):   Zone A: 0-2.3 | B: 2.3-4.6 | C: 4.6-7.1 | D: >7.1 mm/s")
        print("  Group III/IV (3-15 HP): Zone A: 0-1.4 | B: 1.4-2.8 | C: 2.8-4.5 | D: >4.5 mm/s")
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
                    
                    # Get ISO group info for display
                    iso_group = "?"
                    if port in self.equipment_configs:
                        hp = self.equipment_configs[port].hp
                        iso_group = "II" if hp >= 15 else "III/IV"
                    
                    print(f"{alert_symbol} {reading.timestamp.strftime('%H:%M:%S')} | "
                          f"{reading.sensor_id} | "
                          f"RMS: {reading.rms_acceleration:6.4f}g | "
                          f"Velocity: {reading.velocity_mms:5.2f}mm/s | "
                          f"ISO {iso_group}-{reading.iso_zone} | "
                          f"Temp: {reading.temperature:5.1f}°F")
                    
                    # Log to CSV
                    # Get equipment info for CSV
                    if port in self.equipment_configs:
                        eq = self.equipment_configs[port]
                        equipment_type = eq.equipment_type
                        hp = eq.hp
                    else:
                        equipment_type = "Unknown"
                        hp = 0
                    
                    self.csv_writer.writerow([
                        reading.timestamp.isoformat(),
                        reading.sensor_id,
                        equipment_type,
                        hp,
                        reading.acceleration_x,
                        reading.acceleration_y,
                        reading.acceleration_z,
                        reading.rms_acceleration,
                        reading.velocity_mms,
                        reading.iso_zone,
                        reading.temperature,
                        reading.alert_level
                    ])
                    
                    # Save to database
                    equipment_config = self.equipment_configs.get(port)
                    self.save_to_database(reading, equipment_config)
            
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
    
    def save_configuration(self):
        """Save equipment configuration to file"""
        import json
        config_data = {}
        for port, config in self.equipment_configs.items():
            config_data[port] = {
                'equipment_name': config.equipment_name,
                'equipment_type': config.equipment_type,
                'hp': config.hp,
                'voltage': config.voltage,
                'phase': config.phase,
                'rpm': config.rpm,
                'mounting': config.mounting
            }
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            print(f"Configuration saved to {self.config_file}")
        except Exception as e:
            print(f"Error saving configuration: {e}")
    
    def load_configuration(self):
        """Load equipment configuration from file"""
        import json
        if not os.path.exists(self.config_file):
            return
        
        try:
            with open(self.config_file, 'r') as f:
                config_data = json.load(f)
            
            for port, data in config_data.items():
                if port in self.ports:  # Only load config for current ports
                    self.equipment_configs[port] = EquipmentConfig(
                        port=port,
                        equipment_name=data['equipment_name'],
                        equipment_type=data['equipment_type'],
                        hp=data['hp'],
                        voltage=data['voltage'],
                        phase=data['phase'],
                        rpm=data.get('rpm', 1800),
                        mounting=data.get('mounting', 'rigid')
                    )
            
            # Check if all ports are configured
            if len(self.equipment_configs) == len(self.ports):
                self.configured = True
                
            print(f"Loaded configuration for {len(self.equipment_configs)} sensors")
        except Exception as e:
            print(f"Error loading configuration: {e}")

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
    <title>AutomataNexus Multi-Sensor Vibration Monitor</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        .font-ultralight { font-weight: 200; }
        body {
            background: linear-gradient(135deg, #f0fffc 0%, #e6fff5 20%, #f5fffa 40%, #fff5eb 60%, #ffe8d6 80%, #fff0e6 100%);
            min-height: 100vh;
        }
        .glass-card {
            background: rgba(255, 255, 255, 0.7);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.3);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            border-radius: 16px;
        }
        .alert-warning { border-color: rgba(245, 158, 11, 0.5); }
        .alert-critical { border-color: rgba(239, 68, 68, 0.5); }
        .iso-zone-a { background: linear-gradient(45deg, #10b981, #059669); }
        .iso-zone-b { background: linear-gradient(45deg, #3b82f6, #2563eb); }
        .iso-zone-c { background: linear-gradient(45deg, #f59e0b, #d97706); }
        .iso-zone-d { background: linear-gradient(45deg, #ef4444, #dc2626); }
    </style>
</head>
<body class="font-ultralight">
    <div class="container mx-auto px-4 py-8">
        <!-- Header -->
        <div class="glass-card p-6 mb-8">
            <div class="flex items-center justify-between">
                <div>
                    <h1 class="text-3xl font-ultralight text-gray-800">AutomataNexus Multi-Sensor Vibration Monitor</h1>
                    <p class="text-gray-600">ISO 10816-3 Compliant • Real-time Analysis • Industrial Equipment Monitoring</p>
                </div>
                <div class="text-right">
                    <p class="text-sm text-gray-500">Powered by Neural BMS</p>
                    <p class="text-xs text-gray-400">© 2025 AutomataNexus AI</p>
                </div>
            </div>
        </div>

        <!-- Configuration Panel (shown when not configured) -->
        <div id="configPanel" class="glass-card p-6 mb-8 hidden">
            <h2 class="text-2xl mb-6">Equipment Configuration Required</h2>
            <p class="text-gray-600 mb-6">Please configure each sensor before starting monitoring:</p>
            <div id="sensorConfigForms" class="space-y-4">
                <!-- Forms will be dynamically added here -->
            </div>
            <button onclick="saveAllConfigurations()" class="mt-6 px-6 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600">
                Start Monitoring
            </button>
        </div>

        <!-- Sensor Grid -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8" id="sensorGrid">
            <div class="glass-card p-6">
                <p class="text-gray-600">Loading sensors...</p>
            </div>
        </div>

        <!-- Combined Chart -->
        <div class="glass-card p-6" id="chartContainer">
            <h3 class="text-xl mb-4">Vibration Trends</h3>
            <div style="height: 300px; position: relative; overflow: hidden;">
                <canvas id="vibrationChart"></canvas>
            </div>
        </div>
    </div>

    <script>
        const API_BASE = window.location.origin + '/api';
        let chart;
        let systemStatus = null;
        let equipmentTypes = {};

        // Load equipment types
        async function loadEquipmentTypes() {
            try {
                const response = await fetch(`${API_BASE}/equipment-types`);
                equipmentTypes = await response.json();
            } catch (error) {
                console.error('Failed to load equipment types:', error);
            }
        }

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
                        legend: { 
                            display: true,
                            position: 'top'
                        }
                    },
                    scales: {
                        x: {
                            ticks: {
                                maxRotation: 0,
                                autoSkip: true,
                                maxTicksLimit: 10
                            }
                        },
                        y: { 
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'RMS Acceleration (g)'
                            }
                        }
                    }
                }
            });
        }

        // Load sensor data
        async function loadSensorData() {
            try {
                // First check system status
                const statusResponse = await fetch(`${API_BASE}/status`);
                systemStatus = await statusResponse.json();
                
                // Show configuration panel if not configured
                if (!systemStatus.configured && systemStatus.sensors.length > 0) {
                    showConfigurationPanel();
                    return;
                }
                
                // Load readings if configured
                const response = await fetch(`${API_BASE}/readings`);
                const data = await response.json();
                displaySensors(data);
                updateChart(data);
            } catch (error) {
                console.error('Failed to load data:', error);
            }
        }
        
        // Show configuration panel
        function showConfigurationPanel() {
            const configPanel = document.getElementById('configPanel');
            const sensorGrid = document.getElementById('sensorGrid');
            const formsDiv = document.getElementById('sensorConfigForms');
            const chartContainer = document.getElementById('chartContainer');
            
            configPanel.classList.remove('hidden');
            sensorGrid.style.display = 'none';
            if (chartContainer) chartContainer.style.display = 'none';
            
            // Create forms for each sensor
            formsDiv.innerHTML = '';
            systemStatus.sensors.forEach((sensor, index) => {
                // Get saved values if configured
                const name = sensor.configured ? sensor.name : '';
                const type = sensor.configured ? sensor.type : 'general_motor';
                const hp = sensor.configured ? sensor.hp : '';
                const voltage = sensor.configured ? sensor.voltage : '480';
                const phase = sensor.configured ? sensor.phase : '3';
                const mounting = sensor.configured ? (sensor.mounting || 'rigid') : 'rigid';
                
                const formHtml = `
                    <div class="p-4 bg-gray-50 rounded-lg ${sensor.configured ? 'border-2 border-green-300' : ''}">
                        <h3 class="font-medium mb-3">
                            Sensor ${index + 1} - Port: ${sensor.port}
                            ${sensor.configured ? '<span class="text-green-600 text-sm ml-2">(Configured)</span>' : ''}
                        </h3>
                        <div class="grid grid-cols-2 gap-4">
                            <div>
                                <label class="block text-sm mb-1">Equipment Name</label>
                                <input type="text" id="name_${sensor.port}" placeholder="e.g., Cooling_Tower_1" 
                                       value="${name}" class="w-full px-3 py-2 border rounded" required>
                            </div>
                            <div>
                                <label class="block text-sm mb-1">Equipment Type</label>
                                <select id="type_${sensor.port}" class="w-full px-3 py-2 border rounded">
                                    ${Object.entries(equipmentTypes).map(([key, value]) => 
                                        `<option value="${key}" ${key === type ? 'selected' : ''}>${value}</option>`
                                    ).join('')}
                                </select>
                            </div>
                            <div>
                                <label class="block text-sm mb-1">Motor HP</label>
                                <input type="number" id="hp_${sensor.port}" placeholder="e.g., 50" 
                                       value="${hp}" class="w-full px-3 py-2 border rounded" required>
                            </div>
                            <div>
                                <label class="block text-sm mb-1">Voltage</label>
                                <input type="number" id="voltage_${sensor.port}" placeholder="e.g., 480" 
                                       value="${voltage}" class="w-full px-3 py-2 border rounded" required>
                            </div>
                            <div>
                                <label class="block text-sm mb-1">Phase</label>
                                <select id="phase_${sensor.port}" class="w-full px-3 py-2 border rounded">
                                    <option value="3" ${phase == 3 ? 'selected' : ''}>3-Phase</option>
                                    <option value="1" ${phase == 1 ? 'selected' : ''}>Single-Phase</option>
                                </select>
                            </div>
                            <div>
                                <label class="block text-sm mb-1">Mounting</label>
                                <select id="mounting_${sensor.port}" class="w-full px-3 py-2 border rounded">
                                    <option value="rigid" ${mounting === 'rigid' ? 'selected' : ''}>Rigid</option>
                                    <option value="flexible" ${mounting === 'flexible' ? 'selected' : ''}>Flexible</option>
                                </select>
                            </div>
                        </div>
                    </div>
                `;
                formsDiv.innerHTML += formHtml;
            });
        }
        
        // Save all configurations
        async function saveAllConfigurations() {
            const sensors = systemStatus.sensors;
            let allConfigured = true;
            
            for (const sensor of sensors) {
                const port = sensor.port;
                const name = document.getElementById(`name_${port}`).value;
                const type = document.getElementById(`type_${port}`).value;
                const hp = document.getElementById(`hp_${port}`).value;
                const voltage = document.getElementById(`voltage_${port}`).value;
                const phase = document.getElementById(`phase_${port}`).value;
                const mounting = document.getElementById(`mounting_${port}`).value;
                
                if (!name || !hp || !voltage) {
                    alert('Please fill all required fields');
                    return;
                }
                
                try {
                    const response = await fetch(`${API_BASE}/configure`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            port: port,
                            equipment_name: name,
                            equipment_type: type,
                            hp: parseFloat(hp),
                            voltage: parseInt(voltage),
                            phase: parseInt(phase),
                            mounting: mounting
                        })
                    });
                    
                    const result = await response.json();
                    if (!result.success) {
                        allConfigured = false;
                        break;
                    }
                } catch (error) {
                    console.error('Configuration error:', error);
                    allConfigured = false;
                    break;
                }
            }
            
            if (allConfigured) {
                // Start monitoring via API
                fetch(`${API_BASE}/monitoring/start`, { method: 'POST' })
                    .then(response => response.json())
                    .then(result => {
                        if (result.success) {
                            document.getElementById('configPanel').classList.add('hidden');
                            document.getElementById('sensorGrid').style.display = '';
                            const chartContainer = document.getElementById('chartContainer');
                            if (chartContainer) chartContainer.style.display = '';
                            startAutoRefresh();
                            loadSensorData();
                        } else {
                            alert('Failed to start monitoring: ' + (result.error || result.message));
                        }
                    })
                    .catch(error => {
                        alert('Error starting monitoring: ' + error);
                    });
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
                const totalAccel = reading.rms_acceleration || Math.sqrt(
                    reading.acceleration.x ** 2 + 
                    reading.acceleration.y ** 2 + 
                    reading.acceleration.z ** 2
                ) / Math.sqrt(3);
                
                const card = document.createElement('div');
                card.className = `glass-card p-6`;
                
                const alertColors = {
                    'NORMAL': 'green',
                    'WARNING': 'yellow',
                    'CRITICAL': 'red'
                };
                const alertColor = alertColors[reading.alert_level] || 'gray';
                
                // Get equipment info from system status
                let equipmentInfo = "";
                if (systemStatus && systemStatus.sensors) {
                    const sensorConfig = systemStatus.sensors.find(s => 
                        s.name === id || s.port === reading.port
                    );
                    if (sensorConfig && sensorConfig.configured) {
                        equipmentInfo = `
                            <div class="text-sm text-gray-500 mb-2">
                                ${equipmentTypes[sensorConfig.type] || sensorConfig.type} • ${sensorConfig.hp} HP • ${sensorConfig.voltage}V/${sensorConfig.phase}φ
                            </div>
                        `;
                    }
                }
                
                card.innerHTML = `
                    <div class="flex justify-between items-start mb-4">
                        <div>
                            <h3 class="text-xl">${id}</h3>
                            ${equipmentInfo}
                        </div>
                        <span class="px-3 py-1 rounded-full text-xs font-medium bg-${alertColor}-500 text-white">
                            ${reading.alert_level}
                        </span>
                    </div>
                    <div class="space-y-2">
                        <div class="flex justify-between">
                            <span class="text-gray-600">Temperature:</span>
                            <span class="font-medium">${reading.temperature_f.toFixed(1)}°F</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-600">RMS Accel:</span>
                            <span class="font-medium">${totalAccel.toFixed(4)}g</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-600">Velocity:</span>
                            <span class="font-medium">${reading.velocity_mms ? reading.velocity_mms.toFixed(2) : '0.00'} mm/s</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-600">ISO Zone:</span>
                            <span class="font-medium px-2 py-1 rounded text-white text-xs iso-zone-${(reading.iso_zone || 'a').toLowerCase()}">${reading.iso_zone || 'A'}</span>
                        </div>
                        <div class="mt-3 pt-3 border-t border-gray-200">
                            <div class="text-sm text-gray-600">
                                X: ${reading.acceleration.x.toFixed(3)}g, 
                                Y: ${reading.acceleration.y.toFixed(3)}g, 
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
            const now = new Date();
            const time = now.getSeconds().toString().padStart(2, '0');
            
            // Add time label
            if (chart.data.labels.length > 20) {
                chart.data.labels.shift();
            }
            chart.data.labels.push(time);
            
            // Update or create datasets for each sensor
            Object.entries(readings).forEach(([id, reading], index) => {
                const rmsAccel = reading.rms_acceleration || 0;
                
                // Find or create dataset
                let dataset = chart.data.datasets.find(ds => ds.label === id);
                if (!dataset) {
                    const colors = ['#f97316', '#0ea5e9', '#10b981', '#a855f7'];
                    dataset = {
                        label: id,
                        data: [],
                        borderColor: colors[index % colors.length],
                        backgroundColor: colors[index % colors.length] + '20',
                        tension: 0.4,
                        borderWidth: 2,
                        pointRadius: 0
                    };
                    chart.data.datasets.push(dataset);
                }
                
                // Add data point
                dataset.data.push(rmsAccel);
                if (dataset.data.length > 20) {
                    dataset.data.shift();
                }
            });
            
            chart.update('none');
        }

        // Initialize
        let refreshInterval = null;
        initChart();
        loadEquipmentTypes().then(() => {
            loadSensorData();
        });
        
        // Auto-refresh only when configured
        function startAutoRefresh() {
            if (!refreshInterval) {
                refreshInterval = setInterval(() => {
                    if (systemStatus && systemStatus.configured) {
                        loadSensorData();
                    }
                }, 1000);
            }
        }
    </script>
</body>
</html>
    """

@app.route('/api/status')
def get_status():
    """Get system status"""
    if monitor_instance:
        # Build sensor config info
        sensor_configs = []
        for port in monitor_instance.serial_connections.keys():
            if port in monitor_instance.equipment_configs:
                config = monitor_instance.equipment_configs[port]
                sensor_configs.append({
                    'port': port,
                    'name': config.equipment_name,
                    'type': config.equipment_type,
                    'hp': config.hp,
                    'voltage': config.voltage,
                    'phase': config.phase,
                    'configured': True
                })
            else:
                sensor_configs.append({
                    'port': port,
                    'name': port.split('/')[-1].upper(),
                    'configured': False
                })
        
        return jsonify({
            'running': monitor_instance.running,
            'configured': monitor_instance.configured,
            'sensors': sensor_configs,
            'active_sensors': len(monitor_instance.serial_connections),
            'total_readings': len(monitor_instance.latest_readings),
            'start_time': datetime.now().isoformat()
        })
    
    # Even if monitor not fully initialized, try to detect sensors
    ports = ['/dev/ttyUSB0', '/dev/ttyUSB1', '/dev/ttyUSB2', '/dev/ttyUSB3', '/dev/ttyUSB4']
    detected_sensors = []
    
    for port in ports:
        if os.path.exists(port):
            detected_sensors.append({
                'port': port,
                'name': port.split('/')[-1].upper(),
                'configured': False
            })
    
    return jsonify({
        'running': False,
        'configured': False,
        'sensors': detected_sensors,
        'active_sensors': 0,
        'total_readings': 0,
        'start_time': datetime.now().isoformat()
    })

@app.route('/api/configure', methods=['POST'])
def configure_equipment():
    """Configure equipment for each sensor"""
    global monitor_instance
    
    data = request.json
    port = data.get('port')
    
    # If monitor not initialized, initialize it now
    if not monitor_instance:
        ports = ['/dev/ttyUSB0', '/dev/ttyUSB1', '/dev/ttyUSB2', '/dev/ttyUSB3', '/dev/ttyUSB4']
        monitor_instance = MultiPortVibrationMonitor(ports)
        if not monitor_instance.connect_sensors():
            return jsonify({'error': 'Failed to connect to sensors'}), 500
    
    if port not in monitor_instance.serial_connections:
        return jsonify({'error': 'Invalid port'}), 400
    
    # Create equipment configuration
    config = EquipmentConfig(
        port=port,
        equipment_name=data.get('equipment_name', f'Equipment_{port}'),
        equipment_type=data.get('equipment_type', 'general_motor'),
        hp=float(data.get('hp', 20)),
        voltage=int(data.get('voltage', 480)),
        phase=int(data.get('phase', 3)),
        rpm=int(data.get('rpm', 1800)),
        mounting=data.get('mounting', 'rigid')
    )
    
    monitor_instance.equipment_configs[port] = config
    
    # Check if all sensors are configured
    if len(monitor_instance.equipment_configs) == len(monitor_instance.serial_connections):
        monitor_instance.configured = True
    
    # Save configuration to file
    monitor_instance.save_configuration()
    
    return jsonify({'success': True, 'configured': monitor_instance.configured})

@app.route('/api/equipment-types')
def get_equipment_types():
    """Get available equipment types"""
    return jsonify(EQUIPMENT_TYPES)

@app.route('/api/monitoring/start', methods=['POST'])
def start_monitoring():
    """Start monitoring if configured"""
    global monitor_instance
    
    # If monitor not initialized, initialize it now
    if not monitor_instance:
        ports = ['/dev/ttyUSB0', '/dev/ttyUSB1', '/dev/ttyUSB2', '/dev/ttyUSB3', '/dev/ttyUSB4']
        monitor_instance = MultiPortVibrationMonitor(ports)
        if not monitor_instance.connect_sensors():
            return jsonify({'error': 'Failed to connect to sensors'}), 500
    
    if not monitor_instance.configured:
        return jsonify({'error': 'Equipment not configured'}), 400
    
    if monitor_instance.running:
        return jsonify({'message': 'Already running'}), 200
    
    # Start monitoring in a separate thread
    monitor_thread = threading.Thread(target=monitor_instance.run_monitoring)
    monitor_thread.daemon = True
    monitor_thread.start()
    
    return jsonify({'success': True, 'message': 'Monitoring started'})

@app.route('/api/monitoring/stop', methods=['POST'])  
def stop_monitoring():
    """Stop monitoring"""
    if not monitor_instance:
        return jsonify({'error': 'Monitor not initialized'}), 503
    
    monitor_instance.running = False
    time.sleep(2)  # Give it time to stop
    
    return jsonify({'success': True, 'message': 'Monitoring stopped'})

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
                'rms_acceleration': reading.rms_acceleration,
                'velocity_mms': reading.velocity_mms,
                'iso_zone': reading.iso_zone,
                'alert_level': reading.alert_level
            }
        return jsonify(readings)
    return jsonify({})

@app.route('/api/metrics/history')
def get_metrics_history():
    """Get historical metrics from database
    Query params:
    - sensor_id: specific sensor ID (optional)
    - hours: number of hours to retrieve (default 24, max 168)
    - interval: 'raw' or 'hourly' (default 'hourly')
    """
    try:
        sensor_id = request.args.get('sensor_id')
        hours = min(int(request.args.get('hours', 24)), 168)  # Max 7 days
        interval = request.args.get('interval', 'hourly')
        
        conn = sqlite3.connect('vibration_metrics.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if interval == 'hourly':
            # Get hourly aggregates
            query = '''
                SELECT * FROM hourly_metrics 
                WHERE hour_timestamp > datetime('now', '-{} hours')
                {}
                ORDER BY hour_timestamp, sensor_id
            '''.format(hours, 'AND sensor_id = ?' if sensor_id else '')
            
            if sensor_id:
                cursor.execute(query, (sensor_id,))
            else:
                cursor.execute(query)
                
            rows = cursor.fetchall()
            
            result = []
            for row in rows:
                result.append({
                    'timestamp': row['hour_timestamp'],
                    'sensor_id': row['sensor_id'],
                    'equipment_name': row['equipment_name'],
                    'avg_temperature': row['avg_temperature'],
                    'avg_rms_acceleration': row['avg_rms_acceleration'],
                    'avg_velocity': row['avg_velocity'],
                    'max_rms_acceleration': row['max_rms_acceleration'],
                    'max_velocity': row['max_velocity'],
                    'min_rms_acceleration': row['min_rms_acceleration'],
                    'min_velocity': row['min_velocity'],
                    'zone_distribution': {
                        'A': row['zone_a_count'],
                        'B': row['zone_b_count'],
                        'C': row['zone_c_count'],
                        'D': row['zone_d_count']
                    },
                    'sample_count': row['sample_count']
                })
        else:
            # Get raw data
            query = '''
                SELECT * FROM sensor_metrics 
                WHERE timestamp > datetime('now', '-{} hours')
                {}
                ORDER BY timestamp DESC
                LIMIT 1000
            '''.format(hours, 'AND sensor_id = ?' if sensor_id else '')
            
            if sensor_id:
                cursor.execute(query, (sensor_id,))
            else:
                cursor.execute(query)
                
            rows = cursor.fetchall()
            
            result = []
            for row in rows:
                result.append({
                    'timestamp': row['timestamp'],
                    'sensor_id': row['sensor_id'],
                    'equipment_name': row['equipment_name'],
                    'equipment_type': row['equipment_type'],
                    'temperature_f': row['temperature_f'],
                    'rms_acceleration': row['rms_acceleration'],
                    'velocity_mms': row['velocity_mms'],
                    'iso_zone': row['iso_zone'],
                    'alert_level': row['alert_level']
                })
        
        conn.close()
        return jsonify({
            'data': result,
            'query': {
                'sensor_id': sensor_id,
                'hours': hours,
                'interval': interval,
                'count': len(result)
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/metrics/summary')
def get_metrics_summary():
    """Get summary statistics for all sensors
    Query params:
    - hours: number of hours to summarize (default 24)
    """
    try:
        hours = min(int(request.args.get('hours', 24)), 168)
        
        conn = sqlite3.connect('vibration_metrics.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get summary for each sensor
        query = '''
            SELECT 
                sensor_id,
                equipment_name,
                COUNT(*) as total_readings,
                AVG(temperature_f) as avg_temperature,
                MIN(temperature_f) as min_temperature,
                MAX(temperature_f) as max_temperature,
                AVG(rms_acceleration) as avg_rms_acceleration,
                MIN(rms_acceleration) as min_rms_acceleration,
                MAX(rms_acceleration) as max_rms_acceleration,
                AVG(velocity_mms) as avg_velocity,
                MIN(velocity_mms) as min_velocity,
                MAX(velocity_mms) as max_velocity,
                SUM(CASE WHEN iso_zone = 'A' THEN 1 ELSE 0 END) as zone_a_count,
                SUM(CASE WHEN iso_zone = 'B' THEN 1 ELSE 0 END) as zone_b_count,
                SUM(CASE WHEN iso_zone = 'C' THEN 1 ELSE 0 END) as zone_c_count,
                SUM(CASE WHEN iso_zone = 'D' THEN 1 ELSE 0 END) as zone_d_count,
                MAX(timestamp) as last_reading
            FROM sensor_metrics
            WHERE timestamp > datetime('now', '-{} hours')
            GROUP BY sensor_id
        '''.format(hours)
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        result = {}
        for row in rows:
            total = row['total_readings']
            result[row['sensor_id']] = {
                'equipment_name': row['equipment_name'],
                'total_readings': total,
                'last_reading': row['last_reading'],
                'temperature': {
                    'avg': round(row['avg_temperature'], 1),
                    'min': round(row['min_temperature'], 1),
                    'max': round(row['max_temperature'], 1)
                },
                'rms_acceleration': {
                    'avg': round(row['avg_rms_acceleration'], 4),
                    'min': round(row['min_rms_acceleration'], 4),
                    'max': round(row['max_rms_acceleration'], 4)
                },
                'velocity': {
                    'avg': round(row['avg_velocity'], 2),
                    'min': round(row['min_velocity'], 2),
                    'max': round(row['max_velocity'], 2)
                },
                'zone_distribution': {
                    'A': row['zone_a_count'],
                    'B': row['zone_b_count'],
                    'C': row['zone_c_count'],
                    'D': row['zone_d_count'],
                    'A_percent': round((row['zone_a_count'] / total) * 100, 1) if total > 0 else 0,
                    'B_percent': round((row['zone_b_count'] / total) * 100, 1) if total > 0 else 0,
                    'C_percent': round((row['zone_c_count'] / total) * 100, 1) if total > 0 else 0,
                    'D_percent': round((row['zone_d_count'] / total) * 100, 1) if total > 0 else 0
                }
            }
        
        conn.close()
        return jsonify({
            'summary': result,
            'query': {
                'hours': hours,
                'sensor_count': len(result)
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/metrics/alerts')
def get_alerts():
    """Get recent alerts (Zone C and D events)
    Query params:
    - hours: number of hours to check (default 24)
    - limit: max number of alerts (default 100)
    """
    try:
        hours = min(int(request.args.get('hours', 24)), 168)
        limit = min(int(request.args.get('limit', 100)), 500)
        
        conn = sqlite3.connect('vibration_metrics.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = '''
            SELECT * FROM sensor_metrics
            WHERE timestamp > datetime('now', '-{} hours')
            AND iso_zone IN ('C', 'D')
            ORDER BY timestamp DESC
            LIMIT {}
        '''.format(hours, limit)
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        alerts = []
        for row in rows:
            alerts.append({
                'timestamp': row['timestamp'],
                'sensor_id': row['sensor_id'],
                'equipment_name': row['equipment_name'],
                'iso_zone': row['iso_zone'],
                'alert_level': row['alert_level'],
                'velocity_mms': row['velocity_mms'],
                'rms_acceleration': row['rms_acceleration'],
                'temperature_f': row['temperature_f']
            })
        
        conn.close()
        return jsonify({
            'alerts': alerts,
            'count': len(alerts),
            'query': {
                'hours': hours,
                'limit': limit
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def main():
    global monitor_instance
    
    print("╔════════════════════════════════════════════════════════════════════════════════════╗")
    print("║                        AutomataNexus Multi-Port Vibration Monitor                  ║")
    print("║                     Enterprise WitMotion WTVB01-485 Integration                    ║")
    print("║                          ISO 10816-3 Compliant Analysis System                     ║")
    print("║                          (c) 2025 AutomataNexus AI & AutomataControls              ║")
    print("╚════════════════════════════════════════════════════════════════════════════════════╝")
    print("")
    print("MULTI-PORT VIBRATION MONITORING SYSTEM")
    print("Real-time Analysis | Web Dashboard | CSV Logging")
    print("=" * 90)
    
    # Define the ports to check - it will skip any that don't exist
    ports = ['/dev/ttyUSB0', '/dev/ttyUSB1', '/dev/ttyUSB2', '/dev/ttyUSB3', '/dev/ttyUSB4']
    
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
    
    # Check if already configured
    if monitor_instance.configured:
        print("Found saved configuration. Starting monitoring automatically...")
        # Start monitoring in a separate thread
        monitor_thread = threading.Thread(target=monitor_instance.run_monitoring)
        monitor_thread.daemon = True
        monitor_thread.start()
    else:
        print("\nNo configuration found. Please configure equipment via web interface.")
        print(f"Open http://localhost:{api_port} to configure sensors.")
    
    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        monitor_instance.running = False
        monitor_instance.stop()

if __name__ == "__main__":
    main()