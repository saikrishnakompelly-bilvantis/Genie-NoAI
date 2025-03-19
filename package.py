#!/usr/bin/env python3
import os
import sys
import shutil
import platform
from pathlib import Path
import subprocess
import logging
from typing import Optional
import zipfile

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Packager:
    def __init__(self):
        self.os_type = platform.system().lower()
        self.project_root = Path(__file__).resolve().parent
        self.dist_dir = self.project_root / "dist"
        self.package_dir = self.project_root / "package"
        self.app_name = "Genie-Secrets"
        
    def clean_directories(self):
        """Clean up previous package directories."""
        logger.info("Cleaning up previous package directories...")
        shutil.rmtree(self.package_dir, ignore_errors=True)
        os.makedirs(self.package_dir, exist_ok=True)

    def build_application(self) -> Optional[Path]:
        """Build the application using the appropriate build script."""
        logger.info(f"Building application for {self.os_type}...")
        try:
            if self.os_type == "windows":
                build_script = self.project_root / "build_windows.py"
            else:
                build_script = self.project_root / "build.py"
                
            subprocess.check_call([sys.executable, str(build_script)])
            
            # Get the path to the built executable
            if self.os_type == "darwin":
                executable_path = self.dist_dir / f"{self.app_name}.app"
            elif self.os_type == "windows":
                executable_path = self.dist_dir / self.app_name / f"{self.app_name}.exe"
            else:  # Linux
                executable_path = self.dist_dir / self.app_name

            if not executable_path.exists():
                logger.error(f"Build failed: Executable not found at {executable_path}")
                return None

            return executable_path
        except Exception as e:
            logger.error(f"Build failed: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    def create_readme(self):
        """Create README file with installation and usage instructions."""
        readme_content = f"""# Genie-Secrets - Secret Scanner Application

A powerful secret scanning tool for Git repositories with an intuitive GUI.

## Installation

1. Extract the contents of this package
2. Run the application:
   - Windows: Double-click `{self.app_name}.exe`
   - macOS: Double-click `{self.app_name}.app`
   - Linux: Run `./{self.app_name}` from terminal

## First Run

On first run, the application will:
1. Create a desktop shortcut automatically
2. Ask to install Git hooks for automatic scanning

## Features

- GUI-based secret scanning
- Automatic Git hooks integration
- HTML report generation
- Desktop shortcut creation
- Cross-platform support

## Requirements

- Git installed and configured
- Write permissions to home directory
- (Linux only) X11 or Wayland

## Support

For issues or questions, please visit the repository or contact support.

## License

Copyright (c) 2024. All rights reserved.
"""
        readme_path = self.package_dir / "README.md"
        readme_path.write_text(readme_content)

    def package_application(self, executable_path: Path) -> Optional[Path]:
        """Package the application into a zip file."""
        try:
            # Copy executable and assets
            if self.os_type == "darwin":
                # For macOS, copy the entire .app bundle
                shutil.copytree(executable_path, self.package_dir / executable_path.name)
            elif self.os_type == "windows":
                # For Windows, copy the entire directory
                shutil.copytree(executable_path.parent, self.package_dir / self.app_name)
            else:
                # For Linux, copy the executable
                shutil.copy2(executable_path, self.package_dir)

            # Create README
            self.create_readme()

            # Create zip file
            zip_name = f"{self.app_name}-{self.os_type}.zip"
            zip_path = self.project_root / zip_name
            
            # Remove existing zip if it exists
            if zip_path.exists():
                os.remove(zip_path)
            
            logger.info(f"Creating zip file: {zip_path}")
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, _, files in os.walk(self.package_dir):
                    for file in files:
                        file_path = Path(root) / file
                        arcname = file_path.relative_to(self.package_dir)
                        zipf.write(file_path, arcname)

            logger.info(f"Package created successfully at: {zip_path}")
            return zip_path

        except Exception as e:
            logger.error(f"Packaging failed: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    def package(self) -> bool:
        """Run the complete packaging process."""
        try:
            self.clean_directories()
            executable_path = self.build_application()
            if not executable_path:
                return False

            zip_path = self.package_application(executable_path)
            if not zip_path:
                return False

            logger.info(f"""
Package created successfully!
Location: {zip_path}

The package includes:
1. Executable application
2. README with installation instructions
3. All necessary assets and dependencies

To distribute:
1. Share the {zip_path.name} file
2. Users just need to extract and run the application
3. First-run setup will handle everything else automatically
""")
            return True

        except Exception as e:
            logger.error(f"Packaging process failed: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False

def main():
    try:
        # Create log directory if it doesn't exist
        log_dir = Path(os.path.expanduser("~")) / ".genie"
        os.makedirs(log_dir, exist_ok=True)

        # Setup file handler for logging
        file_handler = logging.FileHandler(log_dir / "genie_package.log")
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(file_handler)
        
        packager = Packager()
        success = packager.package()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    main() 