#!/usr/bin/env python3
"""
################################################################################
# AutomataNexus Universal Sensor Configuration GUI
# Professional Multi-Sensor Setup Interface
################################################################################

(c) 2025 AutomataNexus AI & AutomataControls
Author: Andrew Jewell Sr. - Dev Ops Automata Controls / AutomataNexus AI
License: Commercial License Required
Contact: DevOps@automatacontrols.com

Universal configuration tool for any number of WTVB01-485 sensors (1-32)
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import serial
import serial.tools.list_ports
import threading
import time
import json
from datetime import datetime
try:
    import RPi.GPIO as GPIO
    ON_PI = True
except:
    ON_PI = False

class SensorConfigGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AutomataNexus Universal Sensor Configuration")
        self.root.geometry("1400x900")
        
        # AutomataNexus Professional Color Theme
        self.colors = {
            'primary': '#00A8A8',      # Teal/Turquoise
            'text': '#333333',         # Dark Gray
            'bg': '#FFFFFF',           # White
            'border': '#DDDDDD',       # Light Gray
            'light_border': '#EEEEEE', # Lighter Gray
            'table_header': '#F5F5F5', # Light Gray
            
            # Alert Colors
            'warning_bg': '#F8D7DA',   # Light Red
            'warning_border': '#DC3545', # Red
            'caution_bg': '#FFF3CD',   # Light Yellow
            'caution_border': '#FFC107', # Yellow/Gold
            'success_bg': '#D4EDDA',   # Light Green
            'success_border': '#28A745', # Green
            'info_bg': '#E3F2FD',      # Light Blue
            'info_border': '#2196F3',  # Blue
            
            # UI Elements
            'button_bg': '#00A8A8',
            'button_fg': '#FFFFFF',
            'entry_bg': '#FFFFFF',
            'console_bg': '#F5F5F5',
            'console_fg': '#333333'
        }
        
        # Configure root
        self.root.configure(bg=self.colors['bg'])
        
        # Style configuration
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Configure ttk styles with AutomataNexus theme
        self.style.configure('Title.TLabel', 
                           background=self.colors['bg'],
                           foreground=self.colors['primary'],
                           font=('Arial', 24, 'bold'))
        
        self.style.configure('Heading.TLabel',
                           background=self.colors['bg'],
                           foreground=self.colors['text'],
                           font=('Arial', 14, 'bold'))
        
        self.style.configure('Primary.TButton',
                           background=self.colors['primary'],
                           foreground=self.colors['button_fg'],
                           borderwidth=0,
                           focuscolor='none',
                           font=('Arial', 10, 'bold'))
        
        self.style.map('Primary.TButton',
                      background=[('active', '#008888')])
        
        # Serial connection
        self.serial_conn = None
        self.direction_pin = 21
        self.connected = False
        
        # Sensor data
        self.sensors = {}  # address: sensor_info
        self.max_sensors = 32
        
        # Initialize GPIO if on Pi
        if ON_PI:
            self._init_gpio()
        
        # Build GUI
        self._build_gui()
        
        # Start port scanner
        self._scan_ports()
        
    def _init_gpio(self):
        """Initialize GPIO for RS485"""
        try:
            GPIO.setwarnings(False)
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.direction_pin, GPIO.OUT)
            GPIO.output(self.direction_pin, GPIO.HIGH)
        except Exception as e:
            self.log(f"GPIO initialization warning: {e}", 'WARNING')
    
    def _build_gui(self):
        """Build the GUI interface"""
        # Main container with border
        main_container = tk.Frame(self.root, bg=self.colors['bg'], 
                                 highlightbackground=self.colors['border'],
                                 highlightthickness=1)
        main_container.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Title Frame with bottom border
        title_frame = tk.Frame(main_container, bg=self.colors['bg'])
        title_frame.pack(fill='x', padx=20, pady=(20, 0))
        
        # Company Logo
        logo_label = tk.Label(
            title_frame,
            text="AUTOMATANEXUS",
            font=('Arial', 20, 'bold'),
            bg=self.colors['bg'],
            fg=self.colors['primary']
        )
        logo_label.pack()
        
        title_label = tk.Label(
            title_frame,
            text="Universal Sensor Configuration System",
            font=('Arial', 16),
            bg=self.colors['bg'],
            fg=self.colors['text']
        )
        title_label.pack()
        
        # Title separator
        separator = tk.Frame(title_frame, height=2, bg=self.colors['primary'])
        separator.pack(fill='x', pady=(10, 0))
        
        # Connection Frame
        conn_container = tk.Frame(main_container, bg=self.colors['info_bg'],
                                 highlightbackground=self.colors['info_border'],
                                 highlightthickness=0)
        conn_container.pack(fill='x', padx=20, pady=20)
        
        # Blue border on left
        blue_border = tk.Frame(conn_container, bg=self.colors['info_border'], width=4)
        blue_border.pack(side='left', fill='y')
        
        conn_frame = tk.Frame(conn_container, bg=self.colors['info_bg'])
        conn_frame.pack(fill='both', expand=True, padx=15, pady=10)
        
        tk.Label(conn_frame, text="Connection Settings", 
                font=('Arial', 12, 'bold'),
                bg=self.colors['info_bg'], 
                fg=self.colors['text']).grid(row=0, column=0, columnspan=6, pady=(0, 10), sticky='w')
        
        # Port selection
        tk.Label(conn_frame, text="Serial Port:", 
                bg=self.colors['info_bg'], 
                fg=self.colors['text']).grid(row=1, column=0, padx=5, pady=5, sticky='e')
        
        self.port_var = tk.StringVar()
        self.port_combo = ttk.Combobox(conn_frame, textvariable=self.port_var, width=20)
        self.port_combo.grid(row=1, column=1, padx=5, pady=5)
        
        # Baud rate
        tk.Label(conn_frame, text="Baud Rate:", 
                bg=self.colors['info_bg'], 
                fg=self.colors['text']).grid(row=1, column=2, padx=5, pady=5, sticky='e')
        
        self.baud_var = tk.StringVar(value="9600")
        baud_combo = ttk.Combobox(conn_frame, textvariable=self.baud_var, width=10)
        baud_combo['values'] = ['2400', '4800', '9600', '19200', '38400', '57600', '115200']
        baud_combo.grid(row=1, column=3, padx=5, pady=5)
        
        # Connect button
        self.connect_btn = tk.Button(
            conn_frame,
            text="Connect",
            command=self._toggle_connection,
            bg=self.colors['primary'],
            fg=self.colors['button_fg'],
            font=('Arial', 10, 'bold'),
            width=15,
            relief='flat',
            cursor='hand2'
        )
        self.connect_btn.grid(row=1, column=4, padx=20, pady=5)
        
        # Status with colored background
        self.status_frame = tk.Frame(conn_frame, bg=self.colors['warning_bg'], 
                                    highlightbackground=self.colors['warning_border'],
                                    highlightthickness=1)
        self.status_frame.grid(row=1, column=5, padx=5, pady=5)
        
        self.status_label = tk.Label(
            self.status_frame,
            text="Disconnected",
            bg=self.colors['warning_bg'],
            fg=self.colors['warning_border'],
            font=('Arial', 10, 'bold'),
            padx=10,
            pady=5
        )
        self.status_label.pack()
        
        # Main content frame
        content_frame = tk.Frame(main_container, bg=self.colors['bg'])
        content_frame.pack(fill='both', expand=True, padx=20)
        
        # Left panel - Sensor Discovery
        left_frame = tk.Frame(content_frame, bg=self.colors['bg'],
                             highlightbackground=self.colors['border'],
                             highlightthickness=1)
        left_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        # Section header with teal underline
        header_frame = tk.Frame(left_frame, bg=self.colors['bg'])
        header_frame.pack(fill='x', padx=15, pady=(15, 5))
        
        tk.Label(header_frame, text="Sensor Discovery & Configuration", 
                font=('Arial', 14, 'bold'),
                bg=self.colors['bg'], 
                fg=self.colors['primary']).pack(anchor='w')
        
        tk.Frame(header_frame, height=1, bg=self.colors['primary']).pack(fill='x', pady=(5, 0))
        
        # Number of sensors
        num_frame = tk.Frame(left_frame, bg=self.colors['bg'])
        num_frame.pack(fill='x', padx=15, pady=10)
        
        tk.Label(num_frame, text="Expected Sensors:", 
                bg=self.colors['bg'], 
                fg=self.colors['text']).pack(side='left', padx=5)
        
        self.num_sensors_var = tk.IntVar(value=3)
        num_spin = tk.Spinbox(
            num_frame,
            from_=1,
            to=32,
            textvariable=self.num_sensors_var,
            width=5,
            font=('Arial', 10),
            relief='solid',
            borderwidth=1
        )
        num_spin.pack(side='left', padx=5)
        
        tk.Label(num_frame, text="(1-32 sensors)", 
                bg=self.colors['bg'], 
                fg=self.colors['text'],
                font=('Arial', 9)).pack(side='left', padx=5)
        
        # Scan button
        self.scan_btn = tk.Button(
            num_frame,
            text="Scan for Sensors",
            command=self._scan_sensors,
            bg=self.colors['primary'],
            fg=self.colors['button_fg'],
            font=('Arial', 10, 'bold'),
            relief='flat',
            cursor='hand2',
            state='disabled'
        )
        self.scan_btn.pack(side='right', padx=5)
        
        # Sensor list with custom styling
        tree_frame = tk.Frame(left_frame, bg=self.colors['bg'])
        tree_frame.pack(fill='both', expand=True, padx=15, pady=(0, 15))
        
        # Create Treeview with scrollbar
        tree_scroll = tk.Scrollbar(tree_frame)
        tree_scroll.pack(side='right', fill='y')
        
        self.sensor_tree = ttk.Treeview(
            tree_frame,
            columns=('current', 'new', 'status', 'name', 'type'),
            show='tree headings',
            height=15,
            yscrollcommand=tree_scroll.set
        )
        tree_scroll.config(command=self.sensor_tree.yview)
        
        # Configure columns
        self.sensor_tree.heading('#0', text='#')
        self.sensor_tree.heading('current', text='Current Address')
        self.sensor_tree.heading('new', text='New Address')
        self.sensor_tree.heading('status', text='Status')
        self.sensor_tree.heading('name', text='Equipment Name')
        self.sensor_tree.heading('type', text='Type')
        
        self.sensor_tree.column('#0', width=40)
        self.sensor_tree.column('current', width=120)
        self.sensor_tree.column('new', width=120)
        self.sensor_tree.column('status', width=100)
        self.sensor_tree.column('name', width=150)
        self.sensor_tree.column('type', width=100)
        
        # Style the treeview
        self.sensor_tree.tag_configure('found', background=self.colors['success_bg'])
        self.sensor_tree.tag_configure('programmed', background=self.colors['info_bg'])
        self.sensor_tree.tag_configure('error', background=self.colors['warning_bg'])
        
        self.sensor_tree.pack(fill='both', expand=True)
        
        # Configuration buttons
        btn_frame = tk.Frame(left_frame, bg=self.colors['bg'])
        btn_frame.pack(fill='x', padx=15, pady=(0, 15))
        
        tk.Button(
            btn_frame,
            text="Auto-Assign Addresses",
            command=self._auto_assign,
            bg=self.colors['primary'],
            fg=self.colors['button_fg'],
            font=('Arial', 10),
            relief='flat',
            cursor='hand2'
        ).pack(side='left', padx=5)
        
        tk.Button(
            btn_frame,
            text="Program Selected",
            command=self._program_selected,
            bg=self.colors['primary'],
            fg=self.colors['button_fg'],
            font=('Arial', 10),
            relief='flat',
            cursor='hand2'
        ).pack(side='left', padx=5)
        
        tk.Button(
            btn_frame,
            text="Program All",
            command=self._program_all,
            bg=self.colors['success_border'],
            fg=self.colors['button_fg'],
            font=('Arial', 10, 'bold'),
            relief='flat',
            cursor='hand2'
        ).pack(side='left', padx=5)
        
        # Right panel
        right_frame = tk.Frame(content_frame, bg=self.colors['bg'])
        right_frame.pack(side='right', fill='both', expand=True)
        
        # Instructions with caution styling
        inst_container = tk.Frame(right_frame, bg=self.colors['caution_bg'],
                                 highlightbackground=self.colors['caution_border'],
                                 highlightthickness=0)
        inst_container.pack(fill='x', pady=(0, 10))
        
        # Yellow border on left
        yellow_border = tk.Frame(inst_container, bg=self.colors['caution_border'], width=4)
        yellow_border.pack(side='left', fill='y')
        
        inst_frame = tk.Frame(inst_container, bg=self.colors['caution_bg'])
        inst_frame.pack(fill='both', expand=True, padx=15, pady=10)
        
        tk.Label(inst_frame, text="Quick Start Instructions", 
                font=('Arial', 12, 'bold'),
                bg=self.colors['caution_bg'], 
                fg=self.colors['text']).pack(anchor='w')
        
        instructions = tk.Text(
            inst_frame,
            height=8,
            bg=self.colors['caution_bg'],
            fg=self.colors['text'],
            font=('Arial', 10),
            wrap='word',
            relief='flat',
            padx=10,
            pady=10
        )
        instructions.pack(fill='both', expand=True, pady=(10, 0))
        
        instructions.insert('1.0', """1. Connect your RS485 adapter to the computer
2. Click 'Connect' to establish communication
3. Set the number of sensors you want to configure (1-32)
4. Click 'Scan for Sensors' to discover all connected sensors
5. Use 'Auto-Assign Addresses' for sequential addressing
6. Click 'Program All' to configure all sensors at once

For installations with 10+ sensors, the system will automatically use batch programming mode for efficiency.""")
        
        instructions.config(state='disabled')
        
        # Console output
        console_container = tk.Frame(right_frame, bg=self.colors['bg'],
                                    highlightbackground=self.colors['border'],
                                    highlightthickness=1)
        console_container.pack(fill='both', expand=True)
        
        console_header = tk.Frame(console_container, bg=self.colors['bg'])
        console_header.pack(fill='x', padx=15, pady=(15, 5))
        
        tk.Label(console_header, text="System Console", 
                font=('Arial', 12, 'bold'),
                bg=self.colors['bg'], 
                fg=self.colors['text']).pack(anchor='w')
        
        self.console = scrolledtext.ScrolledText(
            console_container,
            bg=self.colors['console_bg'],
            fg=self.colors['console_fg'],
            font=('Consolas', 10),
            height=15,
            relief='flat',
            padx=10,
            pady=10
        )
        self.console.pack(fill='both', expand=True, padx=15, pady=(0, 15))
        
        # Bottom frame
        bottom_frame = tk.Frame(main_container, bg=self.colors['bg'])
        bottom_frame.pack(fill='x', padx=20, pady=(10, 20))
        
        # Footer separator
        tk.Frame(bottom_frame, height=2, bg=self.colors['primary']).pack(fill='x', pady=(0, 10))
        
        # Export/Import buttons
        file_frame = tk.Frame(bottom_frame, bg=self.colors['bg'])
        file_frame.pack(side='left')
        
        tk.Button(
            file_frame,
            text="Export Configuration",
            command=self._export_config,
            bg=self.colors['primary'],
            fg=self.colors['button_fg'],
            relief='flat',
            cursor='hand2'
        ).pack(side='left', padx=5)
        
        tk.Button(
            file_frame,
            text="Import Configuration",
            command=self._import_config,
            bg=self.colors['primary'],
            fg=self.colors['button_fg'],
            relief='flat',
            cursor='hand2'
        ).pack(side='left', padx=5)
        
        # Progress bar
        self.progress = ttk.Progressbar(
            bottom_frame,
            mode='determinate',
            length=400,
            style='Primary.Horizontal.TProgressbar'
        )
        self.progress.pack(side='right', padx=5)
        
        # Configure progress bar style
        self.style.configure('Primary.Horizontal.TProgressbar',
                           background=self.colors['primary'],
                           borderwidth=0,
                           lightcolor=self.colors['primary'],
                           darkcolor=self.colors['primary'])
    
    def log(self, message, level='INFO'):
        """Log message to console with appropriate styling"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        # Insert timestamp
        self.console.insert('end', f"{timestamp} ")
        
        # Insert level indicator with color
        if level == 'SUCCESS':
            self.console.insert('end', "[OK] ", 'success')
            self.console.tag_config('success', foreground=self.colors['success_border'])
        elif level == 'WARNING':
            self.console.insert('end', "[WARN] ", 'warning')
            self.console.tag_config('warning', foreground=self.colors['caution_border'])
        elif level == 'ERROR':
            self.console.insert('end', "[ERROR] ", 'error')
            self.console.tag_config('error', foreground=self.colors['warning_border'])
        
        # Insert message
        self.console.insert('end', f"{message}\n")
        self.console.see('end')
        self.root.update()
    
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
            delay_us = ((1000000 // (int(self.baud_var.get()) // 10)) * len(data)) + 300
            GPIO.output(self.direction_pin, GPIO.HIGH)
            self.serial_conn.write(data)
            self.serial_conn.flush()
            time.sleep(delay_us / 1000000.0)
            GPIO.output(self.direction_pin, GPIO.LOW)
        else:
            self.serial_conn.write(data)
            self.serial_conn.flush()
    
    def _scan_ports(self):
        """Scan for available serial ports"""
        ports = serial.tools.list_ports.comports()
        port_list = [port.device for port in ports]
        self.port_combo['values'] = port_list
        if port_list:
            self.port_combo.current(0)
    
    def _toggle_connection(self):
        """Toggle serial connection"""
        if not self.connected:
            try:
                port = self.port_var.get()
                baud = int(self.baud_var.get())
                
                self.serial_conn = serial.Serial(
                    port=port,
                    baudrate=baud,
                    timeout=0.5
                )
                
                self.connected = True
                self.connect_btn.config(text="Disconnect", bg=self.colors['warning_border'])
                self.status_frame.config(bg=self.colors['success_bg'])
                self.status_label.config(text="Connected", 
                                       fg=self.colors['success_border'],
                                       bg=self.colors['success_bg'])
                self.scan_btn.config(state='normal')
                self.log(f"Connected to {port} at {baud} baud", 'SUCCESS')
                
            except Exception as e:
                self.log(f"Connection failed: {e}", 'ERROR')
                messagebox.showerror("Connection Error", str(e))
        else:
            self._disconnect()
    
    def _disconnect(self):
        """Disconnect serial"""
        if self.serial_conn:
            self.serial_conn.close()
        self.connected = False
        self.connect_btn.config(text="Connect", bg=self.colors['primary'])
        self.status_frame.config(bg=self.colors['warning_bg'])
        self.status_label.config(text="Disconnected", 
                               fg=self.colors['warning_border'],
                               bg=self.colors['warning_bg'])
        self.scan_btn.config(state='disabled')
        self.log("Disconnected", 'INFO')
    
    def _scan_sensors(self):
        """Scan for all sensors"""
        if not self.connected:
            return
        
        self.log("Starting comprehensive sensor scan...", 'INFO')
        self.sensors.clear()
        self.sensor_tree.delete(*self.sensor_tree.get_children())
        
        # Disable buttons during scan
        self.scan_btn.config(state='disabled')
        
        # Run scan in thread
        thread = threading.Thread(target=self._scan_thread)
        thread.start()
    
    def _scan_thread(self):
        """Scan thread"""
        # Comprehensive address ranges
        address_ranges = {
            'Common': list(range(0x50, 0x60)),
            'Extended': list(range(0x60, 0x70)),
            'Legacy': list(range(0x01, 0x10)),
            'High': list(range(0x70, 0x80))
        }
        
        all_addresses = []
        for range_name, addresses in address_ranges.items():
            all_addresses.extend(addresses)
        
        total_addresses = len(all_addresses)
        found_count = 0
        
        self.log(f"Scanning {total_addresses} possible addresses...", 'INFO')
        
        for i, addr in enumerate(all_addresses):
            self.progress['value'] = ((i + 1) / total_addresses) * 100
            
            if self._test_sensor(addr):
                found_count += 1
                self.sensors[addr] = {
                    'current': addr,
                    'new': None,
                    'status': 'Found',
                    'name': f'Motor_{found_count}',
                    'type': 'WTVB01-485'
                }
                
                # Add to tree
                item = self.sensor_tree.insert(
                    '',
                    'end',
                    text=str(found_count),
                    values=(
                        f'0x{addr:02X}',
                        '',
                        'Found',
                        f'Motor_{found_count}',
                        'WTVB01-485'
                    ),
                    tags=('found',)
                )
                
                self.log(f"Found sensor at address 0x{addr:02X}", 'SUCCESS')
        
        self.progress['value'] = 0
        self.scan_btn.config(state='normal')
        
        # Summary
        self.log(f"Scan complete. Found {found_count} sensors.", 'INFO')
        
        if found_count > self.num_sensors_var.get():
            self.log(f"Found more sensors ({found_count}) than expected ({self.num_sensors_var.get()})", 'WARNING')
        elif found_count < self.num_sensors_var.get():
            self.log(f"Found fewer sensors ({found_count}) than expected ({self.num_sensors_var.get()})", 'WARNING')
    
    def _test_sensor(self, address):
        """Test if sensor exists at address"""
        try:
            # Build test command
            cmd = bytearray([address, 0x03, 0x00, 0x34, 0x00, 0x03])
            crc = self._calculate_crc16(cmd)
            cmd.append(crc & 0xFF)
            cmd.append((crc >> 8) & 0xFF)
            
            # Clear buffer and send
            self.serial_conn.reset_input_buffer()
            self._send_command(bytes(cmd))
            time.sleep(0.1)
            
            # Read response
            response = self.serial_conn.read(50)
            return len(response) >= 11 and response[0] == address and response[1] == 0x03
            
        except:
            return False
    
    def _auto_assign(self):
        """Auto-assign sequential addresses"""
        num_needed = self.num_sensors_var.get()
        
        # Get all sensors sorted by current address
        items = list(self.sensor_tree.get_children())
        
        if len(items) == 0:
            messagebox.showwarning("No Sensors", "Please scan for sensors first")
            return
        
        # Clear new addresses
        for item in items:
            self.sensor_tree.set(item, 'new', '')
        
        # Assign addresses starting from 0x50
        assigned = 0
        for i, item in enumerate(items):
            if assigned < num_needed:
                new_addr = 0x50 + assigned
                self.sensor_tree.set(item, 'new', f'0x{new_addr:02X}')
                values = list(self.sensor_tree.item(item)['values'])
                values[4] = f'Motor_{assigned + 1}_0x{new_addr:02X}'
                self.sensor_tree.item(item, values=values)
                assigned += 1
        
        self.log(f"Auto-assigned {assigned} sequential addresses starting from 0x50", 'SUCCESS')
    
    def _program_selected(self):
        """Program selected sensor"""
        selected = self.sensor_tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a sensor to program")
            return
        
        values = self.sensor_tree.item(selected[0])['values']
        if not values[1]:  # No new address
            messagebox.showwarning("No Address", "Please assign a new address first")
            return
        
        # Get addresses
        current_addr = int(values[0].replace('0x', ''), 16)
        new_addr = int(values[1].replace('0x', ''), 16)
        
        self.log(f"Programming sensor from {values[0]} to {values[1]}...", 'INFO')
        
        # Program in thread
        thread = threading.Thread(target=self._program_sensor, args=(current_addr, new_addr, selected[0]))
        thread.start()
    
    def _program_sensor(self, old_addr, new_addr, tree_item):
        """Program a single sensor"""
        try:
            # Unlock
            self.log(f"  Unlocking sensor at 0x{old_addr:02X}...", 'INFO')
            unlock_cmd = bytearray([old_addr, 0x06, 0x00, 0x69, 0xB5, 0x88])
            crc = self._calculate_crc16(unlock_cmd)
            unlock_cmd.append(crc & 0xFF)
            unlock_cmd.append((crc >> 8) & 0xFF)
            
            self.serial_conn.reset_input_buffer()
            self._send_command(bytes(unlock_cmd))
            time.sleep(0.2)
            
            # Set address
            self.log(f"  Setting address to 0x{new_addr:02X}...", 'INFO')
            addr_cmd = bytearray([old_addr, 0x06, 0x00, 0x1A, 0x00, new_addr])
            crc = self._calculate_crc16(addr_cmd)
            addr_cmd.append(crc & 0xFF)
            addr_cmd.append((crc >> 8) & 0xFF)
            
            self.serial_conn.reset_input_buffer()
            self._send_command(bytes(addr_cmd))
            time.sleep(0.2)
            
            # Save
            self.log(f"  Saving configuration...", 'INFO')
            save_cmd = bytearray([old_addr, 0x06, 0x00, 0x00, 0x00, 0x00])
            crc = self._calculate_crc16(save_cmd)
            save_cmd.append(crc & 0xFF)
            save_cmd.append((crc >> 8) & 0xFF)
            
            self.serial_conn.reset_input_buffer()
            self._send_command(bytes(save_cmd))
            time.sleep(2.0)
            
            # Test new address
            if self._test_sensor(new_addr):
                self.log(f"  SUCCESS! Sensor now responds at 0x{new_addr:02X}", 'SUCCESS')
                self.sensor_tree.set(tree_item, 'status', 'Programmed')
                self.sensor_tree.item(tree_item, tags=('programmed',))
                return True
            else:
                self.log(f"  FAILED! Sensor not responding at new address", 'ERROR')
                self.sensor_tree.set(tree_item, 'status', 'Error')
                self.sensor_tree.item(tree_item, tags=('error',))
                return False
                
        except Exception as e:
            self.log(f"  ERROR: {e}", 'ERROR')
            return False
    
    def _program_all(self):
        """Program all sensors with new addresses"""
        # Get all items with new addresses
        to_program = []
        for item in self.sensor_tree.get_children():
            values = self.sensor_tree.item(item)['values']
            if values[1]:  # Has new address
                current_addr = int(values[0].replace('0x', ''), 16)
                new_addr = int(values[1].replace('0x', ''), 16)
                to_program.append((item, current_addr, new_addr))
        
        if not to_program:
            messagebox.showwarning("No Configuration", "Please assign new addresses first")
            return
        
        # Confirm
        if messagebox.askyesno("Confirm Programming", 
                              f"Program {len(to_program)} sensors with new addresses?"):
            thread = threading.Thread(target=self._program_all_thread, args=(to_program,))
            thread.start()
    
    def _program_all_thread(self, sensors_to_program):
        """Program all sensors thread"""
        total = len(sensors_to_program)
        success_count = 0
        
        self.log(f"Starting batch programming of {total} sensors...", 'INFO')
        
        # Group sensors by current address (for handling duplicates)
        address_groups = {}
        for item, current, new in sensors_to_program:
            if current not in address_groups:
                address_groups[current] = []
            address_groups[current].append((item, new))
        
        # Program each group
        sensor_num = 0
        for current_addr, sensor_list in address_groups.items():
            if len(sensor_list) > 1:
                self.log(f"Found {len(sensor_list)} sensors at address 0x{current_addr:02X}", 'WARNING')
                self.log("Programming them sequentially...", 'INFO')
            
            for item, new_addr in sensor_list:
                sensor_num += 1
                self.progress['value'] = (sensor_num / total) * 100
                
                self.log(f"\nProgramming sensor {sensor_num}/{total}", 'INFO')
                
                if len(sensor_list) > 1:
                    self.log("Please ensure only the target sensor is connected", 'WARNING')
                    time.sleep(2)  # Give time for manual intervention if needed
                
                if self._program_sensor(current_addr, new_addr, item):
                    success_count += 1
                    # Update current address for next in group
                    current_addr = new_addr
                
                time.sleep(0.5)  # Small delay between sensors
        
        self.progress['value'] = 0
        
        # Summary
        self.log(f"\nBatch programming complete!", 'INFO')
        self.log(f"Successfully programmed: {success_count}/{total} sensors", 
                'SUCCESS' if success_count == total else 'WARNING')
        
        # Final verification
        self.log("\nPerforming final verification scan...", 'INFO')
        time.sleep(1)
        self._scan_sensors()
    
    def _export_config(self):
        """Export sensor configuration"""
        config = {
            'timestamp': datetime.now().isoformat(),
            'expected_sensors': self.num_sensors_var.get(),
            'sensors': []
        }
        
        for item in self.sensor_tree.get_children():
            values = self.sensor_tree.item(item)['values']
            config['sensors'].append({
                'current_address': values[0],
                'new_address': values[1],
                'status': values[2],
                'name': values[3],
                'type': values[4]
            })
        
        # Save to file
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile=f"sensor_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        if filename:
            with open(filename, 'w') as f:
                json.dump(config, f, indent=2)
            self.log(f"Configuration exported to {filename}", 'SUCCESS')
    
    def _import_config(self):
        """Import sensor configuration"""
        filename = filedialog.askopenfilename(
            title="Select Configuration File",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r') as f:
                    config = json.load(f)
                
                # Clear current list
                self.sensor_tree.delete(*self.sensor_tree.get_children())
                
                # Load configuration
                self.num_sensors_var.set(config.get('expected_sensors', 3))
                
                for i, sensor in enumerate(config['sensors']):
                    tag = 'found'
                    if sensor['status'] == 'Programmed':
                        tag = 'programmed'
                    elif sensor['status'] == 'Error':
                        tag = 'error'
                    
                    self.sensor_tree.insert(
                        '',
                        'end',
                        text=str(i+1),
                        values=(
                            sensor['current_address'],
                            sensor.get('new_address', ''),
                            sensor['status'],
                            sensor['name'],
                            sensor.get('type', 'WTVB01-485')
                        ),
                        tags=(tag,)
                    )
                
                self.log(f"Configuration imported from {filename}", 'SUCCESS')
                
            except Exception as e:
                self.log(f"Import failed: {e}", 'ERROR')
                messagebox.showerror("Import Error", str(e))

def main():
    root = tk.Tk()
    app = SensorConfigGUI(root)
    
    # Center window on screen
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    root.mainloop()

if __name__ == "__main__":
    main()