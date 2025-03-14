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
 
class ValidationWindow:
    def __init__(self):
        self.results = {
            "secrets": {"proceed": False, "messages": {}, "global_message": ""},
            "disallowed": {"proceed": False, "messages": {}, "global_message": ""}
        }
        self.windows = []
 
    def create_items_list(self, parent, items, item_type):
        """Create a list view of all items."""
        frame = ttk.Frame(parent, padding="10", relief="solid", borderwidth=1)
        frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
 
        # Create a canvas with scrollbar for the items
        canvas = tk.Canvas(frame)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        items_frame = ttk.Frame(canvas)
 
        canvas.configure(yscrollcommand=scrollbar.set)
 
        # Pack scrollbar and canvas
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
 
        # Create window inside canvas
        canvas.create_window((0, 0), window=items_frame, anchor="nw")
 
        # Configure canvas scrolling
        def configure_scroll_region(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        items_frame.bind("<Configure>", configure_scroll_region)
 
        # Add items
        for item in items:
            item_frame = ttk.Frame(items_frame)
            item_frame.pack(fill=tk.X, pady=2)
 
            if item_type == "secret":
                ttk.Label(item_frame, text=f"File: {item['file']}", font=('Helvetica', 10, 'bold')).pack(anchor=tk.W)
                ttk.Label(item_frame, text=f"Line {item['line_number']}: {item['line']}", wraplength=700).pack(anchor=tk.W)
            else:  # disallowed file
                ttk.Label(item_frame, text=f"File: {item}", font=('Helvetica', 10, 'bold')).pack(anchor=tk.W)
            ttk.Separator(items_frame, orient='horizontal').pack(fill=tk.X, pady=5)
 
        return frame
 
    def show_validation_window(self, title, items, item_type):
        """Show validation window for either secrets or disallowed files."""
        if not items:
            return True
 
        root = create_window(title)
        self.windows.append(root)
 
        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
 
        # Header
        warning_text = "⚠️ Potential secrets detected!" if item_type == "secret" else "⚠️ Disallowed files detected!"
        ttk.Label(
            main_frame,
            text=warning_text,
            font=('Helvetica', 14, 'bold'),
            foreground='red'
        ).pack(pady=(0, 10))
 
        # Create items list
        self.create_items_list(main_frame, items, item_type)
 
        # Classification frame
        class_frame = ttk.LabelFrame(main_frame, text="Classification", padding="10")
        class_frame.pack(fill=tk.X, pady=(10, 0), padx=5)
 
        # Global message frame (visible by default for True Positive)
        global_msg_frame = ttk.LabelFrame(main_frame, text="Justification Message (required for True Positive)", padding="10")
        global_msg_frame.pack(fill=tk.X, pady=(10, 0), padx=5)
        
        global_msg_entry = ttk.Entry(global_msg_frame)
        global_msg_entry.pack(fill=tk.X, expand=True)
 
        classification_var = tk.StringVar(value="true_positive")  # Default to True Positive
        
        def on_classification_change(*args):
            # Show/hide message entry based on classification
            if classification_var.get() == "true_positive":
                # Ensure message frame is packed before buttons
                global_msg_frame.pack(fill=tk.X, pady=(10, 0), padx=5, before=button_frame)
            else:
                global_msg_frame.pack_forget()
                global_msg_entry.delete(0, tk.END)
 
        ttk.Radiobutton(class_frame, text="True Positive", variable=classification_var,
                       value="true_positive", command=on_classification_change).pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(class_frame, text="False Positive", variable=classification_var,
                       value="false_positive", command=on_classification_change).pack(side=tk.LEFT, padx=10)
 
        # Buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
 
        def on_proceed():
            classification = classification_var.get()
            
            # If true positive, require a message
            if classification == "true_positive" and not global_msg_entry.get().strip():
                messagebox.showerror(
                    "Validation Error",
                    "Please provide a justification message for the True Positive items."
                )
                return
            
            # Collect results
            self.results[item_type] = {
                "proceed": True,
                "messages": {
                    item['file'] if item_type == "secret" else item: {"classification": classification}
                    for item in items
                },
                "global_message": global_msg_entry.get().strip() if classification == "true_positive" else ""
            }
            root.quit()
 
        def on_abort():
            # Reset results for this type
            self.results[item_type] = {"proceed": False, "messages": {}, "global_message": ""}
            root.quit()
 
        ttk.Button(button_frame, text="Abort Commit", command=on_abort).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Proceed", command=on_proceed).pack(side=tk.LEFT, padx=5)
 
        # Handle window close button (X)
        def on_window_close():
            on_abort()  # Use the same abort logic
            root.destroy()
 
        root.protocol("WM_DELETE_WINDOW", on_window_close)
        root.mainloop()
 
        # Clean up the window
        if root in self.windows:
            self.windows.remove(root)
        root.destroy()
 
        return self.results[item_type]["proceed"]
 
    def show_abort_window(self):
        """Show the abort window."""
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
 
    def run_validation(self, secrets_data, disallowed_data):
        """Run the validation process for both secrets and disallowed files."""
        # Reset results at the start of validation
        self.results = {
            "secrets": {"proceed": False, "messages": {}, "global_message": ""},
            "disallowed": {"proceed": False, "messages": {}, "global_message": ""}
        }
 
        if secrets_data:
            proceed = self.show_validation_window(
                "Secrets Found - Genie GitHooks",
                secrets_data,
                "secret"
            )
            if not proceed:
                self.show_abort_window()
                return False
 
        if disallowed_data:
            proceed = self.show_validation_window(
                "Disallowed Files - Genie GitHooks",
                disallowed_data,
                "disallowed"
            )
            if not proceed:
                self.show_abort_window()
                return False
 
        return True
 
def save_metadata(validation_results, secrets_data, disallowed_files):
    """Save commit metadata for post-commit hook."""
    script_dir = get_script_dir()
    metadata_file = script_dir / ".commit_metadata.json"
    
    try:
        metadata = {
            "validation_results": validation_results,
            "secrets_found": secrets_data,
            "disallowed_files": disallowed_files
        }
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
 
    except Exception as e:
        print(f"Warning: Failed to save metadata: {str(e)}", file=sys.stderr)
 
def append_validation_messages():
    """Append validation messages to the commit message."""
    try:
        script_dir = get_script_dir()
        metadata_file = script_dir / ".commit_metadata.json"
        
        if not metadata_file.exists():
            return
            
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
            
        validation_results = metadata.get("validation_results", {})
        
        # Collect messages for true positives
        messages = []
        for result_type in ["secrets", "disallowed"]:
            result_data = validation_results.get(result_type, {})
            type_messages = result_data.get("messages", {})
            global_message = result_data.get("global_message", "")
            
            # If there are any true positives and a global message
            true_positives = [item for item, data in type_messages.items()
                            if data.get("classification") == "true_positive"]
            
            if true_positives and global_message:
                items_list = ", ".join(true_positives)
                messages.append(f"[{result_type.upper()}] {items_list}: {global_message}")
        
        if messages:
            # Read current commit message
            commit_msg_file = Path(sys.argv[1])
            with open(commit_msg_file, 'r') as f:
                current_msg = f.read()
            
            # Append validation messages
            with open(commit_msg_file, 'w') as f:
                f.write(current_msg.rstrip() + "\n\n" + "\n".join(messages))
                
    except Exception as e:
        print(f"Warning: Failed to append validation messages: {str(e)}", file=sys.stderr)
 
def main():
    try:
        check_python()
        check_git()
        
        staged_files = get_staged_files()
        if not staged_files:
            show_message_box("No files staged for commit.")
            sys.exit(0)
        
        disallowed_files = check_disallowed_files(staged_files)
        secrets_data = run_secret_scan()
        
        if secrets_data or disallowed_files:
            validation = ValidationWindow()
            if not validation.run_validation(secrets_data, disallowed_files):
                sys.exit(1)
                
            save_metadata(validation.results, secrets_data, disallowed_files)
            append_validation_messages()
        else:
            save_metadata({}, [], [])
            
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)
 
if __name__ == "__main__":
    main()