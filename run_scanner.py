#!/usr/bin/env python3
import sys
import os
import glob

# Add the hooks directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src/hooks'))

# Import the SecretScanner and should_exclude_file
from src.hooks.commit_scripts.secretscan import SecretScanner
from src.hooks.commit_scripts.config import should_exclude_file

# Create scanner instance
scanner = SecretScanner()

# Get all files in the sample directory
sample_files = glob.glob('sample/**/*', recursive=True)
sample_files = [f for f in sample_files if os.path.isfile(f)]

print("Files that will be scanned vs excluded:")
print("--------------------------------------")

# Group files by whether they'll be scanned or excluded
excluded_files = []
scanned_files = []

for file_path in sample_files:
    # Check if the file should be excluded based on our exclusion rules
    if should_exclude_file(file_path):
        excluded_files.append(file_path)
    else:
        scanned_files.append(file_path)

# Print excluded files
print("\nEXCLUDED FILES:")
for file in sorted(excluded_files):
    print(f"  - {file}")

# Print scanned files
print("\nFILES THAT WILL BE SCANNED:")
for file in sorted(scanned_files):
    print(f"  - {file}")

# Run the scanner on the files that will be scanned
print("\nRunning scan on non-excluded files...")
results = scanner.scan_files(scanned_files)

# Display results
if results:
    print(f"\nFound {len(results)} potential secrets:")
    for i, secret in enumerate(results, 1):
        print(f"\n{i}. {secret['file_path']} (line {secret['line_number']}):")
        print(f"   Type: {secret['type']}")
        print(f"   Content: {secret['line']}")
else:
    print("\nNo secrets found in scanned files.") 