"""Configuration settings for secret scanning."""

from typing import List, Tuple, Dict

# Entropy threshold for identifying potential secrets
ENTROPY_THRESHOLD = 5.5

# Patterns for detecting secrets
PATTERNS: List[Tuple[str, str]] = [
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

# File extensions to exclude from scanning
EXCLUDED_EXTENSIONS = {
    'zip', 'gz', 'tar', 'rar', '7z', 'exe', 'dll', 'so', 'dylib',
    'jar', 'war', 'ear', 'class', 'pyc', 'o', 'a', 'lib', 'obj',
    'bin', 'jpg', 'jpeg', 'png', 'gif', 'bmp', 'ico', 'mp3', 'mp4',
    'avi', 'mov', 'wmv', 'flv', 'pdf', 'doc', 'docx', 'xls', 'xlsx',
    'ppt', 'pptx', 'ttf', 'otf', 'woff', 'woff2', 'eot', 'svg',
    'tif', 'tiff', 'ico', 'webp'
}

# Directories to exclude from scanning
EXCLUDED_DIRECTORIES = {
    'distribution', 'node_modules', 'vendor', 'build', 'dist',
    'reports', 'scan_results', '__pycache__', '.git'
}

# Disallowed file extensions that might contain sensitive data
DISALLOWED_EXTENSIONS = {
    '.crt', '.cer', '.ca-bundle', '.p7b', '.p7c', '.p7s', '.pem',
    '.jceks', '.key', '.keystore', '.jks', '.p12', '.pfx'
}

# HTML report configuration
HTML_CONFIG = {
    'title': 'Genie - Secret Scan Results',
    'styles': {
        'primary_color': '#07439C',
        'error_color': '#d32f2f',
        'background_color': '#f5f5f5',
        'container_background': 'white',
        'header_background': '#f8f9fa',
    }
} 