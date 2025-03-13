#!/usr/bin/env python3
"""Script to scan repository for secrets and display HTML report."""

import os
import sys
import json
import webbrowser
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import platform

# Add the hooks directory to Python path
SCRIPT_DIR = Path(__file__).parent
sys.path.append(str(SCRIPT_DIR))

from commit_scripts.secretscan import SecretScanner, generate_html_report

def is_binary_file(file_path):
    """Check if a file is binary using git check-attr."""
    try:
        # Use forward slashes for Git commands even on Windows
        git_path = str(file_path).replace('\\', '/')
        result = subprocess.run(
            ['git', 'check-attr', '-z', 'text', git_path],
            capture_output=True,
            text=True
        )
        # If the file is marked as text, it's not binary
        return 'text: unset' in result.stdout
    except subprocess.CalledProcessError:
        # If git check-attr fails, try using file command
        try:
            # On Windows, use 'file' command from Git Bash if available
            if platform.system() == 'Windows':
                file_cmd = ['file', '--mime-type', str(file_path)]
            else:
                file_cmd = ['file', '--mime-type', str(file_path)]
                
            result = subprocess.run(
                file_cmd,
                capture_output=True,
                text=True
            )
            # Skip files that are not text/plain
            return not result.stdout.strip().endswith('text/plain')
        except subprocess.CalledProcessError:
            # If both checks fail, assume it's binary to be safe
            return True

def get_all_files():
    """Get all files in the repository."""
    try:
        result = subprocess.run(['git', 'ls-files'],
                              check=True, capture_output=True, text=True)
        return result.stdout.strip().split('\n')
    except subprocess.CalledProcessError:
        return []

def check_disallowed_files(files):
    """Check for disallowed file extensions."""
    DISALLOWED_EXTENSIONS = {'.crt', '.cer', '.ca-bundle', '.p7b', '.p7c', 
                           '.p7s', '.pem', '.jceks', '.key', '.keystore', 
                           '.jks', '.p12', '.pfx'}
    
    disallowed_files = []
    for file in files:
        if any(file.lower().endswith(ext) for ext in DISALLOWED_EXTENSIONS):
            disallowed_files.append(file)
    return disallowed_files

def scan_repository():
    """Scan the entire repository for secrets."""
    scanner = SecretScanner()
    all_files = get_all_files()
    all_results = []
    skipped_files = []
    
    for file in all_files:
        try:
            if is_binary_file(file):
                skipped_files.append(file)
                continue
                
            results = scanner.scan_file(file)
            all_results.extend(results)
        except Exception as e:
            print(f"Warning: Error scanning file {file}: {str(e)}", file=sys.stderr)
    
    if skipped_files:
        print(f"\nSkipped {len(skipped_files)} binary files:", file=sys.stderr)
        for file in skipped_files:
            print(f"  - {file}", file=sys.stderr)
    
    return all_results

def main():
    try:
        # Create reports directory if it doesn't exist
        reports_dir = SCRIPT_DIR / ".commit-reports"
        reports_dir.mkdir(exist_ok=True)
        
        # Get all files and check for disallowed files
        all_files = get_all_files()
        disallowed_files = check_disallowed_files(all_files)
        
        # Scan repository for secrets
        secrets_data = scan_repository()
        
        # Generate HTML report
        output_path = reports_dir / "repository-scan-report.html"
        generate_html_report(
            str(output_path),
            results_data=secrets_data,
            has_secrets=bool(secrets_data),
            secrets_list=secrets_data,
            has_disallowed_files=bool(disallowed_files),
            disallowed_files=disallowed_files
        )
        
        # Open HTML report in default browser if issues found
        if secrets_data or disallowed_files:
            # Use file:// protocol with forward slashes
            file_url = 'file://' + str(output_path.absolute()).replace('\\', '/')
            webbrowser.open(file_url)
        
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
