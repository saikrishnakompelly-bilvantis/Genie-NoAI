#!/usr/bin/env python3
"""Configuration module for Genie's secret scanning."""

import os
import json
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
import datetime

# Configuration constants
CONFIG_FILENAME = ".genie_scan_config.json"
DEFAULT_CONFIG = {
    "scan_mode": "both",  # Options: "diff", "repo", "both"
    "last_updated": None
}

def get_config_path():
    """Get the path to the configuration file."""
    home_dir = os.path.expanduser('~')
    genie_dir = os.path.join(home_dir, '.genie')
    return os.path.join(genie_dir, CONFIG_FILENAME)

def load_config():
    """Load configuration from file or use defaults."""
    config_path = get_config_path()
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            # Ensure all required fields exist
            for key, value in DEFAULT_CONFIG.items():
                if key not in config:
                    config[key] = value
            return config
        except Exception:
            pass
    
    # If we reached here, either the file doesn't exist or there was an error
    return DEFAULT_CONFIG.copy()

def save_config(config):
    """Save configuration to file."""
    # Update last modified time
    config["last_updated"] = datetime.datetime.now().isoformat()
    
    config_path = get_config_path()
    config_dir = os.path.dirname(config_path)
    
    # Create directory if it doesn't exist
    if not os.path.exists(config_dir):
        os.makedirs(config_dir, exist_ok=True)
    
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception:
        return False

def get_scan_mode():
    """Get the current scan mode."""
    config = load_config()
    return config.get("scan_mode", "both")

def should_scan_diff():
    """Check if diff scanning is enabled."""
    mode = get_scan_mode()
    return mode in ["diff", "both"]

def should_scan_repo():
    """Check if repository scanning is enabled."""
    mode = get_scan_mode()
    return mode in ["repo", "both"]

class ScanConfigUI:
    """UI for configuring scan options."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Genie - Scan Configuration")
        self.root.geometry("500x400")
        self.root.resizable(True, True)
        
        # Center the window
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        center_x = int(screen_width/2 - 500/2)
        center_y = int(screen_height/2 - 400/2)
        self.root.geometry(f'+{center_x}+{center_y}')
        
        # Create frame
        self.main_frame = ttk.Frame(self.root, padding="20")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Add header
        header_label = ttk.Label(
            self.main_frame,
            text="Genie Scan Configuration",
            font=('Helvetica', 16, 'bold')
        )
        header_label.pack(pady=(0, 20))
        
        # Add description
        description = ttk.Label(
            self.main_frame,
            text="Select which scanning mode you want to use.\nThis affects how scans are performed during Git pushes.",
            justify=tk.CENTER,
            wraplength=400
        )
        description.pack(pady=(0, 20))
        
        # Load current configuration
        self.config = load_config()
        self.scan_mode = tk.StringVar(value=self.config.get("scan_mode", "both"))
        
        # Current configuration display
        current_config_frame = ttk.LabelFrame(self.main_frame, text="Current Configuration", padding="10")
        current_config_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.current_config_label = ttk.Label(
            current_config_frame,
            text=self.get_config_description(),
            wraplength=400
        )
        self.current_config_label.pack(anchor=tk.W, pady=5)
        
        # Radio buttons for scan mode
        scan_mode_frame = ttk.LabelFrame(self.main_frame, text="Scan Mode", padding="10")
        scan_mode_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Both option
        both_radio = ttk.Radiobutton(
            scan_mode_frame,
            text="Scan Both (Default)",
            value="both",
            variable=self.scan_mode
        )
        both_radio.pack(anchor=tk.W, pady=5)
        both_desc = ttk.Label(
            scan_mode_frame,
            text="Scan both the changes to be pushed and the entire repository",
            wraplength=400,
            foreground="gray"
        )
        both_desc.pack(anchor=tk.W, padx=(20, 0), pady=(0, 10))
        
        # Diff only option
        diff_radio = ttk.Radiobutton(
            scan_mode_frame,
            text="Scan Diff Only",
            value="diff",
            variable=self.scan_mode
        )
        diff_radio.pack(anchor=tk.W, pady=5)
        diff_desc = ttk.Label(
            scan_mode_frame,
            text="Only scan the changes to be pushed (faster)",
            wraplength=400,
            foreground="gray"
        )
        diff_desc.pack(anchor=tk.W, padx=(20, 0), pady=(0, 10))
        
        # Repo only option
        repo_radio = ttk.Radiobutton(
            scan_mode_frame,
            text="Scan Repository Only",
            value="repo",
            variable=self.scan_mode
        )
        repo_radio.pack(anchor=tk.W, pady=5)
        repo_desc = ttk.Label(
            scan_mode_frame,
            text="Only scan the entire repository (more comprehensive)",
            wraplength=400,
            foreground="gray"
        )
        repo_desc.pack(anchor=tk.W, padx=(20, 0), pady=(0, 10))
        
        # Button frame
        button_frame = ttk.Frame(self.main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        # Save and Exit button
        save_exit_button = ttk.Button(
            button_frame,
            text="Save and Exit",
            command=self.save_and_exit
        )
        save_exit_button.pack(side=tk.RIGHT, padx=5)
        
        # Cancel button
        cancel_button = ttk.Button(
            button_frame,
            text="Cancel",
            command=self.root.destroy
        )
        cancel_button.pack(side=tk.RIGHT, padx=5)
        
        # Status label
        self.status_label = ttk.Label(
            self.main_frame,
            text="",
            foreground="blue"
        )
        self.status_label.pack(pady=(10, 0))
    
    def get_config_description(self):
        """Get human-readable description of the current configuration."""
        mode = self.config.get("scan_mode", "both")
        
        if mode == "both":
            return "Currently scanning both changed files and the entire repository."
        elif mode == "diff":
            return "Currently scanning only changed files (diff mode)."
        elif mode == "repo":
            return "Currently scanning only the entire repository."
        else:
            return f"Unknown scan mode: {mode}"
    
    def show_config_confirmation(self):
        """Show a confirmation dialog with the updated configuration."""
        mode = self.scan_mode.get()
        
        if mode == "both":
            message = "Configuration saved successfully!\n\nNow scanning both changed files and the entire repository."
        elif mode == "diff":
            message = "Configuration saved successfully!\n\nNow scanning only changed files (diff mode)."
        elif mode == "repo":
            message = "Configuration saved successfully!\n\nNow scanning only the entire repository."
        else:
            message = f"Configuration saved with scan mode: {mode}"
        
        messagebox.showinfo("Configuration Updated", message)
    
    def save_and_exit(self):
        """Save the current configuration and exit."""
        self.config["scan_mode"] = self.scan_mode.get()
        if save_config(self.config):
            # Update UI to reflect the change
            self.current_config_label.config(text=self.get_config_description())
            
            # Show confirmation with the updated config
            self.show_config_confirmation()
            
            # Close the window after showing the confirmation
            self.root.destroy()
        else:
            messagebox.showerror("Error", "Failed to save configuration")
    
    def run(self):
        """Run the configuration UI."""
        self.root.mainloop()

def main():
    """Main entry point when run as a script."""
    ui = ScanConfigUI()
    ui.run()

if __name__ == "__main__":
    main() 