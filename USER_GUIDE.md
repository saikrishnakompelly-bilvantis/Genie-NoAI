# SecretGenie User Guide

**SecretGenie** is a powerful secret scanning tool that helps prevent accidental commits of sensitive information like API keys, passwords, and credentials to your Git repositories. It automatically scans your code during commits and provides detailed reports.

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Dependencies](#dependencies)
3. [Installation](#installation)
4. [Usage](#usage)
5. [Troubleshooting](#troubleshooting)

## System Requirements

### Minimum Requirements
- **Operating System**: Windows 10+, macOS 10.14+, or Linux (Ubuntu 18.04+, CentOS 7+)
- **Python**: 3.9 or higher
- **Git**: 2.20 or higher
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 500MB free space

### Recommended Requirements
- **RAM**: 8GB or higher
- **Storage**: 1GB free space
- **Network**: Internet connection for installation tracking

## Dependencies

### Required Dependencies

#### 1. Python 3.9+
SecretGenie is built with Python and requires version 3.9 or higher.

**Check your Python version:**
```bash
python --version
# or
python3 --version
```

**Install Python:**
- **Windows**: Download from [python.org](https://www.python.org/downloads/)
- **macOS**: Use Homebrew: `brew install python@3.11`
- **Linux**: `sudo apt install python3` (Ubuntu/Debian) or `sudo yum install python3` (CentOS/RHEL)

#### 2. Git 2.20+
SecretGenie integrates with Git to scan commits and manage hooks.

**Check your Git version:**
```bash
git --version
```

**Install Git:**
- **Windows**: Download from [git-scm.com](https://git-scm.com/download/win)
- **macOS**: Use Homebrew: `brew install git`
- **Linux**: `sudo apt install git` (Ubuntu/Debian) or `sudo yum install git` (CentOS/RHEL)

#### 3. Git Configuration
Before using SecretGenie, ensure Git is properly configured:

```bash
# Set your name
git config --global user.name "Your Name"

# Set your email
git config --global user.email "your.email@example.com"
```

### Optional Dependencies

#### PowerShell (Windows)
For enhanced CLI experience on Windows, PowerShell 5.1+ is recommended.

#### Bash (Linux/macOS)
For enhanced CLI experience on Unix-like systems, ensure bash is available.

## Installation

### Method 1: Using Built Executables (Recommended)

#### Windows
1. Download the latest SecretGenie release
2. Extract the ZIP file to your desired location
3. You'll find:
   - `SecretGenie.exe` - Main application
   - `secretgenie-cli.bat` - Command-line wrapper
   - `secretgenie-cli.ps1` - PowerShell wrapper

#### macOS
1. Download the latest SecretGenie release
2. Extract the ZIP file to your desired location
3. You'll find:
   - `SecretGenie.app` - Main application bundle
   - `secretgenie-cli.sh` - Command-line wrapper

#### Linux
1. Download the latest SecretGenie release
2. Extract the TAR file to your desired location
3. You'll find:
   - `SecretGenie` - Main executable
   - `secretgenie-cli.sh` - Command-line wrapper

### Method 2: Building from Source

#### Prerequisites
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install PyInstaller for building
pip install pyinstaller
```

#### Build Commands
```bash
# Windows
build.bat

# macOS/Linux
./build.sh
```

## Usage

### GUI Mode

#### Windows
```bash
# Double-click the executable
SecretGenie.exe

# Or run from command line
SecretGenie.exe
```

#### macOS
```bash
# Double-click the app bundle
open SecretGenie.app

# Or run from command line
./SecretGenie.app/Contents/MacOS/SecretGenie
```

#### Linux
```bash
# Run the executable
./SecretGenie
```

### Command-Line Interface (CLI)

SecretGenie supports command-line operations for automation and headless environments.

#### Basic CLI Commands

**Install hooks:**
```bash
# Windows
SecretGenie.exe /install
secretgenie-cli.bat /install
.\secretgenie-cli.ps1 /install

# macOS
./SecretGenie.app/Contents/MacOS/SecretGenie /install
./secretgenie-cli.sh /install

# Linux
./SecretGenie /install
./secretgenie-cli.sh /install
```

**Uninstall hooks:**
```bash
# Windows
SecretGenie.exe /uninstall
secretgenie-cli.bat /uninstall
.\secretgenie-cli.ps1 /uninstall

# macOS
./SecretGenie.app/Contents/MacOS/SecretGenie /uninstall
./secretgenie-cli.sh /uninstall

# Linux
./SecretGenie /uninstall
./secretgenie-cli.sh /uninstall
```

**Show help:**
```bash
# All platforms
SecretGenie.exe --help
./SecretGenie --help
```

#### CLI Options

| Option | Description | Example |
|--------|-------------|---------|
| `/install` or `--install` | Install Git hooks | `SecretGenie.exe /install` |
| `/uninstall` or `--uninstall` | Uninstall Git hooks | `SecretGenie.exe /uninstall` |
| `--help` or `-h` | Show help information | `SecretGenie.exe --help` |

#### CLI Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Operation completed successfully |
| `1` | Operation failed (check console output) |

### Step-by-Step Usage Guide

#### First-Time Setup

1. **Install Dependencies**
   ```bash
   # Verify Python
   python --version  # Should be 3.9+
   
   # Verify Git
   git --version     # Should be 2.20+
   
   # Configure Git (if not done)
   git config --global user.name "Your Name"
   git config --global user.email "your.email@example.com"
   ```

2. **Install SecretGenie Hooks**
   ```bash
   # Using GUI
   # Double-click SecretGenie.exe (Windows) or SecretGenie.app (macOS) or ./SecretGenie (Linux)
   # Click "Install Hooks" button
   
   # Using CLI
   SecretGenie.exe /install
   ```

3. **Verify Installation**
   ```bash
   # Check if hooks are installed
   git config --global --get core.hooksPath
   # Should return: ~/.genie/hooks
   
   # Check if aliases are set
   git config --global --get alias.scan-repo
   git config --global --get alias.scan-config
   ```

#### Daily Usage

 **Normal Git Workflow**
   ```bash
   # Make changes to your code
   git add .
   git commit -m "Your commit message"
   git push
   ```
   
   SecretGenie will automatically:
   - Scan your changes for secrets
   - Prompt for justification if secrets are found
   - Generate reports


#### Configuration Management

1. **Access Configuration Interface**
   ```bash
   git scan-config
   ```

2. **Customize Scan Behavior**
   - Choose scan modes (changed files only, entire repository, or both)
   - Set up custom patterns for secret detection
   - Configure reporting options



## Troubleshooting

### Common Issues

#### 1. "Git Not Found" Error
**Problem**: SecretGenie can't find Git installation.

**Solution**:
```bash
# Verify Git is installed
git --version

# Add Git to PATH (Windows)
# Add Git installation directory to system PATH

# Install Git if missing
# Windows: Download from git-scm.com
# macOS: brew install git
# Linux: sudo apt install git
```

#### 2. "Python Not Found" Error
**Problem**: SecretGenie can't find Python installation.

**Solution**:
```bash
# Verify Python is installed
python --version

# Install Python if missing
# Windows: Download from python.org
# macOS: brew install python@3.11
# Linux: sudo apt install python3
```

#### 3. "Git Configuration Missing" Error
**Problem**: Git user name or email not configured.

**Solution**:
```bash
# Set Git configuration
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

#### 4. "Hooks Already Installed" Message
**Problem**: Trying to install hooks when they're already installed.

**Solution**:
```bash
# This is not an error - hooks are already working
# To reinstall, uninstall first:
SecretGenie.exe /uninstall
SecretGenie.exe /install
```

#### 5. Permission Denied Errors
**Problem**: Cannot write to hooks directory or create files.

**Solution**:
```bash
# Check directory permissions
ls -la ~/.genie/

# Fix permissions if needed
chmod 755 ~/.genie/hooks/
chmod 644 ~/.genie/config
```


### Getting Help

1. **Verify dependencies** are installed and configured
2. **Try CLI mode** for better error messages
3. **Check file permissions** in the `.genie` directory

### Version Compatibility

| SecretGenie Version | Python | Git | OS Support |
|---------------------|--------|-----|------------|
| 1.0.0+ | 3.9+ | 2.20+ | Windows 10+, macOS 10.14+, Linux |

---
