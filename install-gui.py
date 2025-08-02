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
import requests
from PIL import Image, ImageTk
import io

class InstallerWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("AutomataNexus Vibration Monitor Installer")
        self.root.geometry("600x500")
        self.root.resizable(False, False)
        
        # Color theme
        self.bg_color = "#f5f5f5"
        self.primary_color = "#f97316"  # Orange
        self.secondary_color = "#14b8a6"  # Teal
        self.text_color = "#374151"
        
        self.root.configure(bg=self.bg_color)
        
        # Create main frame
        self.main_frame = tk.Frame(root, bg=self.bg_color)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header with logo
        self.create_header()
        
        # Progress section
        self.create_progress_section()
        
        # Log section
        self.create_log_section()
        
        # Buttons
        self.create_buttons()
        
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
        
    def create_header(self):
        header_frame = tk.Frame(self.main_frame, bg=self.bg_color)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Logo placeholder (circle with gradient effect)
        logo_frame = tk.Frame(header_frame, bg=self.bg_color)
        logo_frame.pack(side=tk.LEFT, padx=(0, 15))
        
        # Create gradient-like logo
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
            text="Professional Installation Wizard",
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
        packages = [
            "python3", "python3-pip", "python3-venv",
            "git", "curl", "nodejs", "npm", "chromium-browser"
        ]
        
        for pkg in packages:
            self.log(f"  Installing {pkg}...")
            success, _ = self.run_command(f"sudo apt install -y {pkg}")
            if not success:
                self.log(f"✗ Failed to install {pkg}", "error")
                return False
                
        self.log("✓ All dependencies installed", "success")
        return True
        
    def install_python_packages(self):
        self.log("Installing Python packages...")
        packages = ["pyserial", "flask", "flask-cors", "numpy"]
        
        for pkg in packages:
            self.log(f"  Installing {pkg}...")
            success, _ = self.run_command(f"sudo pip3 install --break-system-packages {pkg}")
            if not success:
                self.log(f"✗ Failed to install {pkg}", "error")
                return False
                
        self.log("✓ Python packages installed", "success")
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
        self.log("Cloning repository...")
        os.chdir("/opt/automatanexus")
        success, _ = self.run_command("git clone https://github.com/AutomataControls/IS0-10816-Vibration-Sensor.git")
        if success:
            self.log("✓ Repository cloned successfully", "success")
            return True
        else:
            self.log("✗ Failed to clone repository", "error")
            return False
            
    def setup_service(self):
        self.log("Setting up systemd service...")
        service_content = """[Unit]
Description=AutomataNexus Vibration Monitor
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/opt/automatanexus/IS0-10816-Vibration-Sensor
ExecStart=/usr/bin/python3 /opt/automatanexus/IS0-10816-Vibration-Sensor/multi_port_vibration_monitor.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target"""
        
        try:
            with open("/tmp/vibration-monitor.service", "w") as f:
                f.write(service_content)
            self.run_command("sudo mv /tmp/vibration-monitor.service /etc/systemd/system/")
            self.run_command("sudo systemctl daemon-reload")
            self.run_command("sudo systemctl enable vibration-monitor.service")
            self.log("✓ Service configured", "success")
            return True
        except Exception as e:
            self.log(f"✗ Failed to setup service: {e}", "error")
            return False
            
    def configure_permissions(self):
        self.log("Configuring permissions...")
        user = os.environ.get('USER', 'pi')
        success, _ = self.run_command(f"sudo usermod -a -G dialout {user}")
        if success:
            self.log("✓ Permissions configured", "success")
            return True
        else:
            self.log("✗ Failed to configure permissions", "error")
            return False
            
    def create_shortcuts(self):
        self.log("Creating desktop shortcuts...")
        desktop_entry = """[Desktop Entry]
Type=Application
Name=Vibration Monitor
Comment=AutomataNexus Vibration Monitoring System
Icon=/opt/automatanexus/IS0-10816-Vibration-Sensor/icon.png
Exec=chromium-browser --app=http://localhost:5000/monitoring-app.html
Terminal=false
Categories=Utility;"""
        
        try:
            desktop_path = os.path.expanduser("~/Desktop")
            if not os.path.exists(desktop_path):
                os.makedirs(desktop_path)
                
            with open(f"{desktop_path}/vibration-monitor.desktop", "w") as f:
                f.write(desktop_entry)
                
            os.chmod(f"{desktop_path}/vibration-monitor.desktop", 0o755)
            self.log("✓ Desktop shortcut created", "success")
            return True
        except Exception as e:
            self.log(f"✗ Failed to create shortcuts: {e}", "error")
            return False
            
    def finalize_installation(self):
        self.log("Finalizing installation...")
        time.sleep(1)
        self.log("✓ Installation complete!", "success")
        self.log("\nNext steps:", "info")
        self.log("1. Reboot your Raspberry Pi: sudo reboot")
        self.log("2. Access the monitor at: http://localhost:5000/monitoring-app.html")
        self.log("3. Or click the 'Vibration Monitor' desktop icon")
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