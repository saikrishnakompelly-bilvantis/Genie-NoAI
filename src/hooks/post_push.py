#!/usr/bin/env python3
"""Post-push hook script to scan repository and generate HTML report."""

import os
import sys
import json
import subprocess
from pathlib import Path
import logging
import time

from commit_scripts.secretscan import SecretScanner, generate_html_report

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Create a marker file to prevent recursive triggering
MARKER_FILE = Path(__file__).parent / ".post_push_running"

def get_script_dir():
    """Get the directory where this script is located."""
    return Path(__file__).parent

def main():
    try:
        # Check if we're in a recursive call and exit if so
        if MARKER_FILE.exists():
            logging.info("Post-push hook already running, exiting to prevent recursion")
            return
            
        logging.info("Starting post-push hook")
        
        # Get the hooks directory
        hooks_dir = get_script_dir()
        
        # Define paths
        metadata_file = hooks_dir / ".push_metadata.json"
        reports_dir = hooks_dir / ".push-reports"
                
        # Create reports directory if it doesn't exist
        reports_dir.mkdir(exist_ok=True)
        
        # Initialize scanner
        logging.info("Initializing SecretScanner")
        scanner = SecretScanner()
        
        # Read metadata if it exists
        push_secrets = []
        validation_results = {}
        
        if metadata_file.exists():
            try:
                logging.info("Reading metadata from pre-push hook")
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    push_secrets = metadata.get('secrets_found', [])
                    validation_results = metadata.get('validation_results', {})
                    logging.info(f"Found {len(push_secrets)} secrets from pushed files")
            except json.JSONDecodeError as e:
                logging.error(f"Error parsing metadata file: {e}")
        else:
            logging.info("No metadata file found from pre-push hook")
        
        # Perform repository scan
        logging.info("Scanning entire repository for secrets")
        repo_secrets = scanner.scan_repository()
        logging.info(f"Found {len(repo_secrets)} secrets in repository scan")
        
        # Deduplicate secrets
        already_seen = set()
        unique_push_secrets = []
        
        for secret in push_secrets:
            key = (secret.get('file_path', ''), secret.get('line_number', ''))
            if key not in already_seen:
                already_seen.add(key)
                unique_push_secrets.append(secret)
        
        # For repository scan view, include all secrets (push + repo)
        all_secrets_for_repo_view = unique_push_secrets.copy()
        
        # Add repo secrets that aren't already in the push scan
        for secret in repo_secrets:
            key = (secret.get('file_path', ''), secret.get('line_number', ''))
            if key not in already_seen:
                already_seen.add(key)
                all_secrets_for_repo_view.append(secret)
        
        # Set push secrets to the unique list
        push_secrets = unique_push_secrets
        
        # Generate HTML reports
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        
        if push_secrets:
            # Report for secrets detected in the files that were just pushed
            push_report_path = reports_dir / f"push-secrets-{timestamp}.html"
            generate_html_report(push_secrets, push_report_path, "Secrets in Pushed Files", validation_results)
            logging.info(f"Generated push secrets report at {push_report_path}")
            open_html_report(push_report_path)
            
        # Repository-wide report
        if all_secrets_for_repo_view:
            repo_report_path = reports_dir / f"repo-scan-{timestamp}.html"
            generate_html_report(all_secrets_for_repo_view, repo_report_path, "Repository Scan", validation_results)
            logging.info(f"Generated repository secrets report at {repo_report_path}")
            
            # Only open this if we didn't open the push report
            if not push_secrets:
                open_html_report(repo_report_path)
                
        # Delete the metadata file to avoid reusing it
        if metadata_file.exists():
            metadata_file.unlink()
            logging.info("Deleted metadata file")
                
        logging.info("Post-push hook completed successfully")
        
    except Exception as e:
        logging.error(f"Error in post-push hook: {str(e)}", exc_info=True)
    finally:
        # Remove the marker file if it exists
        if MARKER_FILE.exists():
            MARKER_FILE.unlink()

def open_html_report(file_path):
    """Safely open HTML report in browser."""
    try:
        # Ensure the file exists
        if not os.path.isfile(file_path):
            logging.error(f"HTML report file not found at {file_path}")
            return False
            
        # Get the absolute file path
        abs_path = os.path.abspath(file_path)
        
        # Construct proper file URI
        file_uri = f"file://{abs_path}"
        
        # Log the path being opened
        logging.info(f"Opening HTML report at: {file_uri}")
        
        # Try to open the browser
        import webbrowser
        # Allow a small delay to ensure file is fully written
        time.sleep(0.5)
        success = webbrowser.open(file_uri)
        
        if success:
            logging.info("Browser opened successfully")
        else:
            logging.error("Failed to open browser")
            
        return success
    except Exception as e:
        logging.error(f"Error opening HTML report: {e}")
        return False

if __name__ == "__main__":
    main() 