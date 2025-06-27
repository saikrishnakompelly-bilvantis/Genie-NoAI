# Genie Secret Scanner

Genie is a powerful tool designed to scan your code repositories for secrets and sensitive information that may have been accidentally committed. It helps prevent security breaches by identifying potentially leaked credentials, API keys, tokens, and other sensitive information.

## Features

- **Pre-commit and Pre-push Hooks**: Automatically scan your code before committing or pushing changes to detect secrets
- **Repository Scanning**: Scan your entire repository for secrets
- **Diff Scanning**: Scan only the changes to be pushed
- **Configurable Exclusions**: Exclude specific file types and directories from scanning
- **HTML Reports**: Generate detailed HTML reports of found secrets

## Installation

### GUI Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/Genie-NoAI.git
   ```

2. Run the Genie application:
   ```
   cd Genie-NoAI
   python src/main.py
   ```

3. Use the GUI to install Git hooks in your project repositories.

### Command-Line Installation

Genie supports command-line installation and uninstallation without requiring GUI interaction. This is useful for automated deployments, CI/CD pipelines, or when running on headless systems.

#### Direct Command-Line Usage

**Install hooks:**
```bash
# From source
python src/main.py /install

# From built executable (Windows)
Genie.exe /install

# From built executable (macOS/Linux)
./Genie /install
```

**Uninstall hooks:**
```bash
# From source
python src/main.py /uninstall

# From built executable (Windows)
Genie.exe /uninstall

# From built executable (macOS/Linux)
./Genie /uninstall
```

#### Using Wrapper Scripts

For built executables, you can also use the provided wrapper scripts that ensure console output is visible:

**Windows:**
```batch
# Using batch file
genie-cli.bat /install
genie-cli.bat /uninstall

# Using PowerShell script
.\genie-cli.ps1 /install
.\genie-cli.ps1 /uninstall
```

**macOS/Linux:**
```bash
# Using shell script
./genie-cli.sh /install
./genie-cli.sh /uninstall
```

#### Command-Line Options

- `/install` or `--install`: Install Genie Git hooks
- `/uninstall` or `--uninstall`: Uninstall Genie Git hooks
- `--help`: Show help information

#### Prerequisites for Command-Line Installation

Before using command-line installation, ensure:

1. **Git is installed** and available in your PATH
2. **Git user configuration** is set:
   ```bash
   git config --global user.name "Your Name"
   git config --global user.email "your.email@example.com"
   ```

#### Exit Codes

- `0`: Operation completed successfully
- `1`: Operation failed (check console output for details)

## Configuration

### Scan Configuration

Genie provides a configuration interface that allows you to customize how scanning works:

1. **Scan Mode**: Choose between scanning both changed files and repository, only changed files, or only the repository.
2. **Exclusions**: Configure files and directories to exclude from scanning.

To access the configuration:

```bash
git scan-config
```

### Exclusions Configuration

Genie supports customizing which files and directories are excluded from scanning via a YAML configuration file named `exclusions.yaml`.

#### Default Location

The global exclusions file is located at:
```
~/.genie/exclusions.yaml
```

You can also create a local exclusions file in your repository:
```
your-repo/exclusions.yaml
```

#### Exclusions File Format

The exclusions file uses YAML format and has three main sections:

```yaml
# File extensions to exclude
file_extensions:
  - "*.jar"    # Java Archive files
  - "*.png"    # Image files
  # ... more extensions

# Directories to exclude
directories:
  - "**/node_modules/**"     # JavaScript dependencies
  - "**/build/**"            # Build output
  # ... more directories

# Additional exclusions
additional_exclusions:
  - "**/.git/**"             # Git internal directory
  # ... more patterns
```

#### Patterns

Patterns use glob syntax:
- `*` matches any sequence of non-path-separator characters
- `**` matches any sequence of characters, including path separators
- `?` matches any single non-path-separator character
- `[seq]` matches any character in seq
- `[!seq]` matches any character not in seq

#### Example Exclusions

The default exclusions include:

1. **Compiled/Packaged Artifacts**:
   - `.jar`, `.war`, `.ear`, `.pyc`, `.class` files

2. **Log Files**:
   - `.log`, `.out` files

3. **Temporary Files and Directories**:
   - `.tmp` files, `tmp/` and `temp/` directories, `__pycache__/`

4. **IDE and Editor Files**:
   - `.idea/`, `.vscode/`, etc.

5. **Package Management Directories**:
   - `node_modules/`, `vendor/`, etc.

6. **Media and Documentation**:
   - `.png`, `.jpg`, `.pdf`, `.md` files

#### Editing Exclusions

You can edit the exclusions file directly using a text editor or via the scan configuration interface:

```bash
git scan-config
```

Then click on the "Exclusions" tab and use the "Edit Exclusions" button.

## Usage

### Scanning a Repository

To scan an entire repository:

```bash
git scan-repo
```

### Pre-push Scanning

Once the Git hooks are installed, Genie will automatically scan your code before pushing changes to a remote repository.

### Configuration Interface

Launch the configuration interface:

```bash
git scan-config
```

## Troubleshooting

If you encounter issues with the scanner:

1. Check that Git hooks are properly installed
2. Verify that your exclusions configuration is valid YAML
3. Look for error messages in the console output

## License

Genie is licensed under the MIT License - see the LICENSE file for details.
