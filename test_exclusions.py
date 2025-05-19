#!/usr/bin/env python3
import sys
import os

# Add the hooks directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src/hooks'))

# Import the file exclusion function
from src.hooks.commit_scripts.config import should_exclude_file

# Files to test
files_to_test = [
    'sample/config_file.py',           # Should NOT be excluded
    'sample/normal_file.js',           # Should NOT be excluded
    'sample/notes.txt',                # Might be excluded (txt)
    'sample/test_api_keys.py',         # Should be excluded (test in name)
    'sample/testing_file.py',          # Should be excluded (test in name)
    'sample/unit_test_credentials.py', # Should be excluded (test in name)
    'sample/sample_data.csv',          # Should be excluded (csv extension)
    'sample/excluded_file.pdf',        # Should be excluded (pdf extension)
    'sample/config.json',              # Should be excluded (json extension)
    'sample/test_directory/config.py', # Should be excluded (in test directory)
    'sample/tests/db_config.py',       # Should be excluded (in tests directory)
    'sample/integration_tests/login.py' # Should be excluded (in *tests* directory)
]

# Test each file
print("Testing file exclusions:")
print("-----------------------")
for file_path in files_to_test:
    result = should_exclude_file(file_path)
    excluded_status = "EXCLUDED" if result else "NOT excluded"
    print(f"{file_path}: {excluded_status}") 