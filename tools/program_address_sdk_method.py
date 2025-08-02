#!/usr/bin/env python3
"""
Program WTVB01-485 address using SDK method
Exact timing and sequence from official SDK
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

def send_command(ser, cmd):
    """Send command and return response"""
    try:
        ser.reset_input_buffer()
        ser.write(bytes(cmd))
        time.sleep(0.1)  # SDK uses 100ms delay
        response = ser.read(8)
        return response
    except:
        return None

def write_register_sdk_style(ser, address, register, value):
    """Write register using SDK method"""
    # Build command exactly like SDK
    tempBytes = [None] * 8
    tempBytes[0] = address      # Device modbus address
    tempBytes[1] = 0x06         # Write function code
    tempBytes[2] = register >> 8 # Register high byte
    tempBytes[3] = register & 0xff # Register low byte
    tempBytes[4] = value >> 8    # Value high byte
    tempBytes[5] = value & 0xff  # Value low byte
    
    # Calculate CRC
    tempCrc = calculate_crc16(tempBytes[:6])
    # SDK stores CRC low byte first, then high byte
    tempBytes[6] = tempCrc & 0xff     # CRC low byte
    tempBytes[7] = tempCrc >> 8       # CRC high byte
    
    print(f"Sending: {' '.join([f'{b:02X}' for b in tempBytes])}")
    response = send_command(ser, tempBytes)
    
    if response:
        print(f"Response: {' '.join([f'{b:02X}' for b in response])}")
        return len(response) == 8
    else:
        print("No response")
        return False

def main():
    # Auto-detect port
    if os.path.exists("/dev/ttyUSB0"):
        port = "/dev/ttyUSB0"
    elif os.path.exists("/dev/ttyUSB1"):
        port = "/dev/ttyUSB1"
    else:
        print("No USB serial port found!")
        return
    
    print("WTVB01-485 Address Programmer (SDK Method)")
    print(f"Port: {port}")
    print("=" * 50)
    
    current_addr = 0x50
    new_addr = 0x51
    
    try:
        # Open serial port with SDK settings
        ser = serial.Serial(port, 9600, timeout=0.5)
        time.sleep(0.5)
        
        print(f"\nChanging address from 0x{current_addr:02X} to 0x{new_addr:02X}")
        print("\nFollowing SDK writeReg() sequence:")
        
        # Step 1: Unlock (SDK line 261)
        print("\n1. Unlock (0x69 = 0xB588)")
        write_register_sdk_style(ser, current_addr, 0x69, 0xB588)
        
        # Step 2: Delay 100ms (SDK line 263)
        time.sleep(0.1)
        
        # Step 3: Write new address (SDK line 265)
        print("\n2. Write address (0x1A = 0x{:02X})".format(new_addr))
        write_register_sdk_style(ser, current_addr, 0x1A, new_addr)
        
        # Step 4: Delay 100ms (SDK line 267)
        time.sleep(0.1)
        
        # Step 5: Save (SDK line 269)
        print("\n3. Save (0x00 = 0x0000)")
        write_register_sdk_style(ser, current_addr, 0x00, 0x0000)
        
        print("\n" + "=" * 50)
        print("Programming complete!")
        print("\nIMPORTANT: Power cycle the sensor now!")
        print("After power cycle, run: python3 scan_all_sensors.py")
        
        ser.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()