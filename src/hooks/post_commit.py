#!/usr/bin/env python3
"""Post-commit hook script to scan repository and generate HTML report."""

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
MARKER_FILE = Path(__file__).parent / ".post_commit_running"

def get_script_dir():
    """Get the directory where this script is located."""
    return Path(__file__).parent

def amend_commit_with_messages(validation_results):
    """Amend the current commit with validation messages if needed."""
    if not validation_results:
        return False
    
    # Collect messages for secrets
    messages = []
    result_data = validation_results.get("secrets", {})
    type_messages = result_data.get("messages", {})
    global_message = result_data.get("global_message", "")
    
    # If there are any reviewed items and a global message
    reviewed_items = [item for item, data in type_messages.items()
                    if data.get("classification") == "reviewed"]
    
    if reviewed_items and global_message:
        items_list = ", ".join(reviewed_items)
        messages.append(f"[SECRETS] {items_list}: {global_message}")
    
    if not messages:
        return False
    
    try:
        # Get the last commit message
        last_msg_cmd = ['git', 'log', '-1', '--pretty=%B']
        last_commit_msg = subprocess.check_output(last_msg_cmd, text=True).strip()
        
        # Check if validation messages are already in the commit message
        if any(msg in last_commit_msg for msg in messages):
            logging.info("Validation messages already in commit message")
            return False
        
        # Create marker file to prevent recursive post-commit hooks
        with open(MARKER_FILE, 'w') as f:
            f.write('running')
            
        # Amend the commit with the validation messages
        new_message = last_commit_msg + "\n\n" + "\n".join(messages)
        
        # Write to temporary file
        temp_msg_file = Path(get_script_dir()) / ".temp_commit_msg"
        with open(temp_msg_file, 'w') as f:
            f.write(new_message)
        
        # Amend commit with new message - use environment variables to disable hooks
        env = os.environ.copy()
        env['HUSKY_SKIP_HOOKS'] = '1'  # For husky
        env['SKIPALLHOOKS'] = '1'  # General hook skipping
        
        amend_cmd = ['git', 'commit', '--amend', '-F', str(temp_msg_file), '--no-verify']
        subprocess.run(amend_cmd, check=True, env=env)
        
        # Clean up temp file
        if temp_msg_file.exists():
            temp_msg_file.unlink()
        
        logging.info("Successfully amended commit with validation messages")
        return True
        
    except subprocess.CalledProcessError as e:
        logging.error(f"Error amending commit: {e}")
        return False
    except Exception as e:
        logging.error(f"Unexpected error amending commit: {e}")
        return False
    finally:
        # Remove the marker file
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

def main():
    try:
        # Check if we're in a recursive call and exit if so
        if MARKER_FILE.exists():
            logging.info("Post-commit hook already running, exiting to prevent recursion")
            return
            
        logging.info("Starting post-commit hook")
        
        # Get the hooks directory
        hooks_dir = get_script_dir()
        
        # Define paths
        metadata_file = hooks_dir / ".commit_metadata.json"
        reports_dir = hooks_dir / ".commit-reports"
                
        # Create reports directory if it doesn't exist
        reports_dir.mkdir(exist_ok=True)
        
        # Initialize scanner
        logging.info("Initializing SecretScanner")
        scanner = SecretScanner()
        
        # Read diff scan metadata if it exists
        diff_secrets = []
        validation_results = {}
        
        if metadata_file.exists():
            try:
                logging.info("Reading metadata from pre-commit hook")
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    diff_secrets = metadata.get('secrets_found', [])
                    validation_results = metadata.get('validation_results', {})
                    logging.info(f"Found {len(diff_secrets)} secrets from staged changes")
                    
                # Ensure validation messages are in commit message
                if validation_results:
                    logging.info("Checking if validation messages need to be added to commit")
                    amend_commit_with_messages(validation_results)
            except json.JSONDecodeError as e:
                logging.error(f"Error parsing metadata file: {e}")
        else:
            logging.info("No metadata file found from pre-commit hook")
        
        # Perform repository scan
        logging.info("Scanning entire repository for secrets")
        repo_secrets = scanner.scan_repository()
        logging.info(f"Found {len(repo_secrets)} secrets in repository scan")
        
        # Deduplicate secrets between diff and repo scans
        already_seen = set()
        unique_diff_secrets = []
        
        for secret in diff_secrets:
            key = (secret.get('file_path', ''), secret.get('line_number', ''))
            if key not in already_seen:
                already_seen.add(key)
                unique_diff_secrets.append(secret)
        
        # For repository scan view, include all secrets (diff + repo)
        all_secrets_for_repo_view = unique_diff_secrets.copy()
        
        # Add repo secrets that aren't already in the diff scan
        for secret in repo_secrets:
            key = (secret.get('file_path', ''), secret.get('line_number', ''))
            if key not in already_seen:
                already_seen.add(key)
                all_secrets_for_repo_view.append(secret)
        
        diff_secrets = unique_diff_secrets
        
        # Generate HTML report with both scan results
        output_path = reports_dir / "scan-report.html"
        logging.info(f"Generating HTML report at {output_path}")
        
        try:
            # Generate HTML report
            success = generate_html_report(
                str(output_path),
                diff_secrets=diff_secrets,
                repo_secrets=all_secrets_for_repo_view,
                has_secrets=bool(diff_secrets) or bool(all_secrets_for_repo_view)
            )
            
            if not success:
                logging.error("HTML report generation failed")
                
                # If HTML generation failed, create a simple HTML report as backup
                simple_html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Secret Scan Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1, h2 {{ color: #333366; }}
        .header {{ display: flex; justify-content: space-between; align-items: center; }}
        .btn {{ 
            background-color: #333366; 
            color: white; 
            border: none; 
            padding: 10px 20px; 
            border-radius: 5px; 
            cursor: pointer;
            font-size: 16px;
            display: inline-flex;
            align-items: center;
        }}
        .btn:hover {{ background-color: #252550; }}
        .icon {{ margin-right: 8px; }}
        table {{ border-collapse: collapse; width: 100%; margin-bottom: 30px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
        .tab-container {{ margin-top: 20px; }}
        .tab-buttons {{ display: flex; gap: 10px; margin-bottom: 20px; }}
        .tab-button {{ 
            padding: 10px 20px; 
            background-color: #f0f0f0; 
            border: none; 
            border-radius: 5px; 
            cursor: pointer;
        }}
        .tab-button.active {{ background-color: #333366; color: white; }}
        .tab-content {{ display: none; }}
        .tab-content.active {{ display: block; }}
    </style>
</head>
<body>
    <div id="reportContainer">
        <div class="header">
            <h1>Secret Scan Report</h1>
            <button onclick="window.print()" class="btn">
                <span class="icon">📥</span> Save as PDF
            </button>
        </div>
        
        <div class="tab-container">
            <div class="tab-buttons">
                <button class="tab-button active" id="diffBtn">Staged Changes</button>
                <button class="tab-button" id="repoBtn">Repository Scan</button>
            </div>
            
            <div id="diff-scan" class="tab-content active">
                <h2>Staged Changes - Secrets Found: {len(diff_secrets)}</h2>
                <table>
                    <tr>
                        <th>File</th>
                        <th>Line</th>
                        <th>Content</th>
                    </tr>
                    {''.join(f"<tr><td>{s.get('file_path', '')}</td><td>{s.get('line_number', '')}</td><td><pre>{s.get('line', '')}</pre></td></tr>" for s in diff_secrets) or "<tr><td colspan='3'>No secrets found in staged changes</td></tr>"}
                </table>
            </div>
            
            <div id="repo-scan" class="tab-content">
                <h2>Repository Scan - Secrets Found: {len(all_secrets_for_repo_view)}</h2>
                <table>
                    <tr>
                        <th>File</th>
                        <th>Line</th>
                        <th>Content</th>
                    </tr>
                    {''.join(f"<tr><td>{s.get('file_path', '')}</td><td>{s.get('line_number', '')}</td><td><pre>{s.get('line', '')}</pre></td></tr>" for s in all_secrets_for_repo_view) or "<tr><td colspan='3'>No secrets found in repository scan</td></tr>"}
                </table>
            </div>
        </div>
    </div>
    
    <script>
    // Simple tab switching
    document.getElementById('diffBtn').addEventListener('click', function() {{
        document.getElementById('diff-scan').classList.add('active');
        document.getElementById('repo-scan').classList.remove('active');
        document.getElementById('diffBtn').classList.add('active');
        document.getElementById('repoBtn').classList.remove('active');
    }});
    
    document.getElementById('repoBtn').addEventListener('click', function() {{
        document.getElementById('repo-scan').classList.add('active');
        document.getElementById('diff-scan').classList.remove('active');
        document.getElementById('repoBtn').classList.add('active');
        document.getElementById('diffBtn').classList.remove('active');
    }});
    
    // Print setup - show both tabs when printing
    window.onbeforeprint = function() {{
        // Show both tabs for printing
        document.getElementById('diff-scan').style.display = 'block';
        document.getElementById('repo-scan').style.display = 'block';
    }};
    
    window.onafterprint = function() {{
        // Restore tab visibility after printing
        document.getElementById('diff-scan').style.display = document.getElementById('diffBtn').classList.contains('active') ? 'block' : 'none';
        document.getElementById('repo-scan').style.display = document.getElementById('repoBtn').classList.contains('active') ? 'block' : 'none';
    }};
    </script>
</body>
</html>
"""
                # Write the simple HTML report
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(simple_html)
                logging.info("Generated simple HTML report as fallback")
                success = True
                
        except Exception as e:
            logging.error(f"Error generating HTML report: {e}", exc_info=True)
            success = False
        
        # Clean up metadata file
        try:
            if metadata_file.exists():
                metadata_file.unlink()
                logging.info(f"Metadata file removed: {metadata_file}")
        except Exception as e:
            logging.error(f"Warning: Failed to remove metadata file: {e}")
        
        # Open the report in browser if secrets were found and report was generated
        if success and (diff_secrets or repo_secrets):
            logging.info("Opening HTML report in browser")
            open_html_report(str(output_path))
        elif not success:
            logging.warning("HTML report generation failed, not opening browser")
        else:
            logging.info("No secrets found, HTML report generated but not opened")
        
        logging.info("Post-commit hook completed successfully")
        
    except Exception as e:
        logging.error(f"Error in post-commit hook: {e}", exc_info=True)
        print(f"Error in post-commit hook: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        # Make sure to clean up the marker file
        if MARKER_FILE.exists():
            MARKER_FILE.unlink()

if __name__ == '__main__':
    main() 