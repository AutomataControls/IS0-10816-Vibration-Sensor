#!/usr/bin/env python3
"""
Diagnose WTVB01-485 sensor configuration
Read all config registers to understand the sensor state
"""
import serial
import time
import os

def calculate_crc16(data):
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

def read_registers(ser, address, start_reg, count):
    """Read multiple registers"""
    cmd = bytearray([address, 0x03, (start_reg >> 8) & 0xFF, start_reg & 0xFF, 
                    (count >> 8) & 0xFF, count & 0xFF])
    crc = calculate_crc16(cmd)
    cmd.append(crc & 0xFF)
    cmd.append((crc >> 8) & 0xFF)
    
    try:
        ser.reset_input_buffer()
        ser.write(bytes(cmd))
        time.sleep(0.1)
        
        expected_len = 5 + count * 2
        response = ser.read(expected_len)
        
        if len(response) >= expected_len and response[0] == address and response[1] == 0x03:
            values = []
            for i in range(count):
                val = (response[3 + i*2] << 8) | response[4 + i*2]
                values.append(val)
            return values
        return None
    except:
        return None

def main():
    # Auto-detect port
    if os.path.exists("/dev/ttyUSB0"):
        port = "/dev/ttyUSB0"
    elif os.path.exists("/dev/ttyUSB1"):
        port = "/dev/ttyUSB1"
    else:
        print("No USB serial port found!")
        return
    
    print("WTVB01-485 Sensor Diagnostics")
    print(f"Port: {port}")
    print("=" * 60)
    
    try:
        ser = serial.Serial(port, 9600, timeout=0.5)
        time.sleep(0.5)
        
        address = 0x50
        
        # Important config registers
        config_regs = {
            0x00: "Save/Reset Register",
            0x01: "Calibration Switch",
            0x04: "Baud Rate",
            0x1A: "Device Address",
            0x1B: "LED Off (possible alt address?)",
            0x1F: "Unknown (possible save?)",
            0x69: "Unlock Register",
            0x63: "Cutoff Freq High",
            0x64: "Cutoff Freq Low",
            0x65: "Sample Frequency"
        }
        
        print(f"\nReading configuration registers from sensor at 0x{address:02X}:")
        print("-" * 60)
        
        for reg, desc in sorted(config_regs.items()):
            values = read_registers(ser, address, reg, 1)
            if values:
                print(f"Register 0x{reg:02X} ({desc:30s}): 0x{values[0]:04X} ({values[0]})")
            else:
                print(f"Register 0x{reg:02X} ({desc:30s}): No response")
            time.sleep(0.05)
        
        # Read a block of registers around the address register
        print("\n" + "-" * 60)
        print("Reading registers around address register (0x18-0x1C):")
        values = read_registers(ser, address, 0x18, 5)
        if values:
            for i, val in enumerate(values):
                reg = 0x18 + i
                print(f"Register 0x{reg:02X}: 0x{val:04X} ({val})")
        
        # Try reading current sensor data to verify communication
        print("\n" + "-" * 60)
        print("Sensor data (to verify communication):")
        data_values = read_registers(ser, address, 0x34, 6)  # Accel X,Y,Z, Gyro X,Y,Z
        if data_values:
            print("Communication OK - sensor is responding")
            print(f"Accel X: {data_values[0]}")
            print(f"Accel Y: {data_values[1]}")
            print(f"Accel Z: {data_values[2]}")
        else:
            print("No sensor data - communication problem")
        
        ser.close()
        
        print("\n" + "=" * 60)
        print("Diagnostics complete!")
        print("\nIf address register (0x1A) shows 0x0050, the sensor is at address 0x50")
        print("If it shows 0x0051, the address change worked but isn't loading")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()