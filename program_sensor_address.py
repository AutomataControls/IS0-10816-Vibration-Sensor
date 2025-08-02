#!/usr/bin/env python3
"""
WTVB01-485 Address Programming Tool
Tries multiple methods to program sensor address
"""
import serial
import time
import struct
import sys
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

def write_register(ser, address, register, value):
    """Write to a Modbus register"""
    cmd = bytearray([address, 0x06, (register >> 8) & 0xFF, register & 0xFF, 
                    (value >> 8) & 0xFF, value & 0xFF])
    crc = calculate_crc16(cmd)
    cmd.append(crc & 0xFF)
    cmd.append((crc >> 8) & 0xFF)
    
    print(f"  Writing: Addr=0x{address:02X}, Reg=0x{register:04X}, Val=0x{value:04X}")
    print(f"  Command: {' '.join([f'{b:02X}' for b in cmd])}")
    
    try:
        ser.reset_input_buffer()
        ser.write(bytes(cmd))
        time.sleep(0.1)
        
        response = ser.read(8)
        if len(response) > 0:
            print(f"  Response: {' '.join([f'{b:02X}' for b in response])}")
            if len(response) >= 8 and response[0] == address and response[1] == 0x06:
                print("  ✓ Success")
                return True
        else:
            print("  No response")
        return False
    except Exception as e:
        print(f"  Error: {e}")
        return False

def test_sensor(ser, address):
    """Test if sensor responds"""
    cmd = bytearray([address, 0x03, 0x00, 0x34, 0x00, 0x0C])
    crc = calculate_crc16(cmd)
    cmd.append(crc & 0xFF)
    cmd.append((crc >> 8) & 0xFF)
    
    try:
        ser.reset_input_buffer()
        ser.write(bytes(cmd))
        time.sleep(0.1)
        response = ser.read(100)
        return len(response) >= 29 and response[0] == address
    except:
        return False

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 program_sensor_address.py <current_hex> <new_hex>")
        print("Example: python3 program_sensor_address.py 0x50 0x51")
        return
    
    try:
        current = int(sys.argv[1], 16)
        new = int(sys.argv[2], 16)
    except:
        print("Invalid hex address")
        return
    
    # Auto-detect port
    if os.path.exists("/dev/ttyUSB0"):
        port = "/dev/ttyUSB0"
    elif os.path.exists("/dev/ttyUSB1"):
        port = "/dev/ttyUSB1"
    else:
        print("No USB serial port found!")
        return
    
    print(f"WTVB01-485 Address Programmer")
    print(f"Port: {port}")
    print(f"Current address: 0x{current:02X}")
    print(f"New address: 0x{new:02X}")
    print("=" * 50)
    
    try:
        ser = serial.Serial(port, 9600, timeout=0.5)
        time.sleep(0.5)
        
        # Test current address
        print("\n1. Testing current address...")
        if not test_sensor(ser, current):
            print(f"  ERROR: No sensor found at 0x{current:02X}")
            return
        print(f"  ✓ Sensor found at 0x{current:02X}")
        
        # Try multiple unlock codes
        print("\n2. Unlocking configuration...")
        unlocked = False
        
        # Method 1: Standard unlock
        if write_register(ser, current, 0x69, 0xB588):
            unlocked = True
        else:
            # Method 2: Alternative register
            print("  Trying alternate unlock register...")
            if write_register(ser, current, 0x8B, 0xB588):
                unlocked = True
        
        if not unlocked:
            print("  WARNING: Unlock may have failed")
        
        time.sleep(0.2)
        
        # Write new address
        print("\n3. Writing new address...")
        if not write_register(ser, current, 0x1A, new):
            print("  ERROR: Failed to write address")
            return
        
        time.sleep(0.2)
        
        # Try multiple save methods
        print("\n4. Saving to flash (trying multiple methods)...")
        
        # Method 1: Standard save
        print("  Method 1: Save command (0x00 = 0x0000)")
        write_register(ser, current, 0x00, 0x0000)
        time.sleep(0.5)
        
        # Method 2: Alternative save register
        print("  Method 2: Alternative save (0x1F = 0x0000)")
        write_register(ser, current, 0x1F, 0x0000)
        time.sleep(0.5)
        
        # Method 3: Reboot command
        print("  Method 3: Reboot command (0x00 = 0x00FF)")
        write_register(ser, current, 0x00, 0x00FF)
        time.sleep(0.5)
        
        print("\n5. Waiting for sensor to reset...")
        time.sleep(3)
        
        # Test new address
        print("\n6. Testing new address...")
        if test_sensor(ser, new):
            print(f"  ✓ SUCCESS! Sensor now responds at 0x{new:02X}")
            print("\n  Address change successful!")
        else:
            print(f"  ✗ Sensor not found at 0x{new:02X}")
            
            # Check if still at old address
            if test_sensor(ser, current):
                print(f"  Sensor still at old address 0x{current:02X}")
                print("\n  Address change failed - try power cycling the sensor")
            else:
                print("  Sensor not responding at either address")
                print("  Try power cycling and check both addresses")
        
        ser.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()