# Genie - Secret Scanning Tool

A powerful desktop application designed to help developers scan Git repositories for secrets, API keys, credentials, and other sensitive information that should not be committed to version control.

## Overview

Genie is a cross-platform security tool that helps prevent accidental exposure of sensitive information in your code repositories. It operates in two main ways:

1. **Git Hooks Integration**: Installs pre-commit and post-commit hooks to automatically scan for secrets before they are committed to your repositories
2. **Manual Repository Scanning**: Allows on-demand scanning of entire repositories to identify existing secrets

## Key Features

- **Automatic Secret Detection**: Uses pattern matching and entropy analysis to detect various types of secrets:
  - API keys and tokens
  - Database credentials
  - Private keys
  - Authentication tokens
  - Environment variables with sensitive data
  - And more

- **Git Hooks Integration**: 
  - Pre-commit hook prevents committing secrets
  - Post-commit hook provides additional verification
  - Easy installation/uninstallation directly from the UI

- **Interactive Reports**: 
  - Detailed HTML reports of found secrets
  - Ability to review and justify secrets when needed
  - Historical report storage for audit purposes

- **User-Friendly Interface**:
  - Simple and intuitive UI
  - Clear visualization of detected secrets
  - Easy hook management

## Installation

### Using the Pre-built Executable

1. Download the latest release of Genie
2. Run the executable file:
   - Windows: `Genie.exe`
   - macOS: `Genie.app`
   - Linux: `Genie`

A desktop shortcut will be automatically created on first launch.

### Building from Source

1. Clone this repository
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the build script:
   ```bash
   # Windows
   build.bat
   
   # macOS/Linux
   # Make sure the script is executable
   chmod +x build.sh
   ./build.sh
   ```
4. The executable will be created in the `dist` directory

### Building for HSBC Environments

If you experience an empty screen issue in HSBC environments, use the special HSBC build option:

```bash
# Windows
build.bat hsbc

# macOS/Linux
./build.sh hsbc
```

This creates a special version (`Genie-HSBC.exe`) that uses native UI components instead of web-based rendering, making it compatible with environments that restrict web content rendering.

## Usage

### First Launch

When you first launch Genie, you'll see a welcome screen with an option to install Git hooks.

### Installing Git Hooks

1. Open a Git repository in Genie
2. Click the "Install Hooks" button
3. Genie will install pre-commit and post-commit hooks in the selected repository

### Running Manual Scans

1. Open Genie
2. Select a repository to scan
3. Click "Scan Repository"
4. Review the results in the generated HTML report

### During Git Commits

Once hooks are installed:

1. When you attempt to commit code, the pre-commit hook will automatically scan for secrets
2. If secrets are detected, you'll be prompted to review them
3. You can choose to:
   - Abort the commit to fix the issues
   - Provide justification for detected secrets and proceed with the commit
   - Skip the checks (not recommended)

### Managing Reports

All scan reports are stored in the `.commit-reports` directory within the Git hooks folder. You can view past reports from the Genie interface.

## How It Works

Genie uses several techniques to detect potential secrets:

1. **Pattern Matching**: Searches for common patterns used in secrets and credentials
2. **Entropy Analysis**: Calculates the randomness of strings to identify high-entropy values typical of secrets
3. **Variable Name Inspection**: Identifies variables with names suggesting they contain sensitive information

## System Requirements

- **Windows**: Windows 10 or later
- **macOS**: macOS 10.13 or later
- **Linux**: Most modern distributions supported
- **Git**: Git must be installed and accessible from the command line
- **Disk Space**: Approximately 100MB

## Troubleshooting

### Common Issues

- **Hooks Not Working**: Ensure git is properly installed and configured with user.name and user.email
- **Permission Denied**: Try running Genie with administrator/root privileges
- **Application Not Starting**: Verify that your system meets the minimum requirements

### Empty Screen in HSBC Environments

If you encounter an empty screen when running Genie in an HSBC environment:

1. **Use the HSBC Build**: Download or build the "HSBC" version using `build.bat hsbc` or `./build.sh hsbc`

2. **Manual Fallback Configuration**: If you only have the standard version, create a file named `.genie_config` in your home directory with the following content:
   ```
   USE_NATIVE_UI=true
   ```

3. **Command-Line Arguments**: Run the application with the `--native-ui` flag:
   ```
   Genie.exe --native-ui
   ```

4. **Environment Variable**: Before launching, set this environment variable:
   ```
   # Windows
   set GENIE_USE_NATIVE_UI=1
   
   # macOS/Linux
   export GENIE_USE_NATIVE_UI=1
   ```

### Logs

Logs are stored in:
- Windows: `%USERPROFILE%\.genie\logs`
- macOS/Linux: `~/.genie/logs`

## Privacy

Genie operates entirely locally on your system. No data is sent to external servers, and all scanning is performed on your local machine.

## License

This project is proprietary software. Unauthorized distribution is prohibited.

## Support

For support, bug reports, or feature requests, please contact your system administrator or the development team.
