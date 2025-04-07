#!/usr/bin/env python3
import os
import csv
import io
import time
import datetime
import logging
import subprocess
import json
import platform
import getpass
import base64
import socket
from pathlib import Path

# Add python-dotenv for environment variable management
try:
    from dotenv import load_dotenv
except ImportError:
    # If dotenv is not installed, we'll define a simple version
    def load_dotenv(path=None):
        """Simple .env file loader when python-dotenv is not available."""
        if not path:
            path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
        
        if not os.path.exists(path):
            logging.warning(f".env file not found at {path}")
            return False
            
        with open(path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip().strip('"\'')
        return True

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Load environment variables from .env file
env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
load_dotenv(env_file)

# GitHub API configuration
GITHUB_API_BASE = "https://api.github.com"

# Get configuration from environment variables with fallbacks
TRACKING_REPO_OWNER = os.environ.get("TRACKING_REPO_OWNER", "your-org-name")
TRACKING_REPO_NAME = os.environ.get("TRACKING_REPO_NAME", "installation-tracking")
CSV_PATH = os.environ.get("TRACKING_CSV_PATH", "installations.csv")

def get_github_username():
    """Get the GitHub username from Git configuration."""
    try:
        import subprocess
        # Try to get user.email from git config
        result = subprocess.run(
            ['git', 'config', 'user.email'],
            capture_output=True,
            text=True,
            check=False
        )
        email = result.stdout.strip()
        
        # Try to get user.name from git config
        result = subprocess.run(
            ['git', 'config', 'user.name'],
            capture_output=True,
            text=True,
            check=False
        )
        name = result.stdout.strip()
        
        # Try to get GitHub username if set explicitly
        result = subprocess.run(
            ['git', 'config', 'github.user'],
            capture_output=True,
            text=True,
            check=False
        )
        github_user = result.stdout.strip()
        
        if github_user:
            # If github.user is explicitly set, use that
            return github_user
        else:
            # Otherwise, use user.email (before the @) or user.name
            if email and '@' in email:
                # If it's a GitHub email, it might be username@users.noreply.github.com
                if 'users.noreply.github.com' in email:
                    return email.split('@')[0]
                # Otherwise return the username part of the email
                return email.split('@')[0]
            elif name:
                # As a fallback, use the Git username (converted to lowercase with hyphens)
                return name.lower().replace(' ', '-')
    except Exception as e:
        logging.warning(f"Error getting GitHub username: {e}")
    
    # If all else fails, get the system username
    return getpass.getuser()

def get_user_info():
    """Get current user information for tracking."""
    try:
        # Use GitHub username instead of system username
        username = get_github_username()
        hostname = socket.gethostname()
        os_info = f"{platform.system()} {platform.release()}"
        return {
            "user": username,
            "hostname": hostname,
            "os": os_info
        }
    except Exception as e:
        logging.error(f"Error getting user info: {e}")
        return {"user": "unknown", "hostname": "unknown", "os": "unknown"}

def get_github_token():
    """Get GitHub token from environment variables."""
    # Try to get token from GITHUB_TOKEN env var first (for backward compatibility)
    token = os.environ.get('GITHUB_TOKEN')
    
    # If not found, try GITHUB_PAT which is the recommended name for the token
    if not token:
        token = os.environ.get('GITHUB_PAT')
    
    if not token:
        logging.warning("No GitHub token found. Set GITHUB_PAT in your .env file.")
        
    return token

def fetch_csv_from_github():
    """Fetch the installations CSV from the external GitHub repository using curl."""
    token = get_github_token()
    if not token:
        return None, None
    
    url = f"{GITHUB_API_BASE}/repos/{TRACKING_REPO_OWNER}/{TRACKING_REPO_NAME}/contents/{CSV_PATH}"
    
    try:
        # Prepare curl command
        curl_command = [
            "curl",
            "-s",  # silent
            "-H", "Accept: application/vnd.github.v3+json",
            "-H", f"Authorization: token {token}",
            url
        ]

        # Execute curl command
        result = subprocess.run(curl_command, capture_output=True, text=True)
        
        if result.returncode == 0:
            # Try to parse the JSON response
            try:
                response_json = json.loads(result.stdout)
                
                # Check if we have content
                if "content" in response_json:
                    content_encoded = response_json["content"]
                    content = base64.b64decode(content_encoded).decode('utf-8')
                    sha = response_json.get("sha")
                    return content, sha
                else:
                    # Did we get an error?
                    if "message" in response_json:
                        if response_json.get("message") == "Not Found":
                            logging.info(f"CSV file not found in tracking repository. It will be created.")
                            return "", None
                        else:
                            logging.error(f"GitHub API error: {response_json.get('message')}")
                            return None, None
            except json.JSONDecodeError:
                logging.error(f"Failed to parse JSON response from GitHub API")
                return None, None
        else:
            logging.error(f"Curl command failed: {result.stderr}")
            return None, None
    except Exception as e:
        logging.error(f"Error fetching CSV from GitHub with curl: {e}")
        return None, None

def parse_csv_data(csv_content):
    """Parse CSV content into a list of dictionaries."""
    if not csv_content:
        # Return empty list with headers for a new file
        return []
    
    try:
        reader = csv.DictReader(io.StringIO(csv_content))
        return list(reader)
    except Exception as e:
        logging.error(f"Error parsing CSV data: {e}")
        return []

def csv_to_string(data):
    """Convert CSV data to a string."""
    output = io.StringIO()
    
    if not data:
        # Just write headers for empty data
        writer = csv.writer(output)
        writer.writerow(['user', 'timestamp', 'status', 'hostname', 'os'])
    else:
        # Write headers and data rows
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
        
    return output.getvalue()

def update_csv_in_github(csv_content, file_sha, commit_message):
    """Update the CSV file in the GitHub repository using curl."""
    token = get_github_token()
    if not token:
        return False
    
    url = f"{GITHUB_API_BASE}/repos/{TRACKING_REPO_OWNER}/{TRACKING_REPO_NAME}/contents/{CSV_PATH}"
    
    # Encode content for GitHub API
    content_encoded = base64.b64encode(csv_content.encode('utf-8')).decode('utf-8')
    
    # Create JSON payload
    if file_sha:
        # Update existing file
        payload = {
            'message': commit_message,
            'content': content_encoded,
            'sha': file_sha
        }
    else:
        # Create new file
        payload = {
            'message': commit_message,
            'content': content_encoded
        }
    
    # Convert payload to JSON string
    payload_json = json.dumps(payload)
    
    try:
        # Prepare curl command for PUT request
        curl_command = [
            "curl",
            "-s",  # silent
            "-X", "PUT",
            "-H", "Accept: application/vnd.github.v3+json",
            "-H", f"Authorization: token {token}",
            "-H", "Content-Type: application/json",
            "-d", payload_json,
            url
        ]

        # Execute curl command
        result = subprocess.run(curl_command, capture_output=True, text=True)
        
        if result.returncode == 0:
            try:
                response_json = json.loads(result.stdout)
                if "content" in response_json:
                    logging.info(f"Successfully updated CSV in GitHub: {commit_message}")
                    return True
                else:
                    # Check for error message
                    if "message" in response_json:
                        logging.error(f"GitHub API error: {response_json.get('message')}")
                    else:
                        logging.error("Unknown error while updating CSV in GitHub")
                    return False
            except json.JSONDecodeError:
                logging.error(f"Failed to parse JSON response from GitHub API")
                return False
        else:
            logging.error(f"Curl command failed: {result.stderr}")
            return False
    except Exception as e:
        logging.error(f"Error updating CSV in GitHub with curl: {e}")
        return False

def update_installation_status(status):
    """Update installation status in the external tracking repository.
    
    Args:
        status (str): Either 'installed' or 'uninstalled'
    """
    user_info = get_user_info()
    username = user_info['user']
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Fetch current CSV content from GitHub
    csv_content, file_sha = fetch_csv_from_github()
    if csv_content is None:  # Error occurred
        logging.error("Failed to fetch tracking data from GitHub")
        return False
    
    # Parse CSV data
    data = parse_csv_data(csv_content)
    
    # Check if user already exists
    user_found = False
    for entry in data:
        if entry['user'] == username:
            # Update existing record
            entry['timestamp'] = now
            entry['status'] = status
            entry['hostname'] = user_info['hostname']
            entry['os'] = user_info['os']
            user_found = True
            break
    
    # If user not found, add new record
    if not user_found:
        if not data:
            # Create the first record with proper headers
            data = [{
                'user': username,
                'timestamp': now,
                'status': status,
                'hostname': user_info['hostname'],
                'os': user_info['os']
            }]
        else:
            data.append({
                'user': username,
                'timestamp': now,
                'status': status,
                'hostname': user_info['hostname'],
                'os': user_info['os']
            })
    
    # Convert data back to CSV string
    updated_csv = csv_to_string(data)
    
    # Update CSV in GitHub
    commit_msg = f"Update installation status: {username} {status}"
    return update_csv_in_github(updated_csv, file_sha, commit_msg)

def record_installation():
    """Record that a user has installed the hooks."""
    return update_installation_status('installed')

def record_uninstallation():
    """Record that a user has uninstalled the hooks."""
    return update_installation_status('uninstalled') 