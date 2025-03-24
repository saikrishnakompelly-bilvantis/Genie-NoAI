# Genie - Secret Scanning Tool

A desktop application for scanning Git repositories for secrets and credentials.

## Building the Executable

1. First, install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Make sure you have an icon file at `src/assets/logo.ico`. If you don't have one, you can convert your PNG logo to ICO format using an online converter or image editing software.

3. Build the executable using PyInstaller:
```bash
pyinstaller Genie.spec
```

The executable will be created in the `dist` directory.

## Running the Application

1. Navigate to the `dist` directory
2. Run the `Genie.exe` file

## Features

- Automatic Git hooks installation
- Secret scanning during commits
- HTML report generation
- User-friendly interface
- Cross-platform compatibility

## Requirements

- Windows 10 or later
- Git installed on the system
- No Python installation required (bundled in executable)

## Troubleshooting

If you encounter any issues:

1. Make sure Git is installed and accessible from the command line
2. Run the application as administrator if you encounter permission issues
3. Check the application logs in `%USERPROFILE%\.genie\logs` for detailed error messages

## Support

For support or bug reports, please contact your system administrator or the development team.
