#!/usr/bin/env python3
import sys
import subprocess
import re
import os
import math
import logging
from typing import List, Dict, Union, Set, Tuple

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'secretscan.log')),
        logging.StreamHandler()
    ]
)

# Entropy threshold for identifying potential secrets
ENTROPY_THRESHOLD = 5.5

# Patterns for detecting secrets (same as before)
PATTERNS = [
    (r'(?i)aws.*(access|secret|key)', 'AWS Credential'),
    (r'(?i)private.*(key|token)', 'Private Key/Token'),
    (r'(?i)(api|auth|token|secret|password|credential).*[=:][^{}\n\r]*', 'Generic Secret'),
    (r'(?i)bearer\s+[a-zA-Z0-9_\-\.]+', 'Bearer Token'),
    (r'(?i)ssh-rsa\s+[a-zA-Z0-9/\+=]+', 'SSH Key'),
    (r'(?i)-----BEGIN\s+(?:RSA|OPENSSH|DSA|EC|PGP)\s+(?:PRIVATE|PUBLIC)\s+KEY-----', 'Cryptographic Key'),
    (r'(?i)github[_\-\.]?token\s*[=:]\s*[a-zA-Z0-9_\-]+', 'GitHub Token'),
    (r'ghp_[0-9a-zA-Z]{36}', 'GitHub Personal Access Token'),
    (r'sk-[a-zA-Z0-9_-]{36,}', 'OpenAI API Key'),
    (r'AKIA[0-9A-Z]{16}', 'AWS Access Key ID'),
    (r'AIza[0-9A-Za-z_-]{35}', 'Google API Key'),
    (r'[A-Za-z0-9_-]{64}', 'Generic Secret Key'),
    (r'eyJ[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+', 'JWT Token')
]

def calculate_entropy(text: str) -> float:
    """Calculate Shannon entropy for a given text."""
    if not text:
        return 0
    frequency = {char: text.count(char) for char in set(text)}
    length = len(text)
    return -sum((count / length) * math.log2(count / length) for count in frequency.values())

def scan_content(content: str, file_path: str = "", line_offset: int = 0) -> List[Dict[str, Union[str, int]]]:
    """Scan content for secrets using pattern matching and entropy analysis."""
    logging.debug(f"Scanning content for file: {file_path} with line offset: {line_offset}")
    results = []
    found_secrets: Set[Tuple[str, int]] = set()
    
    lines = content.split('\n')
    for line_number, line in enumerate(lines, 1):
        line = line.strip()
        if not line or line.startswith(('#', '//', '/*', '*', '--')):
            continue
        
        key = (file_path, line_number + line_offset)
        
        # Check patterns
        for pattern, pattern_name in PATTERNS:
            if re.search(pattern, line) and key not in found_secrets:
                found_secrets.add(key)
                results.append({
                    'file': file_path,
                    'line_number': line_number + line_offset,
                    'line': line.strip(),
                    'pattern': pattern_name,
                    'detection': 'pattern'
                })
                break
        
        # Check entropy if no other match found
        if key not in found_secrets:
            entropy = calculate_entropy(line)
            if entropy > ENTROPY_THRESHOLD:
                found_secrets.add(key)
                results.append({
                    'file': file_path,
                    'line_number': line_number + line_offset,
                    'line': line.strip(),
                    'pattern': f'High Entropy ({entropy:.2f})',
                    'detection': 'entropy'
                })
    
    return results

def get_git_diff() -> Dict[str, List[Tuple[int, str]]]:
    """Retrieve the diff of changed lines from Git."""
    diff_output = subprocess.run(
        ['git', 'diff', '--unified=0', '--no-color'], capture_output=True, text=True
    ).stdout

    file_changes = {}
    current_file = None
    current_line_number = None

    for line in diff_output.splitlines():
        if line.startswith('diff --git'):
            current_file = None
        elif line.startswith('+++ b/'):
            current_file = line[6:]
            file_changes[current_file] = []
        elif line.startswith('@@'):
            match = re.search(r'\+(\d+)', line)
            if match:
                current_line_number = int(match.group(1)) - 1  # Adjust for zero-indexing
        elif current_file and line.startswith('+') and not line.startswith('+++'):
            file_changes[current_file].append((current_line_number, line[1:].strip()))
            current_line_number += 1  # Increment for multi-line additions
    
    return file_changes

def scan_git_diff():
    """Scan only changed lines in Git diff."""
    changes = get_git_diff()
    all_results = []
    
    for file, lines in changes.items():
        content = '\n'.join(line[1] for line in lines)  # Extract added lines
        results = scan_content(content, file_path=file, line_offset=lines[0][0] if lines else 0)
        all_results.extend(results)
    
    return all_results

import os
import subprocess
import html
from datetime import datetime
import webbrowser

def get_git_metadata():
    """Retrieve Git metadata like author, branch, commit hash, and timestamp."""
    try:
        repo_name = os.path.basename(os.getcwd())  # Get current directory name (assuming it's the repo)
        branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"]).decode().strip()
        commit_hash = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()
        author = subprocess.check_output(["git", "log", "-1", "--pretty=format:%an"]).decode().strip()
        timestamp_24h = subprocess.check_output(["git", "log", "-1", "--pretty=format:%cd", "--date=format:%Y-%m-%d %I:%M:%S %p"]).decode().strip()
    except subprocess.CalledProcessError:
        repo_name = "Unknown Repo"
        branch = "Unknown Branch"
        commit_hash = "Unknown Commit"
        author = "Unknown Author"
        timestamp_24h = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")  # Fallback to system time

    return {
        "repo_name": repo_name,
        "branch": branch,
        "commit_hash": commit_hash,
        "author": author,
        "timestamp": timestamp_24h
    }
def generate_html_report(output_path, **kwargs):
    """Generate an HTML report for secrets and disallowed files."""
    import html
    from datetime import datetime
    import os
    import webbrowser

    # Extract data from kwargs
    results_data = kwargs.get('results_data', [])
    disallowed_files = kwargs.get('disallowed_files', [])
    metadata = kwargs.get('metadata', {})

    # Use metadata if available
    if metadata:
        results_data = metadata.get('secrets_found', [])
        disallowed_files = metadata.get('disallowed_files', [])

    git_metadata = get_git_metadata()
    
    def mask_secret(secret, visible_chars=3):
        if not secret:
            return ""
        secret = str(secret)
        if len(secret) <= visible_chars * 2:
            return secret
        return f"{secret[:visible_chars]}{'*' * (len(secret) - visible_chars * 2)}{secret[-visible_chars:]}"

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



    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Genie - Secret Scan Results</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/pdfmake/0.2.4/pdfmake.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/pdfmake/0.2.4/vfs_fonts.js"></script>
    <style>
        body {{ font-family: -apple-system, system-ui, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .header-info {{ 
            background: #f8f9fa; 
            padding: 15px; 
            border-radius: 5px; 
            margin-bottom: 20px;
            border-left: 4px solid #07439C;
        }}
        .header-info p {{ 
            margin: 5px 0; 
            color: #666;
            font-size: 14px;
        }}
        .header-info strong {{ 
            color: #333;
            margin-right: 5px;
        }}
        table {{ 
            width: 100%; 
            border-collapse: collapse; 
            margin-top: 20px;
            table-layout: fixed;
        }}
        th, td {{ 
            padding: 12px; 
            text-align: left; 
            border: 1px solid #ddd;
            vertical-align: top;
            overflow-wrap: break-word;
            word-wrap: break-word;
            word-break: break-all;
            hyphens: auto;
        }}
        th {{ background: #07439C; color: white; }}
        tr:nth-child(even) {{ background: #f9f9f9; }}
        .secret-content {{ 
            color: #d32f2f; 
            font-family: monospace;
            white-space: pre-wrap;
            max-width: 100%;
            display: block;
            overflow-x: auto;
            padding: 4px 8px;
            margin: 0;
            border-radius: 4px;
            background: rgba(211, 47, 47, 0.05);
        }}
        .line-number {{ 
            color: #e74c3c; 
            font-weight: bold; 
            text-align: center;
        }}
        .disallowed-file {{
            color: #e74c3c;
            font-family: monospace;
        }}
        .sno {{
            text-align: center;
        }}
        h1, h2 {{ color: #07439C; margin-bottom: 20px; }}
        .download-btn {{
            padding: 10px 20px;
            background-color: #07439C;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            margin-bottom: 20px;
        }}
        .download-btn:hover {{
            background-color: #053278;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <h1>Genie - Secret Scan Results</h1>
            <button id="downloadButton" class="download-btn">Download as PDF</button>
        </div>
        <div class="header-info">
                <div>
                <p><strong>Git Author:</strong> {git_metadata["author"]}</p>
                <p><strong>Repository:</strong> {git_metadata["repo_name"]}</p>
                <p><strong>Branch:</strong> {git_metadata["branch"]}</p>
                <p><strong>Commit Hash:</strong> {git_metadata["commit_hash"]}</p>
                <p><strong>Timestamp:</strong> {git_metadata["timestamp"]}</p>
                </div>
        </div>
        {disallowed_files_section}
        <h2>Potential Secrets Found:</h2>
        <table id="secretsTable">
            <tr>
                <th style="width:5%">S.No</th>
                <th style="width:25%">Filename</th>
                <th style="width:10%">Line #</th>
                <th style="width:60%">Secret</th>
            </tr>
            {secrets_table_rows}
        </table>
    </div>
    <script>
    document.getElementById("downloadButton").addEventListener("click", () => {{
        // Get secrets table data
        const secretsTable = document.getElementById("secretsTable");
        const secretRows = secretsTable.querySelectorAll("tr:not(:first-child)");
        const secrets = Array.from(secretRows).map((row, index) => {{
            const cells = row.querySelectorAll("td");
            return {{
                sno: cells[0]?.innerText || "",
                filename: cells[1]?.innerText || "",
                lineNumber: cells[2]?.innerText || "",
                secret: cells[3]?.innerText || ""
            }};
        }});

        // Get disallowed files data if it exists
        const disallowedFilesSection = document.getElementById("disallowedFilesFound");
        const disallowedRows = disallowedFilesSection ? 
            Array.from(disallowedFilesSection.querySelectorAll("tr:not(:first-child)")) : [];
        const disallowedFiles = disallowedRows.map(row => {{
            const cells = row.querySelectorAll("td");
            return {{
                sno: cells[0]?.innerText || "",
                filename: cells[1]?.innerText || ""
            }};
        }});

        // Create file name using current date
        const currentDate = new Date();
        const formattedDate = currentDate.toLocaleDateString('en-GB', {{
            day: '2-digit', month: 'short', year: 'numeric'
        }}).replace(' ', '_').replace(',', '');
        const fileName = 'repo_scan_' + formattedDate + '.pdf';

        // Create the PDF document definition
        const docDefinition = {{
            pageOrientation: 'landscape',
            content: [
                {{ text: 'Genie - Secret Scan Results', style: 'header' }},
                {{ text: `Git Author: ${git_metadata['author']}`, style: 'info' }},
                {{ text: `Repository: ${git_metadata['repo_name']}`, style: 'info' }},
                {{ text: `Branch: ${git_metadata['branch']}`, style: 'info' }},
                {{ text: `Commit Hash: ${git_metadata['commit_hash']}`, style: 'info' }},
                {{ text: `Timestamp: ${git_metadata['timestamp']}`, style: 'info' }},
                // Disallowed Files Section
                ...(disallowedFiles.length ? [
                    {{ text: 'Disallowed Files Found:', style: 'subheader' }},
                    {{
                        table: {{
                            headerRows: 1,
                            widths: ['5%', '95%'],
                            body: [
                                [
                                    {{ text: 'S.No', fillColor: '#E9E5E5', bold: true, alignment: 'center' }},
                                    {{ text: 'Filename', fillColor: '#E9E5E5', bold: true }}
                                ],
                                ...disallowedFiles.map(file => [
                                    {{ text: file.sno, alignment: 'center' }},
                                    {{ text: file.filename }}
                                ])
                            ]
                        }},
                        margin: [0, 0, 0, 20]
                    }}
                ] : []),
                // Secrets Section
                {{ text: 'Potential Secrets Found:', style: 'subheader' }},
                {{
                    table: {{
                        headerRows: 1,
                        widths: ['5%', '25%', '10%', '60%'],
                        body: [
                            [
                                {{ text: 'S.No', fillColor: '#E9E5E5', bold: true, alignment: 'center' }},
                                {{ text: 'Filename', fillColor: '#E9E5E5', bold: true }},
                                {{ text: 'Line #', fillColor: '#E9E5E5', bold: true, alignment: 'center' }},
                                {{ text: 'Secret', fillColor: '#E9E5E5', bold: true }}
                            ],
                            ...secrets.map((secret, index) => [
                                {{ text: secret.sno, alignment: 'center' }},
                                secret.filename,
                                {{ text: secret.lineNumber, alignment: 'center' }},
                                secret.secret
                            ])
                        ]
                    }}
                }}
            ],
            styles: {{
                header: {{
                    fontSize: 18,
                    bold: true,
                    alignment: 'center',
                    margin: [0, 0, 0, 10]
                }},
                subheader: {{
                    fontSize: 14,
                    bold: true,
                    margin: [0, 10, 0, 5]
                }}
            }}
        }};

        // Generate and download the PDF
        pdfMake.createPdf(docDefinition).download(fileName);
    }});
    </script>
</body>
</html>"""

    with open(output_path, 'w') as f:
        f.write(html_content)
    print(f"HTML report generated at {output_path}")

    # Open the HTML report in the default web browser
    webbrowser.open(f'file://{os.path.abspath(output_path)}')
    return 

if __name__ == "__main__":
    import json
    import os
    import sys
    import logging
    import subprocess

    def is_git_repo():
        """Check if the script is inside a Git repository."""
        try:
            subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError:
            return False

    def has_unstaged_changes():
        """Check if there are unstaged changes in Git."""
        diff_output = subprocess.run(["git", "diff", "--unified=0", "--no-color"], capture_output=True, text=True).stdout
        return bool(diff_output.strip())  # True if diff is not empty

    args = sys.argv[1:]

    if "--diff" in args:
        logging.info("Scanning only changed lines in Git diff...")
        try:
            results = scan_git_diff()
        except Exception as e:
            logging.error(f"Error scanning Git diff: {e}")
            sys.exit(1)
    elif len(args) == 1:
        file_path = args[0]
        if not os.path.isfile(file_path):
            print(f"Error: File '{file_path}' not found.")
            sys.exit(1)

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        results = scan_content(content, file_path=file_path)
    else:
        # Auto-detect mode: If in a Git repo with unstaged changes, scan Git diff
        if is_git_repo() and has_unstaged_changes():
            logging.info("Detected unstaged changes in Git. Running in diff mode...")
            results = scan_git_diff()
        else:
            print("Usage: secretscan.py <file> or run inside a Git repo with unstaged changes.")
            sys.exit(1)

    if results:
        print(json.dumps(results, indent=4))
        sys.exit(1)
    else:
        print("No secrets found.")
        sys.exit(0)
