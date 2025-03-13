#!/usr/bin/env python3
import os
import sys
import shutil
import platform
from pathlib import Path
import subprocess
import logging
from typing import Optional

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Builder:
    def __init__(self):
        self.os_type = platform.system().lower()
        self.project_root = Path(__file__).parent
        self.dist_dir = self.project_root / "dist"
        self.build_dir = self.project_root / "build"
        self.assets_dir = self.project_root / "src" / "assets"
        self.hooks_dir = self.project_root / "src" / "hooks"
        self.logo_path = self.assets_dir / "logo.png"
        self.main_script = self.project_root / "src" / "main.py"
        
        # Application details
        self.app_name = "Genie-Secrets"
        self.version = "1.0.0"
        self.author = "Your Name"
        self.description = "A PyQt-based Secret Scanner Application"

    def check_dependencies(self) -> bool:
        """Check if required build dependencies are installed."""
        try:
            import PyInstaller
            return True
        except ImportError:
            logger.error("PyInstaller not found. Installing required dependencies...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
                return True
            except subprocess.CalledProcessError:
                logger.error("Failed to install dependencies")
                return False

    def generate_spec_file(self) -> Path:
        """Generate optimized PyInstaller spec file."""
        spec_content = f"""# -*- mode: python ; coding: utf-8 -*-

import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect all hooks files
hooks_data = []
hooks_dir = '{self.project_root}/src/hooks'
for root, dirs, files in os.walk(hooks_dir):
    for file in files:
        source = os.path.join(root, file)
        target = os.path.join('hooks', os.path.relpath(source, hooks_dir))
        hooks_data.append((source, os.path.dirname(target)))

# Collect all PyQt6 modules
qt_modules = collect_submodules('PyQt6')
qt_data = collect_data_files('PyQt6')

a = Analysis(
    ['{self.main_script}'],
    pathex=['{self.project_root}'],
    binaries=[],
    datas=[
        ('{self.assets_dir}', 'assets'),
        *hooks_data,  # Include all hooks files with their directory structure
        *qt_data,  # Include all PyQt6 data files
    ],
    hiddenimports=[
        *qt_modules,  # Include all PyQt6 modules
        'PyQt6.QtWebEngineCore',
        'PyQt6.QtWebEngineWidgets',
        'PyQt6.QtWebChannel',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'cv2', 'PIL'],  # Exclude unnecessary packages
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Remove unnecessary files from the bundle
a.binaries = [x for x in a.binaries if not x[0].startswith('opengl32sw.dll')]
a.binaries = [x for x in a.binaries if not x[0].startswith('Qt6WebEngineCore.framework')]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

if '{self.os_type}' == 'darwin':
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name='{self.app_name}',
        debug=False,
        bootloader_ignore_signals=False,
        strip=True,  # Strip symbols for smaller size
        upx=True,  # Enable UPX compression
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon='{self.logo_path}'
    )
    
    # Optimize bundle creation
    app = BUNDLE(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        name='{self.app_name}.app',
        icon='{self.logo_path}',
        bundle_identifier=f'com.{self.app_name.lower()}',
        info_plist={{
            'NSHighResolutionCapable': True,
            'NSRequiresAquaSystemAppearance': False,
            'CFBundleShortVersionString': '{self.version}',
            'CFBundleVersion': '{self.version}',
            'CFBundleName': '{self.app_name}',
            'CFBundleDisplayName': '{self.app_name}',
            'CFBundleGetInfoString': '{self.description}',
            'CFBundleIdentifier': f'com.{self.app_name.lower()}',
            'NSAppTransportSecurity': {{'NSAllowsArbitraryLoads': True}},
        }}
    )
else:
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name='{self.app_name}',
        debug=False,
        bootloader_ignore_signals=False,
        strip=True,  # Strip symbols for smaller size
        upx=True,  # Enable UPX compression
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon='{self.logo_path}'
    )
"""
        spec_file = self.project_root / f"{self.app_name}.spec"
        spec_file.write_text(spec_content)
        return spec_file

    def build(self) -> Optional[Path]:
        """Build the executable with optimized settings."""
        try:
            if not self.check_dependencies():
                return None

            # Clean previous builds
            shutil.rmtree(self.dist_dir, ignore_errors=True)
            shutil.rmtree(self.build_dir, ignore_errors=True)

            # Generate optimized spec file
            spec_file = self.generate_spec_file()
            
            # Build using PyInstaller with optimized settings
            logger.info("Building executable with optimized settings...")
            
            # Install UPX if available (for better compression)
            try:
                if self.os_type == "darwin":
                    subprocess.run(["brew", "install", "upx"], check=False)
                elif self.os_type == "linux":
                    subprocess.run(["sudo", "apt-get", "install", "upx"], check=False)
            except Exception:
                logger.warning("UPX not installed. Continuing without UPX compression.")
            
            build_cmd = [
                sys.executable,
                "-OO",  # Optimize bytecode
                "-m",
                "PyInstaller",
                "--clean",
                "--noconfirm",
                "--log-level=WARN",
                str(spec_file)
            ]
            
            subprocess.run(build_cmd, check=True)

            # Get the path to the built executable
            if self.os_type == "darwin":
                executable_path = self.dist_dir / f"{self.app_name}.app"
            elif self.os_type == "windows":
                executable_path = self.dist_dir / f"{self.app_name}.exe"
            else:  # Linux
                executable_path = self.dist_dir / self.app_name

            if not executable_path.exists():
                logger.error(f"Build failed: Executable not found at {executable_path}")
                return None

            # Make hooks executable in the built package
            if self.os_type != "windows":
                hooks_dir = executable_path
                if self.os_type == "darwin":
                    hooks_dir = hooks_dir / "Contents" / "MacOS"
                hooks_dir = hooks_dir / "hooks"
                if hooks_dir.exists():
                    for hook in ['scan-repo', 'pre-commit', 'post-commit']:
                        hook_path = hooks_dir / hook
                        if hook_path.exists():
                            os.chmod(hook_path, 0o755)

            logger.info(f"Build successful! Executable created at: {executable_path}")
            return executable_path

        except Exception as e:
            logger.error(f"Build failed: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

def main():
    builder = Builder()
    executable_path = builder.build()
    
    if executable_path:
        logger.info("Build completed successfully!")
        sys.exit(0)
    else:
        logger.error("Build failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 