#!/usr/bin/env python3
"""Secret scanning module for detecting potential secrets in code."""

import sys
import os
import re
import json
import logging
from typing import List, Dict, Union, Set, Tuple, Optional
from datetime import datetime
import html
from config import (
    PATTERNS, ENTROPY_THRESHOLD, HTML_CONFIG,
    EXCLUDED_EXTENSIONS, EXCLUDED_DIRECTORIES
)
from utils import (
    setup_logging, calculate_entropy, get_git_metadata,
    is_git_repo, has_unstaged_changes, get_git_diff,
    mask_secret
)
import webbrowser
class SecretScanner:
    """Main class for secret scanning functionality."""
    
    def __init__(self, log_file: str = "secretscan.log"):
        """Initialize the secret scanner."""
        self.log_file = log_file
        setup_logging(log_file)
        self.found_secrets: Set[Tuple[str, int]] = set()
    
    def scan_content(self, content: str, file_path: str = "", line_offset: int = 0) -> List[Dict[str, Union[str, int]]]:
        """Scan content for secrets using pattern matching and entropy analysis."""
        logging.debug(f"Scanning content for file: {file_path} with line offset: {line_offset}")
        results = []
        
        lines = content.split('\n')
        for line_number, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith(('#', '//', '/*', '*', '--')):
                continue
            
            key = (file_path, line_number + line_offset)
            
            # Check patterns
            for pattern, pattern_name in PATTERNS:
                if re.search(pattern, line) and key not in self.found_secrets:
                    self.found_secrets.add(key)
                    results.append({
                        'file': file_path,
                        'line_number': line_number + line_offset,
                        'line': line.strip(),
                        'pattern': pattern_name,
                        'detection': 'pattern'
                    })
                    break
            
            # Check entropy if no other match found
            if key not in self.found_secrets:
                entropy = calculate_entropy(line)
                if entropy > ENTROPY_THRESHOLD:
                    self.found_secrets.add(key)
                    results.append({
                        'file': file_path,
                        'line_number': line_number + line_offset,
                        'line': line.strip(),
                        'pattern': f'High Entropy ({entropy:.2f})',
                        'detection': 'entropy'
                    })
        
        return results

    def scan_file(self, file_path: str) -> List[Dict[str, Union[str, int]]]:
        """Scan a single file for secrets."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            return self.scan_content(content, file_path=file_path)
        except Exception as e:
            logging.error(f"Error scanning file {file_path}: {e}")
            return []

    def scan_git_diff(self) -> List[Dict[str, Union[str, int]]]:
        """Scan only changed lines in Git diff."""
        changes = get_git_diff()
        all_results = []
        
        for file, lines in changes.items():
            content = '\n'.join(line[1] for line in lines)
            results = self.scan_content(content, file_path=file, line_offset=lines[0][0] if lines else 0)
            all_results.extend(results)
        
        return all_results

def generate_html_report(output_path: str, **kwargs) -> None:
    """Generate an HTML report for secrets and disallowed files."""
    results_data = kwargs.get('results_data', [])
    disallowed_files = kwargs.get('disallowed_files', [])
    git_metadata = get_git_metadata()
    
    secrets_table_rows = "".join(
        f"""<tr>
            <td class="sno">{i}</td>
            <td class="filename">{html.escape(data.get('file', ''))}</td>
            <td class="line-number">{data.get('line_number', '')}</td>
            <td class="secret"><div class="secret-content">{html.escape(mask_secret(data.get('line', '')))}</div></td>
        </tr>"""
        for i, data in enumerate(results_data, 1)
    )

    disallowed_files_section = ""
    if disallowed_files:
        disallowed_files_section = f"""
        <div id="disallowedFilesFound">
            <h2>Disallowed Files Found:</h2>
            <table id="disallowedFilesTable">
                <tr>
                    <th style="width:5%">S.No</th>
                    <th style="width:95%">Filename</th>
                </tr>
                {''.join(f'<tr><td class="sno">{i}</td><td class="disallowed-file">{html.escape(file)}</td></tr>' for i, file in enumerate(disallowed_files, 1))}
            </table>
        </div>
        """

    # Generate HTML content using the template
    hooks_dir = os.path.expanduser("~/.genie/hooks/commit-scripts/")
    with open(os.path.join(hooks_dir, 'templates/report.html'), 'r') as f:
        template = f.read()
    html_content = template.format(
        title=HTML_CONFIG['title'],
        primary_color=HTML_CONFIG['styles']['primary_color'],
        error_color=HTML_CONFIG['styles']['error_color'],
        background_color=HTML_CONFIG['styles']['background_color'],
        container_background=HTML_CONFIG['styles']['container_background'],
        header_background=HTML_CONFIG['styles']['header_background'],
        git_metadata=git_metadata,
        disallowed_files_section=disallowed_files_section,
        secrets_table_rows=secrets_table_rows
    )

    with open(output_path, 'w') as f:
        f.write(html_content)
    logging.info(f"HTML report generated at {output_path}")
        # Open the HTML report in the default web browser
    webbrowser.open(f'file://{os.path.abspath(output_path)}')
    return 


def main() -> None:
    """Main entry point for the secret scanner."""
    args = sys.argv[1:]
    scanner = SecretScanner()

    if "--diff" in args:
        logging.info("Scanning only changed lines in Git diff...")
        try:
            results = scanner.scan_git_diff()
        except Exception as e:
            logging.error(f"Error scanning Git diff: {e}")
            sys.exit(1)
    elif len(args) == 1:
        file_path = args[0]
        if not os.path.isfile(file_path):
            print(f"Error: File '{file_path}' not found.")
            sys.exit(1)
        results = scanner.scan_file(file_path)
    else:
        # Auto-detect mode: If in a Git repo with unstaged changes, scan Git diff
        if is_git_repo() and has_unstaged_changes():
            logging.info("Detected unstaged changes in Git. Running in diff mode...")
            results = scanner.scan_git_diff()
        else:
            print("Usage: secretscan.py <file> or run inside a Git repo with unstaged changes.")
            sys.exit(1)

    if results:
        print(json.dumps(results, indent=4))
        sys.exit(1)
    else:
        print("No secrets found.")
        sys.exit(0)

if __name__ == "__main__":
    main()