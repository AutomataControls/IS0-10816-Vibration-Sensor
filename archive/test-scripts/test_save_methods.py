#!/usr/bin/env python3
"""
Test different save methods for WTVB01-485
Try both SAVE_PARAM and SAVE_SWRST methods
"""
import serial
import time
import os
import sys

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

def write_register(ser, address, register, value, description=""):
    """Write to a Modbus register"""
    cmd = bytearray([address, 0x06, (register >> 8) & 0xFF, register & 0xFF, 
                    (value >> 8) & 0xFF, value & 0xFF])
    crc = calculate_crc16(cmd)
    cmd.append(crc & 0xFF)
    cmd.append((crc >> 8) & 0xFF)
    
    print(f"{description}: Reg 0x{register:02X} = 0x{value:04X}")
    
    try:
        ser.reset_input_buffer()
        ser.write(bytes(cmd))
        time.sleep(0.1)
        
        response = ser.read(8)
        if len(response) > 0:
            print(f"Response: {' '.join([f'{b:02X}' for b in response])}")
            return len(response) == 8
        else:
            print("No response")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def read_register(ser, address, register):
    """Read a single register"""
    cmd = bytearray([address, 0x03, (register >> 8) & 0xFF, register & 0xFF, 
                    0x00, 0x01])
    crc = calculate_crc16(cmd)
    cmd.append(crc & 0xFF)
    cmd.append((crc >> 8) & 0xFF)
    
    try:
        ser.reset_input_buffer()
        ser.write(bytes(cmd))
        time.sleep(0.1)
        
        response = ser.read(7)
        if len(response) >= 7 and response[0] == address and response[1] == 0x03:
            return (response[3] << 8) | response[4]
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
    
    print("WTVB01-485 Save Method Test")
    print("=" * 60)
    
    try:
        ser = serial.Serial(port, 9600, timeout=0.5)
        time.sleep(0.5)
        
        current_addr = 0x50
        
        # Read current address
        print("\n1. Reading current address...")
        addr_val = read_register(ser, current_addr, 0x1A)
        if addr_val:
            print(f"Current address in register: 0x{addr_val:04X}")
        
        print("\n2. Testing save methods after writing address...")
        
        # Unlock
        print("\nUnlocking...")
        write_register(ser, current_addr, 0x69, 0xB588, "Unlock")
        time.sleep(0.1)
        
        # Write new address
        print("\nWriting new address...")
        write_register(ser, current_addr, 0x1A, 0x51, "Set address to 0x51")
        time.sleep(0.1)
        
        # Read back to verify write
        print("\nVerifying write...")
        addr_val = read_register(ser, current_addr, 0x1A)
        if addr_val:
            print(f"Address register now shows: 0x{addr_val:04X}")
            if addr_val == 0x51:
                print("✓ Write successful!")
            else:
                print("✗ Write failed!")
        
        # Try different save methods
        print("\n3. Testing save methods...")
        
        print("\nMethod 1: SAVE_PARAM (0x00 to 0x00)")
        write_register(ser, current_addr, 0x00, 0x0000, "Save parameters")
        time.sleep(2)
        
        print("\nMethod 2: Try writing 1 to save register")
        write_register(ser, current_addr, 0x00, 0x0001, "Save with value 1")
        time.sleep(2)
        
        print("\nMethod 3: SAVE_SWRST (0xFF to 0x00) - Software reset")
        write_register(ser, current_addr, 0x00, 0x00FF, "Software reset")
        time.sleep(3)
        
        print("\nMethod 4: Try alternate registers")
        write_register(ser, current_addr, 0x01, 0x0000, "Try register 0x01")
        time.sleep(1)
        
        write_register(ser, current_addr, 0x02, 0x0000, "Try register 0x02")
        time.sleep(1)
        
        print("\n" + "=" * 60)
        print("Test complete!")
        print("\nNOTE: After each save method, the sensor may reset.")
        print("Power cycle the sensor and check with scan_all_sensors.py")
        print("\nIf address still doesn't change, the sensor firmware")
        print("may not support address modification.")
        
        ser.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()