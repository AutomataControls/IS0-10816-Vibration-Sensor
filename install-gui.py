#!/usr/bin/env python3
################################################################################
# AutomataNexus Vibration Monitor - GUI Installer
# Enterprise-Grade ISO 10816-3 Compliant Vibration Analysis Platform
################################################################################
#
# © 2025 AutomataNexus AI & AutomataControls. All rights reserved.
#
# COMMERCIAL LICENSE NOTICE:
# This software is commercially licensed, not open source. For licensing inquiries,
# contact DevOps@automatacontrols.com. See COMMERCIAL.md for full license terms.
#
# Professional installation wizard with progress tracking
################################################################################

"""
AutomataNexus Vibration Monitor GUI Installer
Professional installation wizard with progress tracking
"""

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import threading
import os
import sys
import time
import io

# Check if PIL is available
PIL_AVAILABLE = True
try:
    from PIL import Image, ImageTk
except ImportError:
    PIL_AVAILABLE = False
    print("Warning: PIL not available, logos will not be displayed")

try:
    import requests
except ImportError:
    requests = None

class InstallerWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("AutomataNexus Vibration Monitor Installer")
        self.root.geometry("700x600")
        self.root.resizable(False, False)
        
        # Center the window on screen
        self.root.update_idletasks()
        width = 700
        height = 600
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        
        # Color theme
        self.bg_color = "#f5f5f5"
        self.primary_color = "#f97316"  # Orange
        self.secondary_color = "#14b8a6"  # Teal
        self.text_color = "#374151"
        
        self.root.configure(bg=self.bg_color)
        
        # Start with welcome screen
        self.accepted_license = False
        self.current_step = 0
        self.installation_complete = False
        
        # Initialize variables that will be created later
        self.main_frame = None
        self.log_text = None
        self.progress_bar = None
        self.progress_label = None
        self.task_label = None
        self.install_button = None
        self.close_button = None
        self.steps = []
        
        # Show welcome screen - this should be the ONLY thing shown initially
        self.show_welcome_screen()
        
    def create_header(self):
        header_frame = tk.Frame(self.main_frame, bg=self.bg_color)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Logo
        logo_frame = tk.Frame(header_frame, bg=self.bg_color)
        logo_frame.pack(side=tk.LEFT, padx=(0, 15))
        
        # Try to load the actual logo
        logo_loaded = False
        try:
            # Check multiple possible logo locations
            logo_paths = [
                "automata-nexus-logo.png",
                "/home/Automata/IS0-10816-Vibration-Sensor/automata-nexus-logo.png",
                os.path.join(os.path.dirname(__file__), "automata-nexus-logo.png")
            ]
            
            for logo_path in logo_paths:
                if os.path.exists(logo_path):
                    if PIL_AVAILABLE:
                        img = Image.open(logo_path)
                        img = img.resize((60, 60), Image.Resampling.LANCZOS)
                        self.logo_img = ImageTk.PhotoImage(img)
                        logo_label = tk.Label(logo_frame, image=self.logo_img, bg=self.bg_color)
                        logo_label.pack()
                        logo_loaded = True
                        break
        except Exception as e:
            print(f"Could not load logo: {e}")
        
        # Fallback to drawn logo if image not loaded
        if not logo_loaded:
            canvas = tk.Canvas(logo_frame, width=60, height=60, bg=self.bg_color, highlightthickness=0)
            canvas.pack()
            
            # Draw gradient circle
            for i in range(30, 0, -2):
                color_value = int(255 - (255 - 240) * (i / 30))
                color = f"#{color_value:02x}{int(color_value * 0.7):02x}{int(color_value * 0.4):02x}"
                canvas.create_oval(30-i, 30-i, 30+i, 30+i, fill=color, outline="")
            
            # Add text
            canvas.create_text(30, 30, text="AN", font=("Arial", 20, "bold"), fill="white")
        
        # Title
        title_frame = tk.Frame(header_frame, bg=self.bg_color)
        title_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        title_label = tk.Label(
            title_frame, 
            text="AutomataNexus Vibration Monitor",
            font=("Arial", 18, "bold"),
            fg=self.text_color,
            bg=self.bg_color
        )
        title_label.pack(anchor=tk.W)
        
        subtitle_label = tk.Label(
            title_frame,
            text="Installation Wizard",
            font=("Arial", 12),
            fg="#6b7280",
            bg=self.bg_color
        )
        subtitle_label.pack(anchor=tk.W)
        
    def create_progress_section(self):
        progress_frame = tk.Frame(self.main_frame, bg=self.bg_color)
        progress_frame.pack(fill=tk.X, pady=20)
        
        # Current task label
        self.task_label = tk.Label(
            progress_frame,
            text="Ready to install",
            font=("Arial", 12),
            fg=self.text_color,
            bg=self.bg_color
        )
        self.task_label.pack(anchor=tk.W, pady=(0, 10))
        
        # Progress bar
        style = ttk.Style()
        style.theme_use('clam')
        style.configure(
            "Custom.Horizontal.TProgressbar",
            background=self.primary_color,
            troughcolor="#e5e7eb",
            bordercolor="#e5e7eb",
            lightcolor=self.primary_color,
            darkcolor=self.primary_color
        )
        
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            style="Custom.Horizontal.TProgressbar",
            length=560,
            mode='determinate'
        )
        self.progress_bar.pack(fill=tk.X)
        
        # Progress percentage
        self.progress_label = tk.Label(
            progress_frame,
            text="0%",
            font=("Arial", 10),
            fg="#6b7280",
            bg=self.bg_color
        )
        self.progress_label.pack(anchor=tk.E, pady=(5, 0))
        
    def create_log_section(self):
        log_frame = tk.Frame(self.main_frame, bg=self.bg_color)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=20)
        
        # Log text area
        self.log_text = tk.Text(
            log_frame,
            height=12,
            width=70,
            font=("Courier", 9),
            bg="white",
            fg=self.text_color,
            relief=tk.FLAT,
            bd=1
        )
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Scrollbar
        scrollbar = tk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        # Configure tags for colored output
        self.log_text.tag_configure("success", foreground="#10b981")
        self.log_text.tag_configure("error", foreground="#ef4444")
        self.log_text.tag_configure("info", foreground="#3b82f6")
        self.log_text.tag_configure("warning", foreground="#f59e0b")
        
    def create_buttons(self):
        button_frame = tk.Frame(self.main_frame, bg=self.bg_color)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        self.install_button = tk.Button(
            button_frame,
            text="Install",
            font=("Arial", 12, "bold"),
            bg=self.primary_color,
            fg="white",
            padx=30,
            pady=10,
            relief=tk.FLAT,
            cursor="hand2",
            command=self.start_installation
        )
        self.install_button.pack(side=tk.LEFT)
        
        self.close_button = tk.Button(
            button_frame,
            text="Close",
            font=("Arial", 12),
            bg="#e5e7eb",
            fg=self.text_color,
            padx=30,
            pady=10,
            relief=tk.FLAT,
            cursor="hand2",
            command=self.close_installer
        )
        self.close_button.pack(side=tk.RIGHT)
        
    def show_welcome_screen(self):
        """Show welcome screen with license agreement"""
        # Clear any existing widgets
        for widget in self.root.winfo_children():
            widget.destroy()
            
        # Welcome frame
        welcome_frame = tk.Frame(self.root, bg=self.bg_color)
        welcome_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=40)
        
        # Logo and title
        header_frame = tk.Frame(welcome_frame, bg=self.bg_color)
        header_frame.pack(pady=(0, 30))
        
        # Try to load logo
        logo_loaded = False
        try:
            logo_paths = [
                "automata-nexus-logo.png",
                os.path.join(os.path.dirname(__file__), "automata-nexus-logo.png"),
                os.path.join(os.getcwd(), "automata-nexus-logo.png"),
                "/home/Automata/IS0-10816-Vibration-Sensor/automata-nexus-logo.png"
            ]
            for logo_path in logo_paths:
                if os.path.exists(logo_path):
                    if PIL_AVAILABLE:
                        img = Image.open(logo_path)
                        img = img.resize((80, 80), Image.Resampling.LANCZOS)
                        self.welcome_logo = ImageTk.PhotoImage(img)
                        logo_label = tk.Label(header_frame, image=self.welcome_logo, bg=self.bg_color)
                        logo_label.pack()
                        logo_loaded = True
                        break
        except:
            pass
            
        if not logo_loaded:
            # Fallback logo
            canvas = tk.Canvas(header_frame, width=80, height=80, bg=self.bg_color, highlightthickness=0)
            canvas.pack()
            canvas.create_oval(10, 10, 70, 70, fill=self.primary_color, outline="")
            canvas.create_text(40, 40, text="AN", font=("Arial", 24, "bold"), fill="white")
        
        tk.Label(header_frame, text="AutomataNexus Vibration Monitor", 
                font=("Arial", 20, "bold"), fg=self.text_color, bg=self.bg_color).pack(pady=(10, 0))
        tk.Label(header_frame, text="Enterprise-Grade ISO 10816-3 Compliant System", 
                font=("Arial", 12), fg="#6b7280", bg=self.bg_color).pack()
        
        # Welcome message
        welcome_text = tk.Label(welcome_frame, 
                               text="Welcome to the AutomataNexus Vibration Monitor installer.\n" +
                                    "This wizard will guide you through the installation process.",
                               font=("Arial", 11), fg=self.text_color, bg=self.bg_color,
                               justify="center")
        welcome_text.pack(pady=(0, 20))
        
        # License frame
        license_frame = tk.LabelFrame(welcome_frame, text="Commercial License Agreement", 
                                     font=("Arial", 12, "bold"), fg=self.text_color, bg=self.bg_color)
        license_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # License text
        license_text = tk.Text(license_frame, height=12, width=70, 
                              font=("Courier", 9), bg="white", fg=self.text_color,
                              wrap=tk.WORD, relief=tk.FLAT, bd=1)
        license_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        license_content = """COMMERCIAL LICENSE NOTICE

© 2025 AutomataNexus AI & AutomataControls. All rights reserved.

This software is commercially licensed, not open source. By installing and using this software, you agree to the following terms:

1. LICENSE REQUIRED: A valid commercial license is required for production use.
   - Professional License: $500-$1,500 (up to 5 sensors)
   - Business License: $2,500-$5,000 (up to 16 sensors per location)
   - Enterprise License: $10,000+ (unlimited sensors)

2. EVALUATION PERIOD: You may evaluate this software for 30 days without a license.

3. RESTRICTIONS: You may NOT:
   - Distribute or resell this software
   - Reverse engineer or modify the code
   - Remove copyright notices
   - Use without a valid license after evaluation

4. WARRANTY DISCLAIMER: This software is provided "AS IS" without warranty of any kind.

5. INDUSTRIAL USE: Proper installation by qualified personnel is required. We are not responsible for equipment damage or safety issues.

For licensing inquiries: DevOps@automatacontrols.com
Full license terms: See COMMERCIAL.md

By clicking "I Accept", you acknowledge that you have read and agree to these terms."""
        
        license_text.insert("1.0", license_content)
        license_text.config(state=tk.DISABLED)
        
        # License acceptance checkbox
        self.accept_var = tk.BooleanVar()
        accept_check = tk.Checkbutton(welcome_frame, 
                                     text="I have read and accept the license agreement",
                                     variable=self.accept_var, font=("Arial", 11),
                                     fg=self.text_color, bg=self.bg_color,
                                     command=self.check_accept_button)
        accept_check.pack()
        
        # Buttons
        button_frame = tk.Frame(welcome_frame, bg=self.bg_color)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        self.cancel_welcome_button = tk.Button(button_frame, text="Cancel", 
                                              font=("Arial", 12), bg="#e5e7eb", 
                                              fg=self.text_color, padx=40, pady=15,
                                              relief=tk.FLAT, command=self.root.quit)
        self.cancel_welcome_button.pack(side=tk.LEFT)
        
        self.accept_button = tk.Button(button_frame, text="I Accept", 
                                      font=("Arial", 12, "bold"), 
                                      bg=self.primary_color, fg="white",
                                      padx=40, pady=15, relief=tk.FLAT,
                                      state=tk.DISABLED,
                                      command=self.accept_license)
        self.accept_button.pack(side=tk.RIGHT)
        
    def check_accept_button(self):
        """Enable/disable accept button based on checkbox"""
        if self.accept_var.get():
            self.accept_button.config(state=tk.NORMAL)
        else:
            self.accept_button.config(state=tk.DISABLED)
            
    def accept_license(self):
        """User accepted license, show main installer"""
        self.accepted_license = True
        
        # Clear welcome screen
        for widget in self.root.winfo_children():
            widget.destroy()
            
        # Create main installer interface
        self.main_frame = tk.Frame(self.root, bg=self.bg_color)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header with logo
        self.create_header()
        
        # Progress section
        self.create_progress_section()
        
        # Log section
        self.create_log_section()
        
        # Buttons
        self.create_buttons()
        
        # Setup installation steps
        self.steps = [
            ("Updating system packages...", self.update_system),
            ("Installing dependencies...", self.install_dependencies),
            ("Installing Python packages...", self.install_python_packages),
            ("Creating directories...", self.create_directories),
            ("Cloning repository...", self.clone_repository),
            ("Setting up service...", self.setup_service),
            ("Configuring permissions...", self.configure_permissions),
            ("Creating shortcuts...", self.create_shortcuts),
            ("Finalizing installation...", self.finalize_installation)
        ]
        
        self.current_step = 0
        self.installation_complete = False
        
    def log(self, message, tag="info"):
        self.log_text.insert(tk.END, f"{message}\n", tag)
        self.log_text.see(tk.END)
        self.root.update()
        
    def update_progress(self, value, task=""):
        self.progress_bar['value'] = value
        self.progress_label.config(text=f"{int(value)}%")
        if task:
            self.task_label.config(text=task)
        self.root.update()
        
    def run_command(self, command, shell=True):
        try:
            result = subprocess.run(
                command,
                shell=shell,
                capture_output=True,
                text=True,
                check=True
            )
            return True, result.stdout
        except subprocess.CalledProcessError as e:
            return False, e.stderr
            
    def update_system(self):
        self.log("Updating system packages...")
        success, output = self.run_command("sudo apt update -y")
        if success:
            self.log("✓ System updated successfully", "success")
        else:
            self.log("✗ Failed to update system", "error")
            return False
        return True
        
    def install_dependencies(self):
        self.log("Installing required packages...")
        
        # Core packages that must be installed
        core_packages = [
            "python3", "python3-pip", "python3-venv",
            "git", "curl", "sqlite3"
        ]
        
        # Python packages
        python_packages = [
            "python3-tk", "python3-pil", "python3-pil.imagetk",
            "python3-numpy", "python3-scipy", "python3-pandas",
            "python3-flask", "python3-flask-cors", "python3-serial",
            "python3-dotenv"
        ]
        
        # Optional packages (may have conflicts)
        optional_packages = [
            "nodejs", "npm", "chromium-browser"
        ]
        
        # Install core packages
        self.log("Installing core packages...")
        for pkg in core_packages:
            self.log(f"  Installing {pkg}...")
            success, output = self.run_command(f"sudo apt install -y {pkg}")
            if not success:
                self.log(f"  ✗ Failed: {pkg} - {output}", "error")
                return False
        
        # Install Python packages
        self.log("Installing Python packages...")
        for pkg in python_packages:
            self.log(f"  Installing {pkg}...")
            success, output = self.run_command(f"sudo apt install -y {pkg}")
            if not success:
                self.log(f"  ⚠ Warning: {pkg} failed, will try pip later", "warning")
        
        # Try optional packages individually
        self.log("Installing optional packages...")
        
        # Handle Node.js/npm conflicts
        self.log("  Checking Node.js installation...")
        success, output = self.run_command("which node")
        if not success:
            # Try to install nodejs
            self.log("  Installing Node.js...")
            success, output = self.run_command("sudo apt install -y nodejs")
            if not success:
                self.log("  ⚠ Node.js installation failed - Node-RED features may not work", "warning")
        
        # Try npm separately
        success, output = self.run_command("which npm")
        if not success:
            self.log("  Installing npm...")
            # First remove any conflicting packages
            self.run_command("sudo apt remove -y npm nodejs-legacy libnode72", shell=True)
            success, output = self.run_command("sudo apt install -y npm")
            if not success:
                self.log("  ⚠ npm installation failed - Node-RED features may not work", "warning")
        
        # Chromium browser
        self.log("  Checking browser...")
        success, output = self.run_command("which chromium-browser || which chromium")
        if not success:
            self.log("  Installing Chromium...")
            success, output = self.run_command("sudo apt install -y chromium-browser || sudo apt install -y chromium")
            if not success:
                self.log("  ⚠ Chromium installation failed - web UI will open in default browser", "warning")
                
        self.log("✓ Core dependencies installed", "success")
        return True
        
    def install_python_packages(self):
        self.log("Installing Python packages...")
        packages = ["pyserial", "flask", "flask-cors", "numpy", "Pillow"]
        
        # Check if packages are already installed via apt, only install missing ones via pip
        for pkg in packages:
            self.log(f"  Checking {pkg}...")
            # First try importing to see if already available
            check_cmd = f"python3 -c 'import {pkg.lower()}' 2>/dev/null"
            if pkg == "Pillow":
                check_cmd = "python3 -c 'import PIL' 2>/dev/null"
            
            success, _ = self.run_command(check_cmd)
            if not success:
                # Package not found, install via pip
                self.log(f"  Installing {pkg} via pip...")
                success, _ = self.run_command(f"sudo pip3 install --break-system-packages {pkg}")
                if not success:
                    self.log(f"✗ Failed to install {pkg}", "error")
                    return False
                
        self.log("✓ Python packages verified/installed", "success")
        return True
        
    def create_directories(self):
        self.log("Creating application directories...")
        success, _ = self.run_command("sudo mkdir -p /opt/automatanexus")
        if success:
            self.run_command(f"sudo chown {os.environ.get('USER', 'pi')}:{os.environ.get('USER', 'pi')} /opt/automatanexus")
            self.log("✓ Directories created", "success")
            return True
        else:
            self.log("✗ Failed to create directories", "error")
            return False
            
    def clone_repository(self):
        self.log("Setting up repository...")
        
        # Check if we're already in the repository
        current_dir = os.getcwd()
        if "IS0-10816-Vibration-Sensor" in current_dir:
            self.log("Already in repository, copying files...")
            # Copy current directory to installation location
            success, output = self.run_command(f"sudo cp -r {current_dir} /opt/automatanexus/")
            if not success:
                self.log(f"✗ Failed to copy files: {output}", "error")
                return False
        else:
            # Clone fresh repository
            self.log("Cloning repository...")
            os.chdir("/opt/automatanexus")
            success, _ = self.run_command("git clone https://github.com/AutomataControls/IS0-10816-Vibration-Sensor.git")
            if not success:
                self.log("✗ Failed to clone repository", "error")
                return False
                
        # Make scripts executable
        self.log("Making scripts executable...")
        scripts = [
            "multi_port_vibration_monitor.py",
            "install.sh",
            "install-gui.py",
            "install-on-pi.sh",
            "uninstall.sh"
        ]
        
        for script in scripts:
            script_path = f"/opt/automatanexus/IS0-10816-Vibration-Sensor/{script}"
            self.run_command(f"sudo chmod +x {script_path}")
            
        # Set up database
        self.log("Setting up database...")
        db_path = "/opt/automatanexus/IS0-10816-Vibration-Sensor/vibration_metrics.db"
        
        # Create empty database file with proper permissions
        self.run_command(f"sudo touch {db_path}")
        self.run_command(f"sudo chmod 666 {db_path}")
        self.run_command(f"sudo chown {os.environ.get('USER', 'pi')}:{os.environ.get('USER', 'pi')} {db_path}")
        
        self.log("✓ Repository setup complete", "success")
        return True
            
    def setup_service(self):
        self.log("Setting up systemd service...")
        # Get current user
        current_user = os.environ.get('USER', 'pi')
        
        service_content = f"""[Unit]
Description=AutomataNexus Vibration Monitor
After=network.target

[Service]
Type=simple
User={current_user}
WorkingDirectory=/opt/automatanexus/IS0-10816-Vibration-Sensor
ExecStart=/usr/bin/python3 /opt/automatanexus/IS0-10816-Vibration-Sensor/multi_port_vibration_monitor.py
Restart=always
RestartSec=10
Environment="PYTHONUNBUFFERED=1"

[Install]
WantedBy=multi-user.target"""
        
        try:
            with open("/tmp/vibration-monitor.service", "w") as f:
                f.write(service_content)
            self.run_command("sudo mv /tmp/vibration-monitor.service /etc/systemd/system/")
            self.run_command("sudo systemctl daemon-reload")
            # Don't enable or start - let the desktop icon control it
            # self.run_command("sudo systemctl enable vibration-monitor.service")
            # self.run_command("sudo systemctl start vibration-monitor.service")
            self.log("✓ Service configured (manual start via desktop icon)", "success")
            return True
        except Exception as e:
            self.log(f"✗ Failed to setup service: {e}", "error")
            return False
            
    def configure_permissions(self):
        self.log("Configuring permissions...")
        user = os.environ.get('USER', 'pi')
        
        # Add user to dialout group for USB access
        success, _ = self.run_command(f"sudo usermod -a -G dialout {user}")
        if not success:
            self.log("✗ Failed to add user to dialout group", "error")
            return False
            
        # Set proper ownership and permissions on the entire directory
        app_dir = "/opt/automatanexus/IS0-10816-Vibration-Sensor"
        self.log("Setting directory permissions...")
        
        # Change ownership of the entire directory to the user
        self.run_command(f"sudo chown -R {user}:{user} {app_dir}")
        
        # Ensure the directory is writable for CSV files
        self.run_command(f"sudo chmod -R 755 {app_dir}")
        
        # Make sure the database is writable
        self.run_command(f"sudo chmod 666 {app_dir}/vibration_metrics.db")
        
        self.log("✓ Permissions configured", "success")
        return True
            
    def create_shortcuts(self):
        self.log("Creating desktop shortcuts...")
        
        # First, copy the logo to the installation directory
        try:
            logo_src = os.path.join(os.path.dirname(__file__), "automata-nexus-logo.png")
            logo_dst = "/opt/automatanexus/IS0-10816-Vibration-Sensor/automata-nexus-logo.png"
            if os.path.exists(logo_src):
                self.run_command(f"sudo cp {logo_src} {logo_dst}")
                self.run_command(f"sudo chmod 644 {logo_dst}")
                icon_path = logo_dst
            else:
                # Create a simple icon if logo not found
                icon_path = "/opt/automatanexus/IS0-10816-Vibration-Sensor/icon.png"
                self.log("  Creating fallback icon...", "warning")
        except:
            icon_path = "/opt/automatanexus/IS0-10816-Vibration-Sensor/icon.png"
            
        # Create a launcher script first
        launcher_script = """#!/bin/bash
# AutomataNexus Vibration Monitor Launcher
# This script starts the service, opens the UI, and stops the service when closed

# Ensure we're using HTTP, not file://
URL="http://localhost:5000/monitoring-app.html"

# Function to check if Flask is responding
check_flask() {
    curl -s -o /dev/null -w "%{http_code}" "$URL" 2>/dev/null
}

# Function to cleanup on exit
cleanup() {
    echo "Stopping vibration monitor service..."
    sudo systemctl stop vibration-monitor
    exit 0
}

# Trap exit signals to ensure cleanup
trap cleanup EXIT INT TERM

# Stop any existing instance first
if systemctl is-active --quiet vibration-monitor; then
    echo "Stopping existing instance..."
    sudo systemctl stop vibration-monitor
    sleep 2
fi

# Start the service
echo "Starting vibration monitor service..."
sudo systemctl start vibration-monitor

# Wait for Flask to be ready (up to 30 seconds)
echo "Waiting for monitoring service to start..."
for i in {1..30}; do
    if [ "$(check_flask)" = "200" ]; then
        echo "Service is ready!"
        break
    fi
    sleep 1
done

# Final check before opening browser
if [ "$(check_flask)" != "200" ]; then
    echo "ERROR: Service failed to start properly"
    echo ""
    echo "=== Service Status ==="
    systemctl status vibration-monitor --no-pager
    echo ""
    echo "=== Recent Logs ==="
    sudo journalctl -u vibration-monitor -n 20 --no-pager
    echo ""
    echo "=== Direct Test ==="
    echo "Trying to run the script directly to see error..."
    cd /opt/automatanexus/IS0-10816-Vibration-Sensor
    /usr/bin/python3 multi_port_vibration_monitor.py 2>&1 | head -20
    echo ""
    echo "Press Enter to exit..."
    read
    exit 1
fi

# Launch browser and wait for it to close
echo "Launching monitoring interface..."
if command -v chromium-browser &> /dev/null; then
    chromium-browser --app="$URL" 2>/dev/null
elif command -v chromium &> /dev/null; then
    chromium --app="$URL" 2>/dev/null
elif command -v firefox &> /dev/null; then
    firefox --new-window "$URL" 2>/dev/null
else
    xdg-open "$URL" 2>/dev/null
fi

# Browser closed, cleanup will happen via trap
"""
        launcher_path = "/opt/automatanexus/IS0-10816-Vibration-Sensor/launch-monitor.sh"
        try:
            with open("/tmp/launch-monitor.sh", "w") as f:
                f.write(launcher_script)
            self.run_command("sudo mv /tmp/launch-monitor.sh " + launcher_path)
            self.run_command(f"sudo chmod +x {launcher_path}")
            self.log("  ✓ Launcher script created", "success")
        except Exception as e:
            self.log(f"  ⚠ Failed to create launcher: {e}", "warning")
            
        desktop_entry = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=Vibration Monitor
Comment=AutomataNexus Vibration Monitoring System
Icon={icon_path}
Exec={launcher_path}
Terminal=true
Categories=Utility;System;Monitor;
StartupNotify=true
StartupWMClass=chromium-browser"""
        
        shortcuts_created = 0
        
        # Create desktop shortcut
        try:
            desktop_path = os.path.expanduser("~/Desktop")
            if os.path.exists(desktop_path):
                desktop_file = f"{desktop_path}/vibration-monitor.desktop"
                with open(desktop_file, "w") as f:
                    f.write(desktop_entry)
                os.chmod(desktop_file, 0o755)
                
                # Mark as trusted on some systems
                self.run_command(f"gio set {desktop_file} metadata::trusted true", shell=True)
                self.log("  ✓ Desktop shortcut created", "success")
                shortcuts_created += 1
        except Exception as e:
            self.log(f"  ⚠ Desktop shortcut failed: {e}", "warning")
            
        # Create menu entry
        try:
            menu_path = os.path.expanduser("~/.local/share/applications")
            if not os.path.exists(menu_path):
                os.makedirs(menu_path)
            menu_file = f"{menu_path}/vibration-monitor.desktop"
            with open(menu_file, "w") as f:
                f.write(desktop_entry)
            os.chmod(menu_file, 0o755)
            self.log("  ✓ Menu entry created", "success")
            shortcuts_created += 1
            
            # Update desktop database
            self.run_command("update-desktop-database ~/.local/share/applications", shell=True)
        except Exception as e:
            self.log(f"  ⚠ Menu entry failed: {e}", "warning")
            
        return shortcuts_created > 0
            
    def finalize_installation(self):
        self.log("Finalizing installation...")
        time.sleep(1)
        self.log("✓ Installation complete!", "success")
        self.log("\nNext steps:", "info")
        self.log("1. Reboot your Raspberry Pi: sudo reboot")
        self.log("2. Click the 'Vibration Monitor' desktop icon to start")
        self.log("3. The service will stop when you close the browser")
        return True
        
    def start_installation(self):
        self.install_button.config(state=tk.DISABLED, text="Installing...")
        self.close_button.config(state=tk.DISABLED)
        
        # Run installation in separate thread
        install_thread = threading.Thread(target=self.run_installation)
        install_thread.start()
        
    def run_installation(self):
        total_steps = len(self.steps)
        
        for i, (description, func) in enumerate(self.steps):
            self.current_step = i
            progress = (i / total_steps) * 100
            self.update_progress(progress, description)
            
            success = func()
            if not success:
                self.update_progress(progress, "Installation failed!")
                messagebox.showerror("Installation Failed", 
                                   "The installation encountered an error. Please check the log for details.")
                self.install_button.config(state=tk.NORMAL, text="Retry")
                self.close_button.config(state=tk.NORMAL)
                return
                
            # Update to show step completion
            progress = ((i + 1) / total_steps) * 100
            self.update_progress(progress)
            time.sleep(0.5)
            
        self.installation_complete = True
        self.update_progress(100, "Installation complete!")
        self.install_button.config(text="Reboot", state=tk.NORMAL, command=self.reboot_system)
        self.close_button.config(state=tk.NORMAL)
        
        messagebox.showinfo("Installation Complete",
                          "AutomataNexus Vibration Monitor has been installed successfully!\n\n" +
                          "Please reboot your system to complete the installation.")
        
    def reboot_system(self):
        if messagebox.askyesno("Reboot System", "Are you sure you want to reboot now?"):
            self.run_command("sudo reboot")
            
    def close_installer(self):
        if not self.installation_complete:
            if messagebox.askyesno("Exit Installer", "Installation is not complete. Are you sure you want to exit?"):
                self.root.quit()
        else:
            self.root.quit()

def main():
    # Check if running with GUI
    if os.environ.get('DISPLAY'):
        root = tk.Tk()
        installer = InstallerWindow(root)
        root.mainloop()
    else:
        print("No display detected. Please run install-on-pi.sh for command-line installation.")
        sys.exit(1)

if __name__ == "__main__":
    main()