#!/usr/bin/env python3
"""
################################################################################
# Neural BMS - Universal Vibration Monitoring System
# Enterprise-Grade Industrial Sensor Integration with Web API
################################################################################

(c) 2025 AutomataNexus AI & AutomataControls
Author: Andrew Jewell Sr. - Dev Ops Automata Controls BMS / Automata Nexus AI
License: Commercial License Required
Contact: DevOps@automatacontrols.com

Universal monitoring system with REST API for web interface integration
"""

import serial
import time
import struct
import threading
import csv
import numpy as np
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable
from collections import deque
import json
import os
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import logging

try:
    import RPi.GPIO as GPIO
    ON_PI = True
except:
    ON_PI = False

# Flask app for web API
app = Flask(__name__)
CORS(app)  # Enable CORS for web interface

# Global monitor instance
monitor_instance = None

@dataclass
class SensorConfig:
    """Dynamic sensor configuration"""
    address: int
    name: str
    type: str
    location: str
    power_hp: float
    power_kw: float
    rpm_nominal: int
    enabled: bool = True
    custom_thresholds: dict = field(default_factory=dict)

@dataclass
class VibrationMetrics:
    """Comprehensive vibration analysis metrics"""
    rms_acceleration: float = 0.0
    peak_acceleration: float = 0.0
    peak_to_peak: float = 0.0
    crest_factor: float = 0.0
    vibration_velocity_rms: float = 0.0
    vibration_displacement_rms: float = 0.0
    dominant_frequency: float = 0.0
    frequency_spectrum: List[float] = field(default_factory=list)
    frequency_bins: List[float] = field(default_factory=list)
    iso_zone: str = ""
    
@dataclass 
class SensorReading:
    timestamp: datetime
    sensor_id: int
    acceleration_x: float
    acceleration_y: float
    acceleration_z: float
    angular_velocity_x: float
    angular_velocity_y: float
    angular_velocity_z: float
    angle_x: float
    angle_y: float
    angle_z: float
    temperature: float
    vibration_metrics: Optional[VibrationMetrics] = None
    alert_level: str = "NORMAL"
    sensor_config: Optional[SensorConfig] = None

@dataclass
class AlertThresholds:
    """Dynamic alert thresholds"""
    # Can be overridden per sensor
    rms_accel_warning: float = 0.05
    rms_accel_critical: float = 0.15
    rms_accel_emergency: float = 0.30
    peak_accel_warning: float = 0.20
    peak_accel_critical: float = 0.50
    peak_accel_emergency: float = 1.00
    velocity_warning: float = 1.8
    velocity_critical: float = 4.5
    velocity_emergency: float = 11.0
    temp_warning: float = 158.0
    temp_critical: float = 194.0
    motor_frequency: float = 60.0
    bearing_defect_warning: float = 0.02
    unbalance_warning: float = 0.03
    misalignment_warning: float = 0.025

class VibrationAnalyzer:
    """Advanced vibration analysis engine"""
    
    def __init__(self, sample_rate=2.0, window_size=128):
        self.sample_rate = sample_rate
        self.window_size = window_size
        self.data_buffer = deque(maxlen=window_size)
        
    def add_sample(self, acceleration_magnitude: float):
        """Add acceleration sample to analysis buffer"""
        vibration_magnitude = abs(acceleration_magnitude - 1.0)
        self.data_buffer.append(vibration_magnitude)
        
    def calculate_metrics(self) -> Optional[VibrationMetrics]:
        """Calculate comprehensive vibration metrics"""
        if len(self.data_buffer) < self.window_size // 2:
            return None
            
        data = np.array(list(self.data_buffer))
        
        # Time domain analysis
        rms = np.sqrt(np.mean(data**2))
        peak = np.max(np.abs(data))
        peak_to_peak = np.max(data) - np.min(data)
        crest_factor = peak / rms if rms > 0 else 0
        
        # Frequency domain analysis
        if len(data) >= 32:
            windowed_data = data * np.hanning(len(data))
            fft = np.fft.rfft(windowed_data)
            magnitude_spectrum = np.abs(fft)
            freq_bins = np.fft.rfftfreq(len(data), 1/self.sample_rate)
            
            # Find dominant frequency
            freq_mask = freq_bins >= 5.0
            if np.any(freq_mask):
                masked_spectrum = magnitude_spectrum.copy()
                masked_spectrum[~freq_mask] = 0
                dominant_freq_idx = np.argmax(masked_spectrum)
                dominant_frequency = freq_bins[dominant_freq_idx]
                
                if magnitude_spectrum[dominant_freq_idx] < (np.max(magnitude_spectrum) * 0.1):
                    dominant_frequency = 0.0
            else:
                dominant_frequency = 0.0
            
            # Calculate velocity and displacement
            velocity_spectrum = np.zeros_like(magnitude_spectrum)
            non_zero_mask = freq_bins > 0.01
            velocity_spectrum[non_zero_mask] = magnitude_spectrum[non_zero_mask] / (2 * np.pi * freq_bins[non_zero_mask])
            velocity_rms = np.sqrt(np.sum(velocity_spectrum**2)) / len(velocity_spectrum)
            
            displacement_spectrum = np.zeros_like(velocity_spectrum)
            displacement_spectrum[non_zero_mask] = velocity_spectrum[non_zero_mask] / (2 * np.pi * freq_bins[non_zero_mask])
            displacement_rms = np.sqrt(np.sum(displacement_spectrum**2)) / len(displacement_spectrum)
            
        else:
            dominant_frequency = 0.0
            velocity_rms = rms * 9.81 * 1000 / (2 * np.pi * 10)
            displacement_rms = velocity_rms / (2 * np.pi * 10)
            magnitude_spectrum = []
            freq_bins = []
        
        # Determine ISO zone based on velocity
        iso_zone = ""
        if velocity_rms < 1.8:
            iso_zone = "A"
        elif velocity_rms < 4.5:
            iso_zone = "B"
        elif velocity_rms < 11.0:
            iso_zone = "C"
        else:
            iso_zone = "D"
        
        return VibrationMetrics(
            rms_acceleration=float(rms),
            peak_acceleration=float(peak),
            peak_to_peak=float(peak_to_peak),
            crest_factor=float(crest_factor),
            vibration_velocity_rms=float(velocity_rms),
            vibration_displacement_rms=float(displacement_rms * 1000),
            dominant_frequency=float(dominant_frequency),
            frequency_spectrum=magnitude_spectrum.tolist() if len(magnitude_spectrum) > 0 else [],
            frequency_bins=freq_bins.tolist() if len(freq_bins) > 0 else [],
            iso_zone=iso_zone
        )

class AlertManager:
    """Dynamic alert management system"""
    
    def __init__(self, default_thresholds: AlertThresholds):
        self.default_thresholds = default_thresholds
        self.alert_history = deque(maxlen=1000)
        self.active_alerts = {}
        
    def evaluate_reading(self, reading: SensorReading) -> str:
        """Evaluate sensor reading with dynamic thresholds"""
        alerts = []
        
        # Get sensor-specific thresholds or use defaults
        thresholds = self.default_thresholds
        if reading.sensor_config and reading.sensor_config.custom_thresholds:
            # Override with custom thresholds
            custom = reading.sensor_config.custom_thresholds
            for key, value in custom.items():
                if hasattr(thresholds, key):
                    setattr(thresholds, key, value)
        
        if reading.vibration_metrics:
            metrics = reading.vibration_metrics
            
            # RMS Acceleration alerts
            if metrics.rms_acceleration >= thresholds.rms_accel_emergency:
                alerts.append(("EMERGENCY", f"RMS {metrics.rms_acceleration:.3f}g exceeds emergency threshold"))
            elif metrics.rms_acceleration >= thresholds.rms_accel_critical:
                alerts.append(("CRITICAL", f"RMS {metrics.rms_acceleration:.3f}g exceeds critical threshold"))
            elif metrics.rms_acceleration >= thresholds.rms_accel_warning:
                alerts.append(("WARNING", f"RMS {metrics.rms_acceleration:.3f}g exceeds warning threshold"))
            
            # Vibration velocity alerts
            if metrics.vibration_velocity_rms >= thresholds.velocity_emergency:
                alerts.append(("EMERGENCY", f"Velocity {metrics.vibration_velocity_rms:.2f}mm/s in UNACCEPTABLE zone"))
            elif metrics.vibration_velocity_rms >= thresholds.velocity_critical:
                alerts.append(("CRITICAL", f"Velocity {metrics.vibration_velocity_rms:.2f}mm/s in UNSATISFACTORY zone"))
            elif metrics.vibration_velocity_rms >= thresholds.velocity_warning:
                alerts.append(("WARNING", f"Velocity {metrics.vibration_velocity_rms:.2f}mm/s exceeds warning threshold"))
            
            # Motor fault detection
            if metrics.dominant_frequency > 0 and reading.sensor_config:
                motor_1x = reading.sensor_config.rpm_nominal / 60.0
                motor_2x = motor_1x * 2
                
                if abs(metrics.dominant_frequency - motor_1x) < 2.0 and metrics.rms_acceleration > thresholds.unbalance_warning:
                    alerts.append(("WARNING", f"Possible unbalance at {metrics.dominant_frequency:.1f}Hz"))
                
                if abs(metrics.dominant_frequency - motor_2x) < 2.0 and metrics.rms_acceleration > thresholds.misalignment_warning:
                    alerts.append(("WARNING", f"Possible misalignment at {metrics.dominant_frequency:.1f}Hz"))
            
            if metrics.crest_factor > 4.0:
                alerts.append(("WARNING", f"High crest factor {metrics.crest_factor:.2f} - possible bearing issue"))
            elif metrics.crest_factor > 6.0:
                alerts.append(("CRITICAL", f"Very high crest factor {metrics.crest_factor:.2f} - bearing failure likely"))
        
        # Temperature monitoring
        if reading.temperature >= thresholds.temp_critical:
            alerts.append(("CRITICAL", f"Temperature {reading.temperature:.1f}°F exceeds critical threshold"))
        elif reading.temperature >= thresholds.temp_warning:
            alerts.append(("WARNING", f"Temperature {reading.temperature:.1f}°F exceeds warning threshold"))
        
        # Determine overall alert level
        if any(level == "EMERGENCY" for level, _ in alerts):
            alert_level = "EMERGENCY"
        elif any(level == "CRITICAL" for level, _ in alerts):
            alert_level = "CRITICAL"
        elif any(level == "WARNING" for level, _ in alerts):
            alert_level = "WARNING"
        else:
            alert_level = "NORMAL"
        
        # Log alerts
        for level, message in alerts:
            sensor_name = reading.sensor_config.name if reading.sensor_config else f"Sensor_{reading.sensor_id:02X}"
            alert_key = f"{sensor_name}_{level}"
            if alert_key not in self.active_alerts:
                self.active_alerts[alert_key] = {
                    'timestamp': reading.timestamp,
                    'sensor_id': reading.sensor_id,
                    'sensor_name': sensor_name,
                    'level': level,
                    'message': message
                }
                self.alert_history.append(self.active_alerts[alert_key].copy())
                print(f"ALERT [{level}] {sensor_name}: {message}")
        
        return alert_level

class WT901CMultiSensor:
    """Multi-sensor WT901C-485 communication manager"""
    
    def __init__(self, port='/dev/ttyUSB0', baud_rate=9600):
        self.port = port
        self.baud_rate = baud_rate
        self.direction_pin = 21
        self.serial_conn = None
        
        if ON_PI:
            self._init_gpio()
    
    def _init_gpio(self):
        """Initialize GPIO for RS485 direction control"""
        try:
            GPIO.setwarnings(False)
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.direction_pin, GPIO.OUT)
            GPIO.output(self.direction_pin, GPIO.HIGH)
        except Exception as e:
            print(f"GPIO error: {e}")
    
    def _calculate_crc16(self, data: bytes) -> int:
        """Calculate CRC16 for Modbus RTU"""
        crc = 0xFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x0001:
                    crc = (crc >> 1) ^ 0xA001
                else:
                    crc >>= 1
        return crc
    
    def _send_command(self, data: bytes):
        """Send data with RS485 timing control"""
        if ON_PI:
            delay_us = ((1000000 // (self.baud_rate // 10)) * len(data)) + 300
            GPIO.output(self.direction_pin, GPIO.HIGH)
            self.serial_conn.write(data)
            self.serial_conn.flush()
            time.sleep(delay_us / 1000000.0)
            GPIO.output(self.direction_pin, GPIO.LOW)
        else:
            self.serial_conn.write(data)
            self.serial_conn.flush()
    
    def connect(self) -> bool:
        """Connect to serial port"""
        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baud_rate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=0.5,
                write_timeout=1.0
            )
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False
    
    def scan_sensors(self, address_list=None) -> List[int]:
        """Scan for active sensors"""
        if not address_list:
            # Comprehensive scan
            address_list = list(range(0x50, 0x70)) + list(range(0x01, 0x20))
        
        print(f"Scanning {len(address_list)} addresses...")
        active_sensors = []
        
        for addr in address_list:
            if self._test_sensor(addr):
                active_sensors.append(addr)
                print(f"Found sensor at address 0x{addr:02X}")
        
        return active_sensors
    
    def _test_sensor(self, address):
        """Test if sensor exists at address"""
        try:
            cmd = bytearray([address, 0x03, 0x00, 0x34, 0x00, 0x03])
            crc = self._calculate_crc16(cmd)
            cmd.append(crc & 0xFF)
            cmd.append((crc >> 8) & 0xFF)
            
            self.serial_conn.reset_input_buffer()
            self._send_command(bytes(cmd))
            time.sleep(0.1)
            
            response = self.serial_conn.read(50)
            return len(response) >= 11 and response[0] == address and response[1] == 0x03
        except:
            return False
    
    def read_sensor_data(self, sensor_address: int) -> Optional[SensorReading]:
        """Read data from specific sensor"""
        cmd = bytearray([sensor_address, 0x03, 0x00, 0x34, 0x00, 0x0C])
        crc = self._calculate_crc16(cmd)
        cmd.append(crc & 0xFF)
        cmd.append((crc >> 8) & 0xFF)
        
        try:
            self.serial_conn.reset_input_buffer()
            self._send_command(bytes(cmd))
            time.sleep(0.1)
            
            response = self.serial_conn.read(100)
            if len(response) >= 29 and response[0] == sensor_address and response[1] == 0x03:
                data_bytes = response[3:27]
                
                registers = []
                for i in range(0, len(data_bytes), 2):
                    reg_value = (data_bytes[i] << 8) | data_bytes[i+1]
                    if reg_value > 32767:
                        reg_value -= 65536
                    registers.append(reg_value)
                
                # Read temperature
                temp_cmd = bytearray([sensor_address, 0x03, 0x00, 0x40, 0x00, 0x01])
                crc = self._calculate_crc16(temp_cmd)
                temp_cmd.append(crc & 0xFF)
                temp_cmd.append((crc >> 8) & 0xFF)
                
                self.serial_conn.reset_input_buffer()
                self._send_command(bytes(temp_cmd))
                time.sleep(0.05)
                
                temp_response = self.serial_conn.read(10)
                temperature_f = 77.0
                if len(temp_response) >= 7 and temp_response[0] == sensor_address:
                    temp_raw = (temp_response[3] << 8) | temp_response[4]
                    temp_celsius = temp_raw / 100.0
                    temperature_f = (temp_celsius * 9.0 / 5.0) + 32.0
                
                if len(registers) >= 12:
                    return SensorReading(
                        timestamp=datetime.now(),
                        sensor_id=sensor_address,
                        acceleration_x=registers[0] / 32768.0 * 16.0,
                        acceleration_y=registers[1] / 32768.0 * 16.0,
                        acceleration_z=registers[2] / 32768.0 * 16.0,
                        angular_velocity_x=registers[3] / 32768.0 * 2000.0,
                        angular_velocity_y=registers[4] / 32768.0 * 2000.0,
                        angular_velocity_z=registers[5] / 32768.0 * 2000.0,
                        angle_x=registers[9] / 32768.0 * 180.0,
                        angle_y=registers[10] / 32768.0 * 180.0,
                        angle_z=registers[11] / 32768.0 * 180.0,
                        temperature=temperature_f
                    )
        except:
            pass
        
        return None
    
    def close(self):
        """Clean up resources"""
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
        if ON_PI:
            try:
                GPIO.cleanup()
            except:
                pass

class UniversalVibrationMonitor:
    """Universal multi-sensor vibration monitoring system with web API"""
    
    def __init__(self, port='/dev/ttyUSB0', config_file='sensor_config.json'):
        self.port = port
        self.config_file = config_file
        self.sensor_manager = WT901CMultiSensor(port)
        self.sensor_configs = {}  # address -> SensorConfig
        self.analyzers = {}
        self.alert_manager = None
        self.running = False
        self.csv_file = None
        self.csv_writer = None
        self.latest_readings = {}  # Store latest readings for API
        self.system_status = {
            'running': False,
            'connected': False,
            'active_sensors': [],
            'total_readings': 0,
            'start_time': None
        }
        
        # Load configuration
        self.load_config()
        
    def load_config(self):
        """Load sensor and alert configuration"""
        default_config = {
            'sensors': {},
            'alert_thresholds': {
                'rms_accel_warning': 0.05,
                'rms_accel_critical': 0.15,
                'rms_accel_emergency': 0.30,
                'peak_accel_warning': 0.20,
                'peak_accel_critical': 0.50,
                'peak_accel_emergency': 1.00,
                'velocity_warning': 1.8,
                'velocity_critical': 4.5,
                'velocity_emergency': 11.0,
                'temp_warning': 158.0,
                'temp_critical': 194.0,
                'motor_frequency': 60.0,
                'bearing_defect_warning': 0.02,
                'unbalance_warning': 0.03,
                'misalignment_warning': 0.025
            },
            'analysis_settings': {
                'sample_rate': 2.0,
                'window_size': 128,
                'update_interval': 0.5
            }
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
            except:
                config = default_config
        else:
            config = default_config
        
        # Load sensor configurations
        self.sensor_configs.clear()
        for addr_str, sensor_data in config.get('sensors', {}).items():
            addr = int(addr_str, 16) if addr_str.startswith('0x') else int(addr_str)
            self.sensor_configs[addr] = SensorConfig(
                address=addr,
                name=sensor_data.get('name', f'Sensor_{addr:02X}'),
                type=sensor_data.get('type', 'MOTOR_GENERAL'),
                location=sensor_data.get('location', 'Unknown'),
                power_hp=sensor_data.get('power_hp', 20),
                power_kw=sensor_data.get('power_kw', sensor_data.get('power_hp', 20) * 0.746),
                rpm_nominal=sensor_data.get('rpm_nominal', 1800),
                enabled=sensor_data.get('enabled', True),
                custom_thresholds=sensor_data.get('custom_thresholds', {})
            )
        
        # Initialize alert manager
        thresholds = AlertThresholds(**config['alert_thresholds'])
        self.alert_manager = AlertManager(thresholds)
        
        # Analysis settings
        self.sample_rate = config['analysis_settings']['sample_rate']
        self.window_size = config['analysis_settings']['window_size']
        self.update_interval = config['analysis_settings']['update_interval']
    
    def save_config(self):
        """Save current configuration"""
        config = {
            'sensors': {},
            'alert_thresholds': {
                'rms_accel_warning': self.alert_manager.default_thresholds.rms_accel_warning,
                'rms_accel_critical': self.alert_manager.default_thresholds.rms_accel_critical,
                'rms_accel_emergency': self.alert_manager.default_thresholds.rms_accel_emergency,
                'peak_accel_warning': self.alert_manager.default_thresholds.peak_accel_warning,
                'peak_accel_critical': self.alert_manager.default_thresholds.peak_accel_critical,
                'peak_accel_emergency': self.alert_manager.default_thresholds.peak_accel_emergency,
                'velocity_warning': self.alert_manager.default_thresholds.velocity_warning,
                'velocity_critical': self.alert_manager.default_thresholds.velocity_critical,
                'velocity_emergency': self.alert_manager.default_thresholds.velocity_emergency,
                'temp_warning': self.alert_manager.default_thresholds.temp_warning,
                'temp_critical': self.alert_manager.default_thresholds.temp_critical
            },
            'analysis_settings': {
                'sample_rate': self.sample_rate,
                'window_size': self.window_size,
                'update_interval': self.update_interval
            }
        }
        
        # Save sensor configurations
        for addr, sensor_config in self.sensor_configs.items():
            config['sensors'][f'0x{addr:02X}'] = {
                'name': sensor_config.name,
                'type': sensor_config.type,
                'location': sensor_config.location,
                'power_hp': sensor_config.power_hp,
                'power_kw': sensor_config.power_kw,
                'rpm_nominal': sensor_config.rpm_nominal,
                'enabled': sensor_config.enabled,
                'custom_thresholds': sensor_config.custom_thresholds
            }
        
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    def update_sensor_config(self, address: int, config_data: dict):
        """Update or add sensor configuration"""
        if address not in self.sensor_configs:
            self.sensor_configs[address] = SensorConfig(
                address=address,
                name=config_data.get('name', f'Sensor_{address:02X}'),
                type='MOTOR_GENERAL',
                location='Unknown',
                power_hp=20,
                power_kw=14.92,
                rpm_nominal=1800
            )
        
        # Update existing config
        sensor_config = self.sensor_configs[address]
        for key, value in config_data.items():
            if hasattr(sensor_config, key):
                setattr(sensor_config, key, value)
        
        # Add analyzer if needed
        if address not in self.analyzers and sensor_config.enabled:
            self.analyzers[address] = VibrationAnalyzer(self.sample_rate, self.window_size)
        
        self.save_config()
    
    def initialize(self) -> bool:
        """Initialize monitoring system"""
        print("Universal Vibration Monitor Initializing...")
        
        if not self.sensor_manager.connect():
            print("ERROR: Failed to connect to serial port")
            return False
        
        self.system_status['connected'] = True
        
        # If we have configured sensors, scan for them
        if self.sensor_configs:
            print(f"Scanning for {len(self.sensor_configs)} configured sensors...")
            addresses_to_scan = list(self.sensor_configs.keys())
            active_sensors = self.sensor_manager.scan_sensors(addresses_to_scan)
        else:
            # No configuration, do comprehensive scan
            print("No sensor configuration found. Performing comprehensive scan...")
            active_sensors = self.sensor_manager.scan_sensors()
        
        if not active_sensors:
            print("ERROR: No sensors found")
            return False
        
        print(f"Found {len(active_sensors)} active sensor(s)")
        
        # Initialize analyzers for active sensors
        for sensor_id in active_sensors:
            if sensor_id not in self.sensor_configs:
                # Create default config for unconfigured sensor
                self.sensor_configs[sensor_id] = SensorConfig(
                    address=sensor_id,
                    name=f'Sensor_{sensor_id:02X}',
                    type='MOTOR_GENERAL',
                    location='Unknown',
                    power_hp=20,
                    power_kw=14.92,
                    rpm_nominal=1800
                )
            
            self.analyzers[sensor_id] = VibrationAnalyzer(self.sample_rate, self.window_size)
            sensor_name = self.sensor_configs[sensor_id].name
            print(f"   {sensor_name} (0x{sensor_id:02X}): Analyzer initialized")
        
        self.system_status['active_sensors'] = [f'0x{addr:02X}' for addr in active_sensors]
        self.save_config()
        
        return True
    
    def start_csv_logging(self, filename=None):
        """Start CSV data logging"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"vibration_data_{timestamp}.csv"
        
        self.csv_file = open(filename, 'w', newline='')
        self.csv_writer = csv.writer(self.csv_file)
        
        header = [
            'timestamp', 'sensor_address', 'sensor_name', 'sensor_type', 'location',
            'alert_level', 'iso_zone', 'accel_x_g', 'accel_y_g', 'accel_z_g',
            'gyro_x_dps', 'gyro_y_dps', 'gyro_z_dps',
            'angle_x_deg', 'angle_y_deg', 'angle_z_deg',
            'temperature_f', 'rms_accel_g', 'peak_accel_g',
            'crest_factor', 'vib_velocity_rms_mms', 'vib_displacement_rms_um',
            'dominant_freq_hz'
        ]
        self.csv_writer.writerow(header)
        print(f"CSV logging: {filename}")
    
    def run_monitoring(self):
        """Main monitoring loop"""
        if not self.initialize():
            return
        
        self.start_csv_logging()
        self.running = True
        self.system_status['running'] = True
        self.system_status['start_time'] = datetime.now().isoformat()
        
        print("\nUniversal Vibration Monitoring ACTIVE")
        print("Real-time Analysis | Web API Enabled | Dynamic Configuration")
        print("=" * 90)
        
        try:
            while self.running:
                for sensor_id in list(self.analyzers.keys()):
                    if sensor_id not in self.sensor_configs or not self.sensor_configs[sensor_id].enabled:
                        continue
                    
                    reading = self.sensor_manager.read_sensor_data(sensor_id)
                    
                    if reading:
                        # Attach sensor configuration
                        reading.sensor_config = self.sensor_configs[sensor_id]
                        
                        # Calculate acceleration magnitude
                        total_accel_magnitude = np.sqrt(
                            reading.acceleration_x**2 + 
                            reading.acceleration_y**2 + 
                            reading.acceleration_z**2
                        )
                        
                        # Add to analyzer
                        analyzer = self.analyzers[sensor_id]
                        analyzer.add_sample(total_accel_magnitude)
                        metrics = analyzer.calculate_metrics()
                        reading.vibration_metrics = metrics
                        
                        # Evaluate alerts
                        reading.alert_level = self.alert_manager.evaluate_reading(reading)
                        
                        # Store latest reading for API
                        self.latest_readings[sensor_id] = reading
                        self.system_status['total_readings'] += 1
                        
                        # Display reading
                        self.display_reading(reading)
                        
                        # Log to CSV
                        self.log_reading(reading)
                
                time.sleep(self.update_interval)
                
        except KeyboardInterrupt:
            print("\nMonitoring stopped by user")
        
        self.running = False
        self.system_status['running'] = False
        self.cleanup()
    
    def display_reading(self, reading: SensorReading):
        """Display sensor reading with analysis"""
        alert_symbol = {
            'NORMAL': '[OK]',
            'WARNING': '[WARN]', 
            'CRITICAL': '[CRIT]',
            'EMERGENCY': '[EMRG]'
        }.get(reading.alert_level, '[????]')
        
        timestamp_str = reading.timestamp.strftime('%H:%M:%S.%f')[:-3]
        sensor_name = reading.sensor_config.name if reading.sensor_config else f"0x{reading.sensor_id:02X}"
        
        base_info = (f"{alert_symbol} {timestamp_str} | {sensor_name} | "
                    f"Accel: [{reading.acceleration_x:+6.3f}, {reading.acceleration_y:+6.3f}, {reading.acceleration_z:+6.3f}]g | "
                    f"Temp: {reading.temperature:5.1f}°F")
        
        if reading.vibration_metrics:
            m = reading.vibration_metrics
            analysis_info = (f" | RMS: {m.rms_acceleration:.4f}g | "
                           f"Vel: {m.vibration_velocity_rms:.2f}mm/s | "
                           f"Zone: {m.iso_zone}")
            if m.dominant_frequency > 5.0:
                analysis_info += f" | Freq: {m.dominant_frequency:.1f}Hz"
        else:
            analysis_info = " | [Analyzing...]"
        
        print(base_info + analysis_info)
    
    def log_reading(self, reading: SensorReading):
        """Log reading to CSV"""
        if not self.csv_writer:
            return
        
        config = reading.sensor_config
        m = reading.vibration_metrics
        
        row = [
            reading.timestamp.isoformat(),
            f"0x{reading.sensor_id:02X}",
            config.name if config else "",
            config.type if config else "",
            config.location if config else "",
            reading.alert_level,
            m.iso_zone if m else "",
            f"{reading.acceleration_x:.4f}",
            f"{reading.acceleration_y:.4f}",
            f"{reading.acceleration_z:.4f}",
            f"{reading.angular_velocity_x:.2f}",
            f"{reading.angular_velocity_y:.2f}",
            f"{reading.angular_velocity_z:.2f}",
            f"{reading.angle_x:.2f}",
            f"{reading.angle_y:.2f}",
            f"{reading.angle_z:.2f}",
            f"{reading.temperature:.1f}",
            f"{m.rms_acceleration:.6f}" if m else "0",
            f"{m.peak_acceleration:.6f}" if m else "0",
            f"{m.crest_factor:.3f}" if m else "0",
            f"{m.vibration_velocity_rms:.4f}" if m else "0",
            f"{m.vibration_displacement_rms:.2f}" if m else "0",
            f"{m.dominant_frequency:.2f}" if m else "0"
        ]
        
        self.csv_writer.writerow(row)
        self.csv_file.flush()
    
    def cleanup(self):
        """Clean up resources"""
        self.sensor_manager.close()
        if self.csv_file:
            self.csv_file.close()
        self.save_config()
        print("Cleanup complete")

# Flask Web API Routes
@app.route('/api/status')
def get_status():
    """Get system status"""
    if monitor_instance:
        return jsonify(monitor_instance.system_status)
    return jsonify({'error': 'Monitor not initialized'}), 503

@app.route('/api/sensors')
def get_sensors():
    """Get all sensor configurations"""
    if monitor_instance:
        sensors = {}
        for addr, config in monitor_instance.sensor_configs.items():
            sensors[f'0x{addr:02X}'] = {
                'name': config.name,
                'type': config.type,
                'location': config.location,
                'power_hp': config.power_hp,
                'power_kw': config.power_kw,
                'rpm_nominal': config.rpm_nominal,
                'enabled': config.enabled
            }
        return jsonify(sensors)
    return jsonify({'error': 'Monitor not initialized'}), 503

@app.route('/api/sensors/<sensor_id>', methods=['GET', 'PUT'])
def sensor_detail(sensor_id):
    """Get or update specific sensor configuration"""
    if not monitor_instance:
        return jsonify({'error': 'Monitor not initialized'}), 503
    
    # Parse sensor address
    try:
        addr = int(sensor_id, 16)
    except:
        return jsonify({'error': 'Invalid sensor ID'}), 400
    
    if request.method == 'GET':
        if addr in monitor_instance.sensor_configs:
            config = monitor_instance.sensor_configs[addr]
            return jsonify({
                'address': f'0x{addr:02X}',
                'name': config.name,
                'type': config.type,
                'location': config.location,
                'power_hp': config.power_hp,
                'power_kw': config.power_kw,
                'rpm_nominal': config.rpm_nominal,
                'enabled': config.enabled,
                'custom_thresholds': config.custom_thresholds
            })
        return jsonify({'error': 'Sensor not found'}), 404
    
    elif request.method == 'PUT':
        data = request.json
        monitor_instance.update_sensor_config(addr, data)
        return jsonify({'success': True})

@app.route('/api/readings')
def get_readings():
    """Get latest readings from all sensors"""
    if monitor_instance:
        readings = {}
        for addr, reading in monitor_instance.latest_readings.items():
            if reading.vibration_metrics:
                readings[f'0x{addr:02X}'] = {
                    'timestamp': reading.timestamp.isoformat(),
                    'name': reading.sensor_config.name if reading.sensor_config else f'Sensor_{addr:02X}',
                    'temperature_f': reading.temperature,
                    'acceleration': {
                        'x': reading.acceleration_x,
                        'y': reading.acceleration_y,
                        'z': reading.acceleration_z
                    },
                    'metrics': {
                        'rms_acceleration': reading.vibration_metrics.rms_acceleration,
                        'velocity_mms': reading.vibration_metrics.vibration_velocity_rms,
                        'iso_zone': reading.vibration_metrics.iso_zone,
                        'dominant_frequency': reading.vibration_metrics.dominant_frequency
                    },
                    'alert_level': reading.alert_level
                }
        return jsonify(readings)
    return jsonify({'error': 'Monitor not initialized'}), 503

@app.route('/api/alerts')
def get_alerts():
    """Get active alerts"""
    if monitor_instance and monitor_instance.alert_manager:
        return jsonify(monitor_instance.alert_manager.active_alerts)
    return jsonify({'error': 'Monitor not initialized'}), 503

@app.route('/api/thresholds', methods=['GET', 'PUT'])
def thresholds():
    """Get or update alert thresholds"""
    if not monitor_instance:
        return jsonify({'error': 'Monitor not initialized'}), 503
    
    if request.method == 'GET':
        thresholds = monitor_instance.alert_manager.default_thresholds
        return jsonify({
            'rms_accel_warning': thresholds.rms_accel_warning,
            'rms_accel_critical': thresholds.rms_accel_critical,
            'rms_accel_emergency': thresholds.rms_accel_emergency,
            'velocity_warning': thresholds.velocity_warning,
            'velocity_critical': thresholds.velocity_critical,
            'velocity_emergency': thresholds.velocity_emergency,
            'temp_warning': thresholds.temp_warning,
            'temp_critical': thresholds.temp_critical
        })
    
    elif request.method == 'PUT':
        data = request.json
        thresholds = monitor_instance.alert_manager.default_thresholds
        for key, value in data.items():
            if hasattr(thresholds, key):
                setattr(thresholds, key, value)
        monitor_instance.save_config()
        return jsonify({'success': True})

@app.route('/api/control/start', methods=['POST'])
def start_monitoring():
    """Start monitoring"""
    global monitor_instance
    if monitor_instance and not monitor_instance.running:
        thread = threading.Thread(target=monitor_instance.run_monitoring)
        thread.start()
        return jsonify({'success': True, 'message': 'Monitoring started'})
    return jsonify({'error': 'Already running or not initialized'}), 400

@app.route('/api/control/stop', methods=['POST'])
def stop_monitoring():
    """Stop monitoring"""
    if monitor_instance and monitor_instance.running:
        monitor_instance.running = False
        return jsonify({'success': True, 'message': 'Monitoring stopped'})
    return jsonify({'error': 'Not running'}), 400

# Serve web interface (if you create one)
@app.route('/')
def serve_web_interface():
    """Serve the web interface"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>AutomataNexus Vibration Monitor</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            h1 { color: #00A8A8; }
        </style>
    </head>
    <body>
        <h1>AutomataNexus Universal Vibration Monitor</h1>
        <p>API Endpoints:</p>
        <ul>
            <li>GET /api/status - System status</li>
            <li>GET /api/sensors - All sensor configurations</li>
            <li>GET/PUT /api/sensors/{id} - Specific sensor config</li>
            <li>GET /api/readings - Latest sensor readings</li>
            <li>GET /api/alerts - Active alerts</li>
            <li>GET/PUT /api/thresholds - Alert thresholds</li>
            <li>POST /api/control/start - Start monitoring</li>
            <li>POST /api/control/stop - Stop monitoring</li>
        </ul>
    </body>
    </html>
    """

def main():
    global monitor_instance
    
    print("╔════════════════════════════════════════════════════════════════════════════════════╗")
    print("║                        Neural BMS Universal Vibration Monitor                      ║")
    print("║                     Enterprise WitMotion WTVB01-485 Integration                    ║")
    print("║                          (c) 2025 AutomataNexus AI & AutomataControls              ║")
    print("╚════════════════════════════════════════════════════════════════════════════════════╝")
    print("")
    print("UNIVERSAL VIBRATION MONITORING SYSTEM")
    print("Dynamic Configuration | Web API | Real-time Analysis")
    print("=" * 90)
    
    # Create monitor instance
    monitor_instance = UniversalVibrationMonitor("/dev/ttyUSB0", "sensor_config.json")
    
    # Start web API in separate thread
    api_thread = threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000, debug=False))
    api_thread.daemon = True
    api_thread.start()
    
    print("Web API started on http://localhost:5000")
    print("")
    
    # Start monitoring
    monitor_instance.run_monitoring()

if __name__ == "__main__":
    main()