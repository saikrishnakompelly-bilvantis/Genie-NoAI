#!/usr/bin/env python3
"""Secret scanning module for detecting potential secrets in code."""

import sys
import os
import re
import json
import logging
import subprocess
from typing import List, Dict, Union, Set, Tuple, Optional
from datetime import datetime
import html
from .config import (
    PATTERNS, ENTROPY_THRESHOLD, HTML_CONFIG,
    EXCLUDED_EXTENSIONS, EXCLUDED_DIRECTORIES
)
from .utils import (
    setup_logging, calculate_entropy, get_git_metadata,
    is_git_repo, has_unstaged_changes, get_git_diff,
    mask_secret
)
import webbrowser
from pathlib import Path

class SecretScanner:
    """Main class for secret scanning functionality."""
    
    def __init__(self, log_file: str = "secretscan.log"):
        """Initialize the secret scanner."""
        self.log_file = log_file
        setup_logging(log_file)
        self.found_secrets: Set[Tuple[str, int]] = set()
    
    def scan_patterns(self, content: str, file_path: str = "", line_offset: int = 0) -> List[Dict[str, Union[str, int]]]:
        """Scan content for secret patterns."""
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
        
        return results

    def scan_variable_names(self, file_path: str) -> List[Dict[str, Union[str, int]]]:
        """Scan for suspicious variable names using git grep."""
        results = []
        suspicious_terms = ['secret', 'key', 'password', 'token', 'credential', 'auth']
        
        try:
            for term in suspicious_terms:
                # Use git grep to find lines containing suspicious terms
                cmd = ['git', 'grep', '-n', '-i', term, file_path]
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:  # Found matches
                    for line in result.stdout.split('\n'):
                        if not line:
                            continue
                        
                        # Parse git grep output (filename:line_number:content)
                        parts = line.split(':', 2)
                        if len(parts) != 3:
                            continue
                            
                        line_number = int(parts[1])
                        content = parts[2].strip()
                        
                        # Skip if it's a comment or empty line
                        if not content or content.startswith(('#', '//', '/*', '*', '--')):
                            continue
                        
                        key = (file_path, line_number)
                        if key not in self.found_secrets:
                            self.found_secrets.add(key)
                            results.append({
                                'file': file_path,
                                'line_number': line_number,
                                'line': content,
                                'Potential Secret': f'Suspicious variable name containing "{term}"',
                                'detection': 'variable_name'
                            })
        except Exception as e:
            logging.error(f"Error scanning variable names in {file_path}: {e}")
        
        return results

    def scan_entropy(self, content: str, file_path: str = "", line_offset: int = 0) -> List[Dict[str, Union[str, int]]]:
        """Scan content for high entropy strings."""
        results = []
        lines = content.split('\n')
        
        for line_number, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith(('#', '//', '/*', '*', '--')):
                continue
            
            key = (file_path, line_number + line_offset)
            
            # Skip if already found by other methods
            if key in self.found_secrets:
                continue
            
            # Check entropy
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

    def scan_content(self, content: str, file_path: str = "", line_offset: int = 0) -> List[Dict[str, Union[str, int]]]:
        """Scan content using all three methods."""
        all_results = []
        
        # 1. Pattern matching
        pattern_results = self.scan_patterns(content, file_path, line_offset)
        all_results.extend(pattern_results)
        
        # 2. Variable name scanning
        if file_path:
            var_results = self.scan_variable_names(file_path)
            all_results.extend(var_results)
        
        # 3. Entropy analysis
        entropy_results = self.scan_entropy(content, file_path, line_offset)
        all_results.extend(entropy_results)
        
        return all_results

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
    try:
        # Get the hooks directory (parent of the script)
        hooks_dir = Path(__file__).parent.parent
        template_path = hooks_dir / "commit_scripts" / "templates" / "report.html"
        
        if not template_path.exists():
            print(f"Warning: Template file not found at {template_path}")
            return False
            
        with open(template_path, 'r', encoding='utf-8') as f:
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
        return True
    except Exception as e:
        logging.error(f"Error generating HTML report: {e}")
        return False

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