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
    
    def write_register(self, sensor_address: int, register: int, value: int):
        """Write a value to a Modbus register"""
        cmd = bytearray([sensor_address, 0x06, (register >> 8) & 0xFF, register & 0xFF, 
                        (value >> 8) & 0xFF, value & 0xFF])
        crc = self._calculate_crc16(cmd)
        cmd.append(crc & 0xFF)
        cmd.append((crc >> 8) & 0xFF)
        
        try:
            self.serial_conn.reset_input_buffer()
            self._send_command(bytes(cmd))
            time.sleep(0.1)
            
            response = self.serial_conn.read(8)
            if len(response) >= 8 and response[0] == sensor_address and response[1] == 0x06:
                return True
            return False
        except Exception as e:
            print(f"Write register error: {e}")
            return False
    
    def read_single_sensor(self, sensor_address: int) -> Optional[SensorReading]:
        """Read data from a single sensor (alias for read_sensor_data)"""
        return self.read_sensor_data(sensor_address)
    
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
        # Don't call cleanup here - it closes the serial port
        # We want to keep the app running for web interface
        print("Monitoring paused - web interface still active")
    
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
    
    def test_sensor_connection(self, address: int) -> bool:
        """Test if a sensor responds at the given address"""
        try:
            # Try to read status register
            reading = self.sensor_manager.read_single_sensor(address)
            return reading is not None
        except:
            return False
    
    def program_sensor_address(self, current_address: int, new_address: int) -> bool:
        """Program a new address for a sensor"""
        try:
            # Implementation for WTVB01-485 address programming
            # First unlock the register
            self.sensor_manager.write_register(current_address, 0x69, 0xB588)
            time.sleep(0.1)
            
            # Write new address to register 0x1A
            self.sensor_manager.write_register(current_address, 0x1A, new_address)
            time.sleep(0.5)
            
            # Save settings to flash
            self.sensor_manager.write_register(current_address, 0x00, 0x0000)
            time.sleep(0.5)
            
            # Verify the change
            return self.test_sensor_connection(new_address)
        except Exception as e:
            print(f"Error programming address: {e}")
            return False
    
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
    if monitor_instance and monitor_instance.latest_readings:
        readings = {}
        for addr, reading in monitor_instance.latest_readings.items():
            # Always include the reading, even without full metrics
            sensor_data = {
                'timestamp': reading.timestamp.isoformat(),
                'name': reading.sensor_config.name if reading.sensor_config else f'Sensor_{addr:02X}',
                'temperature_f': reading.temperature,
                'acceleration': {
                    'x': reading.acceleration_x,
                    'y': reading.acceleration_y,
                    'z': reading.acceleration_z
                },
                'alert_level': reading.alert_level,
                'metrics': {
                    'rms_acceleration': 0.0,
                    'velocity_mms': 0.0,
                    'iso_zone': 'A',
                    'dominant_frequency': 0.0
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

@app.route('/api/scan', methods=['GET'])
def scan_sensors():
    """Scan for sensors on the bus"""
    if not monitor_instance:
        return jsonify({'error': 'Monitor not initialized'}), 400
    
    found_sensors = []
    
    # First, add all configured sensors
    for sensor in monitor_instance.config.sensors:
        found_sensors.append({
            'address': sensor.address,
            'configured': True,
            'name': sensor.name,
            'active': sensor.address in monitor_instance.latest_readings
        })
    
    # If monitoring is running, we can't scan for new sensors
    # But we can show which addresses have recent readings
    if monitor_instance.running:
        # Add any sensors we're getting data from that aren't configured
        for addr in monitor_instance.latest_readings.keys():
            if addr not in [s.address for s in monitor_instance.config.sensors]:
                found_sensors.append({
                    'address': addr,
                    'configured': False,
                    'name': f'Sensor_{addr:02X}',
                    'active': True
                })
    else:
        # If not running, just show configured sensors
        # We can't scan because the serial port might be closed
        pass
    
    # Add a note if monitoring is stopped
    if not monitor_instance.running and len(found_sensors) == 0:
        return jsonify({
            'error': 'No sensors configured. Start monitoring with at least one sensor first.',
            'sensors': []
        })
    
    return jsonify(found_sensors)

@app.route('/api/program-address', methods=['POST'])
def program_sensor_address():
    """Program a new sensor address"""
    data = request.json
    current_addr = data.get('current_address')
    new_addr = data.get('new_address')
    
    if not all([current_addr, new_addr]):
        return jsonify({'error': 'Missing address parameters'}), 400
    
    if not monitor_instance:
        return jsonify({'error': 'Monitor not initialized'}), 400
    
    try:
        # Program the address
        success = monitor_instance.program_sensor_address(current_addr, new_addr)
        if success:
            return jsonify({'success': True, 'message': f'Address changed from 0x{current_addr:02X} to 0x{new_addr:02X}'})
        else:
            return jsonify({'error': 'Failed to program address'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Serve web interface (if you create one)
@app.route('/')
def serve_web_interface():
    """Serve the web interface"""
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
                <button onclick="openConfig()" class="px-6 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600 transition-colors">
                    ⚙️ Configure Sensors
                </button>
                <button onclick="scanSensors()" class="px-6 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600 transition-colors">
                    🔍 Scan for Sensors
                </button>
                <button onclick="startMonitoring()" class="px-6 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors">
                    ▶️ Start Monitor
                </button>
                <button onclick="stopMonitoring()" class="px-6 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors">
                    ⏹️ Stop Monitor
                </button>
            </div>
        </div>

        <!-- Configuration Modal -->
        <div id="configModal" class="fixed inset-0 bg-black bg-opacity-50 hidden z-50 flex items-center justify-center">
            <div class="glass-card p-8 max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto">
                <h2 class="text-2xl mb-6">Sensor Configuration</h2>
                
                <div class="mb-6">
                    <h3 class="text-lg mb-3">Detected Sensors</h3>
                    <p class="text-sm text-gray-600 mb-2">Currently monitoring address 0x50. If you have multiple sensors at 0x50, program them to unique addresses below.</p>
                    <div id="detectedSensors" class="space-y-2">
                        <p class="text-gray-600">Loading...</p>
                    </div>
                </div>

                <div class="border-t pt-6">
                    <h3 class="text-lg mb-3">Program Sensor Address</h3>
                    <div class="grid grid-cols-2 gap-4 mb-4">
                        <div>
                            <label class="block text-sm mb-1">Current Address (hex)</label>
                            <input type="text" id="currentAddr" placeholder="0x50" class="w-full px-3 py-2 border rounded-lg">
                        </div>
                        <div>
                            <label class="block text-sm mb-1">New Address (hex)</label>
                            <input type="text" id="newAddr" placeholder="0x51" class="w-full px-3 py-2 border rounded-lg">
                        </div>
                    </div>
                    <button onclick="programAddress()" class="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600">
                        Program Address
                    </button>
                </div>

                <div class="flex justify-end mt-6 gap-2">
                    <button onclick="closeConfig()" class="px-6 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600">
                        Close
                    </button>
                </div>
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
                <div style="height: 300px; position: relative;">
                    <canvas id="vibrationChart"></canvas>
                </div>
            </div>
            <div class="glass-card p-6">
                <h3 class="text-xl mb-4">Temperature Trend</h3>
                <div style="height: 300px; position: relative;">
                    <canvas id="temperatureChart"></canvas>
                </div>
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
                        x: {
                            ticks: {
                                maxRotation: 45,
                                minRotation: 45
                            }
                        },
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

        // Configuration functions
        function openConfig() {
            document.getElementById('configModal').classList.remove('hidden');
            // Show current sensor status
            showCurrentSensors();
        }
        
        function showCurrentSensors() {
            const sensorsDiv = document.getElementById('detectedSensors');
            sensorsDiv.innerHTML = `
                <div class="space-y-3">
                    <div class="p-3 bg-blue-50 border border-blue-200 rounded">
                        <p class="font-medium text-blue-800">Current Setup:</p>
                        <p class="text-sm text-blue-700">1 sensor detected at address 0x50 (default)</p>
                    </div>
                    <div class="p-3 bg-amber-50 border border-amber-200 rounded">
                        <p class="font-medium text-amber-800">Multiple Sensors at 0x50?</p>
                        <p class="text-sm text-amber-700">If you have 3 sensors, they're likely all at address 0x50.</p>
                        <p class="text-sm text-amber-700 mt-1">Program them one at a time:</p>
                        <ol class="text-sm text-amber-700 ml-4 mt-1 list-decimal">
                            <li>Disconnect 2 sensors, leave only 1 connected</li>
                            <li>Program it to 0x51 using the form below</li>
                            <li>Disconnect that sensor, connect the next one</li>
                            <li>Program it to 0x52</li>
                            <li>Connect all 3 sensors and restart monitoring</li>
                        </ol>
                    </div>
                </div>
            `;
        }

        function closeConfig() {
            document.getElementById('configModal').classList.add('hidden');
        }

        async function scanSensors() {
            const sensorsDiv = document.getElementById('detectedSensors');
            sensorsDiv.innerHTML = '<p class="text-gray-600">Scanning...</p>';
            
            try {
                const response = await fetch(`${API_BASE}/scan`);
                const data = await response.json();
                
                if (data.error) {
                    sensorsDiv.innerHTML = `<p class="text-amber-600">${data.error}</p>`;
                } else if (data.length === 0) {
                    sensorsDiv.innerHTML = '<p class="text-gray-600">No sensors found</p>';
                } else {
                    const sensors = data;
                    sensorsDiv.innerHTML = sensors.map(sensor => `
                        <div class="flex justify-between items-center p-3 bg-gray-100 rounded">
                            <div>
                                <span class="font-medium">${sensor.name || 'Unknown'}</span>
                                <span class="text-sm text-gray-600 ml-2">0x${sensor.address.toString(16).toUpperCase().padStart(2, '0')}</span>
                            </div>
                            <div class="flex items-center gap-2">
                                ${sensor.active ? '<span class="w-2 h-2 bg-green-500 rounded-full"></span>' : ''}
                                <span class="text-sm ${sensor.configured ? 'text-blue-600' : 'text-orange-600'}">
                                    ${sensor.configured ? 'Configured' : 'New Device'}
                                </span>
                            </div>
                        </div>
                    `).join('');
                }
            } catch (error) {
                sensorsDiv.innerHTML = '<p class="text-red-600">Scan failed</p>';
            }
        }

        async function programAddress() {
            const currentAddr = document.getElementById('currentAddr').value;
            const newAddr = document.getElementById('newAddr').value;
            
            if (!currentAddr || !newAddr) {
                alert('Please enter both current and new addresses');
                return;
            }
            
            try {
                const response = await fetch(`${API_BASE}/program-address`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        current_address: parseInt(currentAddr, 16),
                        new_address: parseInt(newAddr, 16)
                    })
                });
                
                const result = await response.json();
                if (result.success) {
                    alert('Address programmed successfully!');
                    scanSensors();
                } else {
                    alert('Failed to program address: ' + result.error);
                }
            } catch (error) {
                alert('Error programming address');
            }
        }

        // Monitoring control functions
        async function startMonitoring() {
            try {
                const response = await fetch(`${API_BASE}/control/start`, { method: 'POST' });
                const result = await response.json();
                if (result.success) {
                    alert('Monitoring started');
                    setTimeout(() => {
                        loadSystemStatus();
                        loadSensorData();
                    }, 1000);
                } else {
                    alert('Failed to start: ' + result.error);
                }
            } catch (error) {
                alert('Error starting monitoring');
            }
        }

        async function stopMonitoring() {
            try {
                const response = await fetch(`${API_BASE}/control/stop`, { method: 'POST' });
                const result = await response.json();
                if (result.success) {
                    alert('Monitoring stopped. You can now scan for new sensors.');
                    loadSystemStatus();
                } else {
                    alert('Failed to stop: ' + result.error);
                }
            } catch (error) {
                alert('Error stopping monitoring');
            }
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
    
    # Start monitoring in a separate thread
    monitor_thread = threading.Thread(target=monitor_instance.run_monitoring)
    monitor_thread.start()
    
    # Keep the main thread alive for the web interface
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        monitor_instance.running = False
        monitor_instance.cleanup()

if __name__ == "__main__":
    main()