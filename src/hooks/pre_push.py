#!/usr/bin/env python3
import os
import sys
import json
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
import logging
from typing import List, Dict, Any
 
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
 
# Add the hooks directory to Python path
SCRIPT_DIR = Path(__file__).parent
sys.path.append(str(SCRIPT_DIR))
 
from commit_scripts.secretscan import SecretScanner
from commit_scripts.utils import mask_secret
 
def get_script_dir():
    """Get the directory where this script is located."""
    return SCRIPT_DIR
 
def check_python():
    """Check if Python is available."""
    if sys.version_info[0] < 3:
        print("WARNING: Python3 is not installed. Push review functionality will not work.")
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

def get_files_to_push():
    """Get list of files about to be pushed."""
    try:
        logging.info("Getting files to be pushed...")
        # Get the files that have been changed in commits that will be pushed
        result = subprocess.run(
            ['git', 'diff', '--name-only', '@{u}..'],
            check=True,
            capture_output=True,
            text=True
        )
        files = [f for f in result.stdout.strip().split('\n') if f]
        
        # If no files found from the above command (maybe first push), get all tracked files
        if not files:
            logging.info("No upstream found, checking all staged and committed files")
            result = subprocess.run(
                ['git', 'ls-files'],
                check=True,
                capture_output=True,
                text=True
            )
            files = [f for f in result.stdout.strip().split('\n') if f]
            
        logging.info(f"Found {len(files)} files to be pushed")
        return files
    except subprocess.CalledProcessError as e:
        logging.error(f"Error getting files to push: {e}")
        return []
 
def run_secret_scan():
    """Run the secret scanning script."""
    try:
        logging.info("Initializing secret scanner...")
        scanner = SecretScanner()
        
        logging.info("Scanning files to be pushed...")
        results = scanner.scan_files(get_files_to_push())
        
        logging.info(f"Found {len(results)} potential secrets")
        return results
    except Exception as e:
        logging.error(f"Secret scan failed: {str(e)}")
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
 
class ValidationWindow:
    def __init__(self):
        self.results = {
            "secrets": {"proceed": False, "messages": {}, "global_message": ""}
        }
        self.windows = []
        self.ITEMS_PER_PAGE = 50  # Number of items to show per page
        self.current_page = 1
        self.justification_entries = []
        
    # Rest of the ValidationWindow class implementation
    # ...

def save_metadata(validation_results, secrets_data):
    """Save metadata for post-push processing."""
    try:
        metadata = {
            "validation_results": validation_results,
            "secrets_found": secrets_data
        }
        
        metadata_file = Path(get_script_dir()) / ".push_metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        logging.info(f"Metadata saved to {metadata_file}")
    except Exception as e:
        logging.error(f"Error saving metadata: {e}")

def append_validation_messages():
    """Append validation messages if needed."""
    # Implementation for push validation messages
    # (This could be simplified for push hooks since we don't need to modify the commit message)
    pass

def main():
    try:
        logging.info("Starting pre-push hook")
        check_python()
        check_git()
        
        files_to_push = get_files_to_push()
        if not files_to_push:
            logging.info("No files to push")
            show_message_box("No files to push.")
            sys.exit(0)
        
        logging.info("Running secret scan...")
        secrets_data = run_secret_scan()
        
        if secrets_data:
            logging.info("Showing validation window...")
            validation = ValidationWindow()
            if not validation.run_validation(secrets_data):
                logging.info("Validation failed or was aborted")
                sys.exit(1)
            
            logging.info("Saving metadata...")
            save_metadata(validation.results, secrets_data)
            logging.info("Appending validation messages...")
            append_validation_messages()
        else:
            logging.info("No issues found, saving empty metadata")
            save_metadata({}, [])
        
        logging.info("Pre-push hook completed successfully")
            
    except Exception as e:
        logging.error(f"Error in pre-push hook: {str(e)}", exc_info=True)
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main() 