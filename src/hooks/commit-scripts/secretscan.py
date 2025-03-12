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

if __name__ == "__main__":
    import json

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

    # Automatically decide whether to scan Git diff or a file
    if len(sys.argv) == 2 and sys.argv[1] == "--diff":
        if is_git_repo() and has_unstaged_changes():
            logging.info("Detected unstaged changes in Git. Running in diff mode...")
            results = scan_git_diff()
        else:
            print("No unstaged changes found or not inside a Git repository.")
            sys.exit(1)
    elif len(sys.argv) == 2 and sys.argv[1] != "--diff":
        file_path = sys.argv[1]
        if not os.path.isfile(file_path):
            print(f"Error: File '{file_path}' not found.")
            sys.exit(1)

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        results = scan_content(content, file_path=file_path)
    else:
        print("Usage: secretscan.py [file_path] or run inside a Git repo with unstaged changes.")
        sys.exit(1)

    if results:
        print(json.dumps(results, indent=4))
        sys.exit(1)
    else:
        print("No secrets found.")
        sys.exit(0)
