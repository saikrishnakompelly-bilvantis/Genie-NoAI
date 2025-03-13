#!/usr/bin/env python3
import os
import sys
import json
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

# Add the hooks directory to Python path
SCRIPT_DIR = Path(__file__).parent
sys.path.append(str(SCRIPT_DIR))

from commit_scripts.secretscan import SecretScanner

def get_script_dir():
    """Get the directory where this script is located."""
    return SCRIPT_DIR

def check_python():
    """Check if Python is available."""
    if sys.version_info[0] < 3:
        print("WARNING: Python3 is not installed. Commit review functionality will not work.")
        sys.exit(1)

def check_git():
    """Check if Git is installed and configured."""
    try:
        subprocess.run(['git', '--version'], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        show_message_box("Error: Git is not installed. Please install Git before proceeding.")
        sys.exit(1)

    # Check Git configuration
    try:
        username = subprocess.run(['git', 'config', '--global', 'user.name'], 
                                check=True, capture_output=True, text=True).stdout.strip()
        email = subprocess.run(['git', 'config', '--global', 'user.email'], 
                             check=True, capture_output=True, text=True).stdout.strip()
        
        if not username or not email:
            show_message_box('Error: Git global username and/or email is not set.\n'
                           'Please configure them using:\n'
                           'git config --global user.name "Your Name"\n'
                           'git config --global user.email "you@example.com"')
            sys.exit(1)
    except subprocess.CalledProcessError:
        show_message_box("Error: Git configuration check failed.")
        sys.exit(1)

def show_message_box(message):
    """Display a message box using Tkinter."""
    root = tk.Tk()
    root.withdraw()
    messagebox.showinfo("Genie GitHooks", message)
    root.destroy()

def get_user_confirmation(prompt):
    """Get user confirmation via Tkinter."""
    root = tk.Tk()
    root.withdraw()
    response = messagebox.askyesno("Genie GitHooks", prompt)
    root.destroy()
    return "Y" if response else "N"

def get_staged_files():
    """Get list of staged files."""
    try:
        result = subprocess.run(['git', 'diff', '--cached', '--name-only'],
                              check=True, capture_output=True, text=True)
        return result.stdout.strip().split('\n')
    except subprocess.CalledProcessError:
        return []

def check_disallowed_files(staged_files):
    """Check for disallowed file extensions."""
    DISALLOWED_EXTENSIONS = {'.crt', '.cer', '.ca-bundle', '.p7b', '.p7c', 
                           '.p7s', '.pem', '.jceks', '.key', '.keystore', 
                           '.jks', '.p12', '.pfx'}
    
    disallowed_files = []
    for file in staged_files:
        if any(file.lower().endswith(ext) for ext in DISALLOWED_EXTENSIONS):
            disallowed_files.append(file)
    return disallowed_files

def run_secret_scan():
    """Run the secret scanning script."""
    try:
        scanner = SecretScanner()
        results = scanner.scan_git_diff()
        return results
    except Exception as e:
        print(f"Warning: Secret scan failed: {str(e)}", file=sys.stderr)
        return []

def create_window(title, width=800, height=600):
    """Create a centered window."""
    window = tk.Tk()
    window.title(title)
    
    # Get screen dimensions
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    
    # Calculate center position
    center_x = int(screen_width/2 - width/2)
    center_y = int(screen_height/2 - height/2)
    
    # Set window geometry
    window.geometry(f'{width}x{height}+{center_x}+{center_y}')
    
    # Make window resizable
    window.resizable(True, True)
    
    # Set minimum size
    window.minsize(400, 300)
    
    return window

class ReviewWindow:
    def __init__(self):
        self.results = {"secrets": "N", "disallowed": "N"}
        self.windows = []

    def show_secrets_window(self, secrets_data):
        if not secrets_data:
            return
        
        root = create_window("Secrets Found - Genie GitHooks")
        self.windows.append(root)
        
        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        warning_label = ttk.Label(
            main_frame,
            text="⚠️ Potential secrets detected in your changes!",
            font=('Helvetica', 14, 'bold'),
            foreground='red'
        )
        warning_label.pack(pady=(0, 10))
        
        text_widget = tk.Text(main_frame, wrap=tk.WORD, width=80, height=20)
        text_widget.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        scrollbar = ttk.Scrollbar(text_widget, orient=tk.VERTICAL, command=text_widget.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        for item in secrets_data:
            text_widget.insert(tk.END, "━" * 50 + "\n")
            text_widget.insert(tk.END, f"File: {item['file']}\n")
            # text_widget.insert(tk.END, f"Pattern: {item['pattern']}\n")
            text_widget.insert(tk.END, f"Line {item['line_number']}: {item['line']}\n\n")
        
        text_widget.configure(state='disabled')
        
        caution_label = ttk.Label(
            main_frame,
            text="⚠️ Caution: These secrets will be committed if you proceed!",
            foreground='red'
        )
        caution_label.pack(pady=(0, 10))
        
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        def on_proceed():
            self.results["secrets"] = "Y"
            root.quit()
        
        def on_abort():
            self.results["secrets"] = "N"
            root.quit()
        
        abort_btn = ttk.Button(button_frame, text="Abort Commit", command=on_abort)
        abort_btn.pack(side=tk.LEFT, padx=5)
        
        proceed_btn = ttk.Button(button_frame, text="Proceed Anyway", command=on_proceed)
        proceed_btn.pack(side=tk.LEFT, padx=5)
        
        root.protocol("WM_DELETE_WINDOW", on_abort)
        return root

    def show_disallowed_files_window(self, disallowed_files):
        if not disallowed_files:
            return
        
        root = create_window("Disallowed Files - Genie GitHooks", width=600, height=400)
        self.windows.append(root)
        
        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        warning_label = ttk.Label(
            main_frame,
            text="⚠️ Disallowed file types detected!",
            font=('Helvetica', 14, 'bold'),
            foreground='red'
        )
        warning_label.pack(pady=(0, 10))
        
        text_widget = tk.Text(main_frame, wrap=tk.WORD, width=60, height=15)
        text_widget.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        scrollbar = ttk.Scrollbar(text_widget, orient=tk.VERTICAL, command=text_widget.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.insert(tk.END, "The following files have disallowed extensions:\n\n")
        for file in disallowed_files:
            text_widget.insert(tk.END, f"• {file}\n")
        
        text_widget.configure(state='disabled')
        
        caution_label = ttk.Label(
            main_frame,
            text="⚠️ Caution: These files will be committed if you proceed!",
            foreground='red'
        )
        caution_label.pack(pady=(0, 10))
        
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        def on_proceed():
            self.results["disallowed"] = "Y"
            root.quit()
        
        def on_abort():
            self.results["disallowed"] = "N"
            root.quit()
        
        abort_btn = ttk.Button(button_frame, text="Abort Commit", command=on_abort)
        abort_btn.pack(side=tk.LEFT, padx=5)
        
        proceed_btn = ttk.Button(button_frame, text="Proceed Anyway", command=on_proceed)
        proceed_btn.pack(side=tk.LEFT, padx=5)
        
        root.protocol("WM_DELETE_WINDOW", on_abort)
        return root

    def show_abort_window(self):
        root = create_window("Commit Aborted - Genie GitHooks", width=400, height=200)
        
        main_frame = ttk.Frame(root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        warning_label = ttk.Label(
            main_frame,
            text="⚠️ Commit Aborted",
            font=('Helvetica', 16, 'bold'),
            foreground='red'
        )
        warning_label.pack(pady=(0, 15))
        
        message_label = ttk.Label(
            main_frame,
            text="The commit has been aborted due to unresolved issues.\nPlease review and address the concerns before committing.",
            justify=tk.CENTER,
            wraplength=350
        )
        message_label.pack(pady=(0, 20))
        
        ok_button = ttk.Button(main_frame, text="OK", command=root.destroy)
        ok_button.pack()
        ok_button.pack_configure(anchor=tk.CENTER)
        
        root.protocol("WM_DELETE_WINDOW", root.destroy)
        root.transient()
        root.grab_set()
        root.wait_window()

    def run_windows(self, secrets_data, disallowed_data):
        if secrets_data:
            secrets_window = self.show_secrets_window(secrets_data)
            secrets_window.mainloop()
            secrets_window.destroy()
            
            if self.results["secrets"] != "Y":
                self.show_abort_window()
                return "N"
        
        if disallowed_data:
            disallowed_window = self.show_disallowed_files_window(disallowed_data)
            disallowed_window.mainloop()
            disallowed_window.destroy()
            
            if self.results["disallowed"] != "Y":
                self.show_abort_window()
                return "N"
            
            return "Y"
        
        result = "Y" if not secrets_data or self.results["secrets"] == "Y" else "N"
        if result == "N":
            self.show_abort_window()
        return result

def save_metadata(has_secrets, secrets_list, has_disallowed_files, disallowed_files):
    """Save commit metadata for post-commit hook."""
    script_dir = get_script_dir()
    metadata_file = script_dir / ".commit_metadata.json"
    
    try:
        metadata = {
            "has_secrets": has_secrets,
            "secrets_found": secrets_list,
            "has_disallowed_files": has_disallowed_files,
            "disallowed_files": disallowed_files
        }
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)

    except Exception as e:
        print(f"Warning: Failed to save metadata: {str(e)}", file=sys.stderr)

def main():
    try:
        check_python()
        check_git()
        
        staged_files = get_staged_files()
        if not staged_files:
            show_message_box("No files staged for commit.")
            sys.exit(0)
        
        disallowed_files = check_disallowed_files(staged_files)
        # print(f"Disallowed files: {disallowed_files}")
        secrets_data = run_secret_scan()
        # print(f"Secrets data: {secrets_data}")
        
        if secrets_data or disallowed_files:
            review = ReviewWindow()
            user_input = review.run_windows(secrets_data, disallowed_files)
            
            if user_input != "Y":
                sys.exit(1)
            
            save_metadata(
                has_secrets=bool(secrets_data),
                secrets_list=secrets_data,
                has_disallowed_files=bool(disallowed_files),
                disallowed_files=disallowed_files
            )
        else:
            save_metadata(
                has_secrets=False,
                secrets_list=[],
                has_disallowed_files=False,
                disallowed_files=[]
            )
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main() 