#!/usr/bin/env python3
import sys
import json
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

# Variable name patterns that might indicate secrets
VARIABLE_PATTERNS = [
    (r'(?i)var\s+.*(?:password|secret|token|key|credential|auth)', 'Variable Declaration - Secret'),
    (r'(?i)let\s+.*(?:password|secret|token|key|credential|auth)', 'Variable Declaration - Secret'),
    (r'(?i)const\s+.*(?:password|secret|token|key|credential|auth)', 'Variable Declaration - Secret'),
    (r'(?i)private\s+.*(?:password|secret|token|key|credential|auth)', 'Variable Declaration - Secret'),
    (r'(?i)protected\s+.*(?:password|secret|token|key|credential|auth)', 'Variable Declaration - Secret'),
    (r'(?i)\$(?:password|secret|token|key|credential|auth)', 'PHP Variable - Secret'),
    (r'(?i)self\.(?:password|secret|token|key|credential|auth)', 'Python Self Variable - Secret'),
    (r'(?i)this\.(?:password|secret|token|key|credential|auth)', 'JavaScript/TypeScript This Variable - Secret'),
]

# Assignment patterns that might indicate secrets
ASSIGNMENT_PATTERNS = [
    (r'(?i)(?:password|secret|token|key|credential|auth)\s*[=:]\s*["\'][^"\']+["\']', 'Direct String Assignment'),
    (r'(?i)(?:password|secret|token|key|credential|auth)\s*[=:]\s*`[^`]+`', 'Template Literal Assignment'),
    (r'(?i)(?:password|secret|token|key|credential|auth)\s*[=:]\s*process\.env\.[A-Za-z0-9_]+', 'Environment Variable Assignment'),
    (r'(?i)(?:password|secret|token|key|credential|auth)\s*[=:]\s*os\.getenv\([^)]+\)', 'Python Environment Variable'),
    (r'(?i)(?:password|secret|token|key|credential|auth)\s*[=:]\s*config\[[^\]]+\]', 'Config Assignment'),
]

# Secret patterns to check
PATTERNS = [
    (r'(?i)aws.*(access|secret|key)', 'AWS Credential'),
    (r'(?i)private.*(key|token)', 'Private Key/Token'),
    (r'(?i)(api|auth|token|secret|password|credential).*[=:][^{}\n\r]*', 'Generic Secret'),
    (r'(?i)bearer\s+[a-zA-Z0-9_\-\.]+', 'Bearer Token'),
    (r'(?i)basic\s+[a-zA-Z0-9_\-\.]+', 'Basic Auth'),
    (r'(?i)ssh-rsa\s+[a-zA-Z0-9/\+=]+', 'SSH Key'),
    (r'(?i)-----BEGIN\s+(?:RSA|OPENSSH|DSA|EC|PGP)\s+(?:PRIVATE|PUBLIC)\s+KEY-----', 'Cryptographic Key'),
    (r'(?i)github[_\-\.]?token\s*[=:]\s*[a-zA-Z0-9_\-]+', 'GitHub Token'),
    (r'(?i)npm[_\-\.]?token\s*[=:]\s*[a-zA-Z0-9_\-]+', 'NPM Token'),
    # Additional patterns from the provided script
    (r'sk-[a-zA-Z0-9_-]{36,}', 'OpenAI API Key'),
    (r'AKIA[0-9A-Z]{16}', 'AWS Access Key ID'),
    (r'ASIA[0-9A-Z]{16}', 'AWS Session Token'),
    (r'AIza[0-9A-Za-z_-]{35}', 'Google API Key'),
    (r'AIzaSy[A-Za-z0-9_-]{35}', 'Google API Key'),
    (r'[0-9a-fA-F]{32}', 'MD5 Hash or API Key'),
    (r'[0-9a-fA-F]{40}', 'SHA1 Hash or API Key'),
    (r'[A-Za-z0-9_-]{64}', 'Generic Secret Key'),
    (r'xox[baprs]-[0-9A-Za-z]{10,48}', 'Slack Token'),
    (r'[A-Za-z0-9]{20}-us[0-9]{2}', 'Generic API Key'),
    (r'SG\.[A-Za-z0-9_-]{22}\.[A-Za-z0-9_-]{43}', 'SendGrid API Key'),
    (r'sq0atp-[0-9A-Za-z_-]{22}', 'Square Access Token'),
    (r'sq0csp-[0-9A-Za-z_-]{43}', 'Square OAuth Secret'),
    (r'sk_live_[0-9a-zA-Z]{24}', 'Stripe Secret Key'),
    (r'pt_[a-zA-Z0-9]{20}', 'Generic Token'),
    (r'ghp_[0-9a-zA-Z]{36}', 'GitHub Personal Access Token'),
    (r'gh[oasr]_[0-9a-zA-Z]{36}', 'GitHub Token'),
    (r'glpat-[0-9a-zA-Z-]{20}', 'GitLab Personal Access Token'),
    (r'eyJ[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+', 'JWT Token')
]

def calculate_entropy(text: str) -> float:
    """Calculate Shannon entropy for a given text."""
    if not text:
        return 0
    
    # Convert to string if not already
    text = str(text)
    
    # Calculate frequency of each character
    frequency = {}
    for char in text:
        frequency[char] = frequency.get(char, 0) + 1
    
    # Calculate entropy
    length = len(text)
    return -sum((count / length) * math.log2(count / length) for count in frequency.values())

def check_variable_patterns(line: str) -> Union[str, None]:
    """Check if a line contains variable patterns indicating secrets."""
    for pattern, pattern_name in VARIABLE_PATTERNS:
        if re.search(pattern, line):
            return pattern_name
    return None

def check_assignment_patterns(line: str) -> Union[str, None]:
    """Check if a line contains assignment patterns indicating secrets."""
    for pattern, pattern_name in ASSIGNMENT_PATTERNS:
        if re.search(pattern, line):
            return pattern_name
    return None

def scan_content(content: str, file_path: str = "", line_offset: int = 0) -> List[Dict[str, Union[str, int]]]:
    """
    Scan content for secrets using pattern matching, entropy analysis, and variable scanning.
    """
    logging.debug(f"Scanning content for file: {file_path} with line offset: {line_offset}")
    results = []
    found_secrets: Set[Tuple[str, int]] = set()  # Track unique (file, line) pairs
    
    lines = content.split('\n')
    for line_number, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue
            
        # Skip comments
        if line.startswith(('#', '//', '/*', '*', '--')):
            continue
        
        key = (file_path, line_number + line_offset)
        
        # Check variable patterns
        var_pattern = check_variable_patterns(line)
        if var_pattern and key not in found_secrets:
            found_secrets.add(key)
            results.append({
                'file': file_path,
                'line_number': line_number + line_offset,
                'line': line.strip(),
                'pattern': var_pattern,
                'detection': 'variable'
            })
            continue  # Skip other checks for this line
        
        # Check assignment patterns
        assign_pattern = check_assignment_patterns(line)
        if assign_pattern and key not in found_secrets:
            found_secrets.add(key)
            results.append({
                'file': file_path,
                'line_number': line_number + line_offset,
                'line': line.strip(),
                'pattern': assign_pattern,
                'detection': 'assignment'
            })
            continue  # Skip other checks for this line
        
        # Check regular patterns
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
                break  # Found a match, no need to check other patterns
        
        # Only check entropy if no other detection was made
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

def scan_file(file_path: str) -> List[Dict[str, Union[str, int]]]:
    """
    Scan an entire file for secrets.
    
    Args:
        file_path: Path to the file to scan
        
    Returns:
        List of dictionaries containing found secrets
    """
    logging.debug(f"Starting file scan for: {file_path}")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return scan_content(content, file_path)
    except Exception as e:
        logging.error(f"Error scanning {file_path}: {e}")
        return []

def scan_git_diff(diff_content: str) -> List[Dict[str, Union[str, int]]]:
    """
    Scan git diff output for secrets.
    
    Args:
        diff_content: The git diff output to scan
        
    Returns:
        List of dictionaries containing found secrets
    """
    logging.debug("Starting git diff scan")
    logging.debug(f"Received diff content length: {len(diff_content)} characters")
    
    results = []
    current_file = ""
    current_content = []
    line_offset = 0
    
    lines = diff_content.split('\n')
    logging.debug(f"Number of lines in diff: {len(lines)}")
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Check for file header in diff
        if line.startswith('diff --git'):
            logging.debug(f"Found diff header: {line}")
            # Process previous file if exists
            if current_file and current_content:
                logging.debug(f"Processing accumulated content for {current_file}")
                results.extend(scan_content('\n'.join(current_content), current_file, line_offset))
            
            # Reset for new file
            current_file = ""
            current_content = []
            line_offset = 0
            
        # Get new file name
        elif line.startswith('+++ b/'):
            current_file = line[6:]
            logging.debug(f"Processing file: {current_file}")
            
        # Handle hunk header
        elif line.startswith('@@'):
            try:
                # Parse the @@ line to get the starting line number
                # Format: @@ -old_start,old_count +new_start,new_count @@
                hunk_header = line.split('@@')[1].strip()
                logging.debug(f"Parsing hunk header: {hunk_header}")
                old_range, new_range = hunk_header.split(' ')
                new_start = new_range.split(',')[0][1:]  # Remove the '+' prefix
                line_offset = int(new_start) - 1
                logging.debug(f"New hunk starting at line offset: {line_offset}")
            except Exception as e:
                logging.error(f"Error parsing hunk header '{line}': {e}")
                line_offset = 0
                
        # Handle added/modified lines
        elif line.startswith('+') and not line.startswith('+++'):
            content_line = line[1:]  # Remove the '+' prefix
            current_content.append(content_line)
            logging.debug(f"Added line to scan: {content_line[:50]}...")
            
        i += 1
    
    # Process the last file
    if current_file and current_content:
        logging.debug(f"Processing final file: {current_file}")
        results.extend(scan_content('\n'.join(current_content), current_file, line_offset))
    
    logging.info(f"Scan complete. Found {len(results)} potential secrets")
    return results

def deduplicate_results(results: List[Dict[str, Union[str, int]]]) -> List[Dict[str, Union[str, int]]]:
    """
    Deduplicate results based on file path and line number.
    Takes the first detection found for each line.
    """
    unique_results = {}
    
    for result in results:
        key = (result['file'], result['line_number'])
        if key not in unique_results:
            unique_results[key] = result
    
    return list(unique_results.values())

def main():
    """Main function to handle file scanning."""
    try:
        # If a file path is provided as argument, scan that file
        if len(sys.argv) > 1:
            file_path = sys.argv[1]
            results = scan_file(file_path)
            # Output results as JSON
            json.dump(results, sys.stdout, indent=2)
            # Exit with success if we found secrets (for reporting) or no secrets (clean)
            sys.exit(0)
        else:
            logging.error("No file path provided")
            sys.exit(1)
    except Exception as e:
        logging.error(f"Error in main: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
