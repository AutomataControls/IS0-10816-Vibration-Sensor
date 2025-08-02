#!/usr/bin/env python3
"""
Quick scanner to find all sensors on the RS485 bus
"""
import serial
import time
import struct

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

def scan_sensor(port, address):
    """Try to read from a sensor at given address"""
    cmd = bytearray([address, 0x03, 0x00, 0x34, 0x00, 0x0C])
    crc = calculate_crc16(cmd)
    cmd.append(crc & 0xFF)
    cmd.append((crc >> 8) & 0xFF)
    
    try:
        port.reset_input_buffer()
        port.write(bytes(cmd))
        time.sleep(0.1)
        
        response = port.read(100)
        if len(response) >= 29 and response[0] == address and response[1] == 0x03:
            return True
        return False
    except:
        return False

def main():
    print("Scanning for WTVB01-485 sensors...")
    print("=" * 50)
    
    try:
        ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=0.5)
        time.sleep(0.5)
        
        found_sensors = []
        
        # Scan common address range
        for addr in range(0x01, 0xFF):
            if scan_sensor(ser, addr):
                found_sensors.append(addr)
                print(f"Found sensor at address 0x{addr:02X} (decimal {addr})")
        
        ser.close()
        
        print("=" * 50)
        if found_sensors:
            print(f"Total sensors found: {len(found_sensors)}")
            print("Addresses:", [f"0x{addr:02X}" for addr in found_sensors])
        else:
            print("No sensors found!")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()