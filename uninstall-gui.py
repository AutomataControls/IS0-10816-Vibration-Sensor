#!/usr/bin/env python3
################################################################################
# AutomataNexus Vibration Monitor - GUI Uninstaller
# Enterprise-Grade ISO 10816-3 Compliant Vibration Analysis Platform
################################################################################
#
# © 2025 AutomataNexus AI & AutomataControls. All rights reserved.
#
# COMMERCIAL LICENSE NOTICE:
# This software is commercially licensed, not open source. For licensing inquiries,
# contact DevOps@automatacontrols.com. See COMMERCIAL.md for full license terms.
#
# Professional uninstallation wizard with progress tracking
################################################################################

"""
AutomataNexus Vibration Monitor GUI Uninstaller
Professional uninstallation wizard with component selection
"""

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import threading
import os
import sys
import time
from PIL import Image, ImageTk
import io

class UninstallerWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("AutomataNexus Vibration Monitor - Uninstaller")
        self.root.geometry("700x600")
        self.root.resizable(False, False)
        
        # Colors matching our theme
        self.bg_color = "#f0fdf4"  # Ultra light mint
        self.primary_color = "#14b8a6"  # Teal
        self.secondary_color = "#0891b2"  # Cyan
        self.danger_color = "#ef4444"  # Red
        self.text_color = "#134e4a"
        self.card_bg = "#ffffff"
        
        self.root.configure(bg=self.bg_color)
        
        # Configure styles
        self.setup_styles()
        
        # Component tracking
        self.components_to_remove = tk.BooleanVar(value=True)
        self.remove_service = tk.BooleanVar(value=True)
        self.remove_files = tk.BooleanVar(value=True)
        self.remove_config = tk.BooleanVar(value=True)
        self.remove_database = tk.BooleanVar(value=True)
        self.remove_nodered = tk.BooleanVar(value=True)
        self.remove_desktop = tk.BooleanVar(value=True)
        self.remove_logs = tk.BooleanVar(value=True)
        
        # Create main UI
        self.create_widgets()
        
    def setup_styles(self):
        """Configure ttk styles"""
        style = ttk.Style()
        
        # Configure button styles
        style.configure("Danger.TButton",
                       foreground="white",
                       background=self.danger_color,
                       borderwidth=0,
                       focuscolor="none",
                       padding=(20, 12))
        style.map("Danger.TButton",
                 background=[('active', '#dc2626')])
        
        style.configure("Secondary.TButton",
                       foreground="white",
                       background="#6b7280",
                       borderwidth=0,
                       focuscolor="none",
                       padding=(20, 12))
        style.map("Secondary.TButton",
                 background=[('active', '#4b5563')])
        
        # Configure progress bar
        style.configure("Danger.Horizontal.TProgressbar",
                       background=self.danger_color,
                       troughcolor="#fee2e2",
                       borderwidth=0,
                       lightcolor=self.danger_color,
                       darkcolor=self.danger_color)
        
    def create_widgets(self):
        """Create the main UI"""
        # Header with logo
        header_frame = tk.Frame(self.root, bg=self.card_bg, height=80)
        header_frame.pack(fill="x", padx=20, pady=(20, 0))
        header_frame.pack_propagate(False)
        
        # Logo and title
        logo_frame = tk.Frame(header_frame, bg=self.card_bg)
        logo_frame.pack(side="left", padx=20, pady=15)
        
        # Create AutomataNexus logo
        logo_canvas = tk.Canvas(logo_frame, width=50, height=50, 
                               bg=self.card_bg, highlightthickness=0)
        logo_canvas.pack(side="left")
        
        # Draw logo
        gradient_id = logo_canvas.create_oval(5, 5, 45, 45, 
                                            fill=self.primary_color, 
                                            outline=self.secondary_color, 
                                            width=2)
        logo_canvas.create_text(25, 25, text="AN", 
                               font=("Arial", 18, "bold"), 
                               fill="white")
        
        title_frame = tk.Frame(header_frame, bg=self.card_bg)
        title_frame.pack(side="left", padx=10, pady=20)
        
        tk.Label(title_frame, text="Vibration Monitor Uninstaller", 
                font=("Arial", 20, "bold"), 
                fg=self.text_color, bg=self.card_bg).pack(anchor="w")
        tk.Label(title_frame, text="Remove all components safely", 
                font=("Arial", 12), 
                fg="#6b7280", bg=self.card_bg).pack(anchor="w")
        
        # Warning card
        warning_frame = tk.Frame(self.root, bg="#fef3c7", relief="flat", borderwidth=1)
        warning_frame.pack(fill="x", padx=20, pady=10)
        
        warning_inner = tk.Frame(warning_frame, bg="#fef3c7")
        warning_inner.pack(padx=15, pady=12)
        
        tk.Label(warning_inner, text="⚠️  Warning", 
                font=("Arial", 14, "bold"), 
                fg="#92400e", bg="#fef3c7").pack(anchor="w")
        tk.Label(warning_inner, 
                text="This will permanently remove the AutomataNexus Vibration Monitor.\nAll data and configurations will be deleted.",
                font=("Arial", 11), 
                fg="#78350f", bg="#fef3c7", 
                justify="left").pack(anchor="w", pady=(5, 0))
        
        # Components selection
        components_frame = tk.Frame(self.root, bg=self.card_bg, relief="flat", borderwidth=1)
        components_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        tk.Label(components_frame, text="Components to Remove", 
                font=("Arial", 14, "bold"), 
                fg=self.text_color, bg=self.card_bg).pack(anchor="w", padx=15, pady=(15, 10))
        
        # Checkboxes for components
        check_frame = tk.Frame(components_frame, bg=self.card_bg)
        check_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        components = [
            (self.remove_service, "System Service", "Stop and remove the vibration monitor service"),
            (self.remove_files, "Application Files", "Remove all files from /opt/automatanexus-vibration-monitor"),
            (self.remove_config, "Configuration", "Delete all configuration files"),
            (self.remove_database, "Database", "Remove vibration data database (cannot be recovered)"),
            (self.remove_nodered, "Node-RED Package", "Uninstall Node-RED integration package"),
            (self.remove_desktop, "Desktop Shortcuts", "Remove desktop and menu shortcuts"),
            (self.remove_logs, "Log Files", "Delete all log files")
        ]
        
        for var, title, desc in components:
            comp_frame = tk.Frame(check_frame, bg=self.card_bg)
            comp_frame.pack(fill="x", pady=5)
            
            cb = tk.Checkbutton(comp_frame, text=title, variable=var,
                               font=("Arial", 11, "bold"),
                               fg=self.text_color, bg=self.card_bg,
                               activebackground=self.card_bg,
                               selectcolor=self.card_bg)
            cb.pack(anchor="w")
            
            tk.Label(comp_frame, text=f"  {desc}",
                    font=("Arial", 9),
                    fg="#6b7280", bg=self.card_bg).pack(anchor="w", padx=(25, 0))
        
        # Progress frame (initially hidden)
        self.progress_frame = tk.Frame(self.root, bg=self.card_bg, relief="flat", borderwidth=1)
        
        progress_inner = tk.Frame(self.progress_frame, bg=self.card_bg)
        progress_inner.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.status_label = tk.Label(progress_inner, text="Preparing uninstallation...", 
                                    font=("Arial", 12), 
                                    fg=self.text_color, bg=self.card_bg)
        self.status_label.pack(pady=(0, 10))
        
        self.progress = ttk.Progressbar(progress_inner, style="Danger.Horizontal.TProgressbar",
                                       mode='determinate', length=400)
        self.progress.pack(pady=10)
        
        self.detail_label = tk.Label(progress_inner, text="", 
                                    font=("Arial", 10), 
                                    fg="#6b7280", bg=self.card_bg)
        self.detail_label.pack(pady=5)
        
        # Button frame
        button_frame = tk.Frame(self.root, bg=self.bg_color)
        button_frame.pack(fill="x", padx=20, pady=(10, 20))
        
        self.cancel_button = ttk.Button(button_frame, text="Cancel", 
                                       style="Secondary.TButton",
                                       command=self.cancel_uninstall)
        self.cancel_button.pack(side="left")
        
        self.uninstall_button = ttk.Button(button_frame, text="Uninstall", 
                                          style="Danger.TButton",
                                          command=self.start_uninstall)
        self.uninstall_button.pack(side="right")
        
    def cancel_uninstall(self):
        """Cancel and close the uninstaller"""
        if messagebox.askyesno("Confirm Exit", "Are you sure you want to cancel the uninstallation?"):
            self.root.quit()
            
    def start_uninstall(self):
        """Start the uninstallation process"""
        # Confirm with user
        if not messagebox.askyesno("Confirm Uninstallation", 
                                   "This will permanently remove the AutomataNexus Vibration Monitor.\n\n" +
                                   "Are you absolutely sure you want to continue?",
                                   icon='warning'):
            return
        
        # Hide components frame and show progress
        for widget in self.root.winfo_children():
            if isinstance(widget, tk.Frame) and widget != self.progress_frame:
                if "Components to Remove" in [w.cget("text") for w in widget.winfo_children() if isinstance(w, tk.Label)]:
                    widget.pack_forget()
        
        self.progress_frame.pack(fill="both", expand=True, padx=20, pady=10)
        self.uninstall_button.configure(state='disabled')
        self.cancel_button.configure(state='disabled')
        
        # Start uninstallation in background thread
        thread = threading.Thread(target=self.run_uninstallation)
        thread.daemon = True
        thread.start()
        
    def run_uninstallation(self):
        """Run the actual uninstallation process"""
        steps = []
        
        # Build steps based on selections
        if self.remove_service.get():
            steps.append(("Stopping service", self.stop_service))
        if self.remove_files.get():
            steps.append(("Removing application files", self.remove_app_files))
        if self.remove_config.get():
            steps.append(("Removing configuration", self.remove_configuration))
        if self.remove_database.get():
            steps.append(("Removing database", self.remove_database_files))
        if self.remove_nodered.get():
            steps.append(("Uninstalling Node-RED package", self.remove_nodered_package))
        if self.remove_desktop.get():
            steps.append(("Removing shortcuts", self.remove_shortcuts))
        if self.remove_logs.get():
            steps.append(("Cleaning up logs", self.remove_log_files))
        
        total_steps = len(steps)
        
        for i, (description, func) in enumerate(steps):
            # Update UI
            self.root.after(0, self.update_progress, description, (i / total_steps) * 100)
            
            # Run the step
            success = func()
            
            if not success:
                self.root.after(0, self.uninstall_failed, description)
                return
            
            time.sleep(0.5)  # Brief pause for visibility
        
        # Final step
        self.root.after(0, self.update_progress, "Uninstallation complete", 100)
        time.sleep(1)
        self.root.after(0, self.uninstall_complete)
        
    def update_progress(self, status, percent):
        """Update progress bar and status"""
        self.status_label.configure(text=status)
        self.progress['value'] = percent
        
    def stop_service(self):
        """Stop and disable the service"""
        try:
            subprocess.run(['sudo', 'systemctl', 'stop', 'vibration-monitor'], 
                         check=False, capture_output=True)
            subprocess.run(['sudo', 'systemctl', 'disable', 'vibration-monitor'], 
                         check=False, capture_output=True)
            return True
        except:
            return True  # Continue even if service doesn't exist
            
    def remove_app_files(self):
        """Remove application files"""
        try:
            subprocess.run(['sudo', 'rm', '-rf', '/opt/automatanexus-vibration-monitor'], 
                         check=False, capture_output=True)
            return True
        except:
            return False
            
    def remove_configuration(self):
        """Remove configuration files"""
        try:
            home = os.path.expanduser("~")
            config_file = os.path.join(home, '.vibration_monitor_config.json')
            if os.path.exists(config_file):
                os.remove(config_file)
            
            # Remove systemd service file
            subprocess.run(['sudo', 'rm', '-f', '/etc/systemd/system/vibration-monitor.service'], 
                         check=False, capture_output=True)
            subprocess.run(['sudo', 'systemctl', 'daemon-reload'], 
                         check=False, capture_output=True)
            return True
        except:
            return False
            
    def remove_database_files(self):
        """Remove database files"""
        try:
            home = os.path.expanduser("~")
            db_locations = [
                os.path.join(home, 'vibration_monitor.db'),
                '/opt/automatanexus-vibration-monitor/vibration_monitor.db'
            ]
            
            for db_file in db_locations:
                if os.path.exists(db_file):
                    if db_file.startswith('/opt'):
                        subprocess.run(['sudo', 'rm', '-f', db_file], 
                                     check=False, capture_output=True)
                    else:
                        os.remove(db_file)
            return True
        except:
            return False
            
    def remove_nodered_package(self):
        """Remove Node-RED package"""
        try:
            # Check global installation
            result = subprocess.run(['npm', 'list', '-g', 'node-red-contrib-automatanexus-hvac-vibration'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                subprocess.run(['sudo', 'npm', 'uninstall', '-g', 
                              'node-red-contrib-automatanexus-hvac-vibration'], 
                              check=False, capture_output=True)
            
            # Check local installation
            home = os.path.expanduser("~")
            nodered_dir = os.path.join(home, '.node-red')
            if os.path.exists(nodered_dir):
                os.chdir(nodered_dir)
                result = subprocess.run(['npm', 'list', 'node-red-contrib-automatanexus-hvac-vibration'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    subprocess.run(['npm', 'uninstall', 
                                  'node-red-contrib-automatanexus-hvac-vibration'], 
                                  check=False, capture_output=True)
            return True
        except:
            return True  # Continue if npm not available
            
    def remove_shortcuts(self):
        """Remove desktop shortcuts"""
        try:
            home = os.path.expanduser("~")
            shortcuts = [
                os.path.join(home, 'Desktop', 'vibration-monitor.desktop'),
                os.path.join(home, '.local', 'share', 'applications', 'vibration-monitor.desktop')
            ]
            
            for shortcut in shortcuts:
                if os.path.exists(shortcut):
                    os.remove(shortcut)
            return True
        except:
            return False
            
    def remove_log_files(self):
        """Remove log files"""
        try:
            subprocess.run(['sudo', 'rm', '-rf', '/var/log/vibration-monitor'], 
                         check=False, capture_output=True)
            
            home = os.path.expanduser("~")
            log_file = os.path.join(home, 'vibration_monitor.log')
            if os.path.exists(log_file):
                os.remove(log_file)
            return True
        except:
            return False
            
    def uninstall_failed(self, step):
        """Handle uninstallation failure"""
        self.detail_label.configure(text=f"Failed at: {step}", fg=self.danger_color)
        messagebox.showerror("Uninstallation Failed", 
                           f"The uninstallation failed during:\n{step}\n\n" +
                           "Some components may have been removed. Please check manually.")
        self.cancel_button.configure(state='normal', text="Close")
        
    def uninstall_complete(self):
        """Handle successful uninstallation"""
        self.status_label.configure(text="✓ Uninstallation Complete!", fg="#059669")
        self.detail_label.configure(text="All selected components have been removed.", fg="#059669")
        
        messagebox.showinfo("Uninstallation Complete", 
                          "AutomataNexus Vibration Monitor has been successfully uninstalled.\n\n" +
                          "To reinstall:\n" +
                          "git clone https://github.com/AutomataControls/IS0-10816-Vibration-Sensor.git\n" +
                          "cd IS0-10816-Vibration-Sensor\n" +
                          "./install.sh")
        
        self.root.quit()

def main():
    """Main entry point"""
    # Check if running as root
    if os.geteuid() == 0:
        print("Please run this uninstaller as a regular user, not as root.")
        sys.exit(1)
    
    root = tk.Tk()
    app = UninstallerWindow(root)
    root.mainloop()

if __name__ == "__main__":
    main()