#!/usr/bin/env python3
"""
Test each USB port individually to diagnose connection issues
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

def test_port(port):
    """Test a single port"""
    print(f"\nTesting {port}...")
    print("-" * 40)
    
    if not os.path.exists(port):
        print(f"✗ Port {port} does not exist")
        return
    
    try:
        ser = serial.Serial(port, 9600, timeout=0.5)
        time.sleep(0.5)
        print(f"✓ Opened {port}")
        
        # Try to read from sensor at 0x50
        address = 0x50
        cmd = bytearray([address, 0x03, 0x00, 0x34, 0x00, 0x0C])
        crc = calculate_crc16(cmd)
        cmd.append(crc & 0xFF)
        cmd.append((crc >> 8) & 0xFF)
        
        print(f"Sending command to address 0x{address:02X}...")
        ser.reset_input_buffer()
        ser.write(bytes(cmd))
        time.sleep(0.2)
        
        response = ser.read(100)
        if response:
            print(f"✓ Response received ({len(response)} bytes)")
            if len(response) >= 29 and response[0] == address:
                print("✓ Valid sensor response!")
                # Show first few values
                print(f"  First bytes: {' '.join([f'{b:02X}' for b in response[:10]])}")
            else:
                print("✗ Invalid response format")
                print(f"  Response: {' '.join([f'{b:02X}' for b in response[:20]])}")
        else:
            print("✗ No response from sensor")
        
        ser.close()
        
    except Exception as e:
        print(f"✗ Error: {e}")

def main():
    print("Individual Port Tester")
    print("=" * 50)
    
    ports = ['/dev/ttyUSB1', '/dev/ttyUSB2', '/dev/ttyUSB3']
    
    for port in ports:
        test_port(port)
    
    print("\n" + "=" * 50)
    print("Test complete!")
    print("\nIf a port shows 'No response', check:")
    print("- Is the sensor powered?")
    print("- Are A+/B- connected correctly?")
    print("- Is the sensor at address 0x50?")

if __name__ == "__main__":
    main()