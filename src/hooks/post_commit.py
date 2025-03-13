#!/usr/bin/env python3
"""Post-commit hook script to generate HTML report from commit metadata."""

import os
import sys
import json
from pathlib import Path
from commit_scripts.secretscan import generate_html_report

def get_script_dir():
    """Get the directory where this script is located."""
    return Path(__file__).parent

def main():
    try:
        # Get the hooks directory
        hooks_dir = get_script_dir()
        
        # Define paths
        metadata_file = hooks_dir / ".commit_metadata.json"
        reports_dir = hooks_dir / ".commit-reports"
                
        # Create reports directory if it doesn't exist
        reports_dir.mkdir(exist_ok=True)
        
        # Check if metadata file exists
        if not metadata_file.exists():
            print("No commit metadata found.")
            sys.exit(0)
        
        # Read metadata
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error parsing metadata file: {e}", file=sys.stderr)
            sys.exit(1)
        
        # Generate HTML report
        output_path = reports_dir / "commit-scan-report.html"
        
        # Pass the correct metadata parameters
        generate_html_report(
            str(output_path),
            results_data=metadata.get('secrets_found', []),
            has_secrets=metadata.get('has_secrets', False),
            secrets_list=metadata.get('secrets_found', []),
            has_disallowed_files=metadata.get('has_disallowed_files', False),
            disallowed_files=metadata.get('disallowed_files', [])
        )
        
        # Clean up metadata file
        try:
            metadata_file.unlink()
            print(f"Metadata file removed: {metadata_file}")
        except Exception as e:
            print(f"Warning: Failed to remove metadata file: {e}", file=sys.stderr)
        
    except Exception as e:
        print(f"Error in post-commit hook: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main() 