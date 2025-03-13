#!/usr/bin/env python3
import os
import sys
import shutil
import platform
from pathlib import Path
import subprocess
import logging
from typing import Optional
import PyInstaller.__main__

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Builder:
    def __init__(self):
        self.os_type = platform.system().lower()
        self.project_root = Path(__file__).parent
        self.dist_dir = self.project_root / "dist"
        self.build_dir = self.project_root / "build"
        self.src_dir = self.project_root / "src"
        self.hooks_dir = self.src_dir / "hooks"
        self.assets_dir = self.src_dir / "assets"
        self.logo_path = self.assets_dir / "logo.png"
        self.main_script = self.src_dir / "main.py"
        
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

    def clean_build_dirs(self):
        """Clean up previous build artifacts."""
        logger.info("Cleaning build directories...")
        for dir_path in [self.dist_dir, self.build_dir]:
            if dir_path.exists():
                shutil.rmtree(dir_path)

    def collect_data_files(self):
        """Collect all necessary data files."""
        data_files = []
        
        # Add hooks directory with proper relative paths
        for root, _, files in os.walk(self.hooks_dir):
            for file in files:
                full_path = os.path.join(root, file)
                # Calculate the relative path to maintain directory structure
                rel_dir = os.path.relpath(root, self.project_root)
                target_dir = os.path.join('hooks', os.path.relpath(root, self.hooks_dir))
                data_files.append((full_path, target_dir))

        # Add assets directory with proper relative paths
        for root, _, files in os.walk(self.assets_dir):
            for file in files:
                full_path = os.path.join(root, file)
                # Calculate the relative path to maintain directory structure
                rel_dir = os.path.relpath(root, self.project_root)
                target_dir = os.path.join('assets', os.path.relpath(root, self.assets_dir))
                data_files.append((full_path, target_dir))

        return data_files

    def generate_spec_file(self):
        """Generate PyInstaller spec file content."""
        data_files = self.collect_data_files()
        
        spec_content = f"""# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

block_cipher = None

# Collect all data files
data_files = {data_files}

# Collect Qt resources
qt_data_files = []
try:
    from PyQt6.QtCore import QLibraryInfo
    qt_path = QLibraryInfo.path(QLibraryInfo.LibraryPath.DataPath)
    resources_path = os.path.join(qt_path, "resources")
    translations_path = os.path.join(qt_path, "translations")
    
    # Add resources
    if os.path.exists(resources_path):
        for file in os.listdir(resources_path):
            if file.startswith('qtwebengine'):
                source = os.path.join(resources_path, file)
                qt_data_files.append((source, "resources"))
    
    # Add translations
    if os.path.exists(translations_path):
        for file in os.listdir(translations_path):
            if file.startswith('qtwebengine'):
                source = os.path.join(translations_path, file)
                qt_data_files.append((source, "translations"))
except Exception as e:
    print(f"Warning: Could not collect Qt resources: {{e}}")

a = Analysis(
    [os.path.join('{self.src_dir}', 'main.py')],
    pathex=['{self.project_root}'],
    binaries=[],
    datas=data_files + qt_data_files,
    hiddenimports=[
        'PyQt6.QtWebEngineCore',
        'PyQt6.QtWebEngineWidgets',
        'PyQt6.QtWebChannel',
        'PyQt6.QtNetwork',
        'PyQt6.sip',
        'PyQt6.QtPrintSupport'
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Add WebEngine resources for PyQt6
try:
    from PyQt6.QtWebEngineCore import QWebEngineUrlScheme
    import shutil
    import PyQt6
    
    qt_path = os.path.dirname(PyQt6.__file__)
    web_engine_path = os.path.join(qt_path, "Qt6", "resources")
    
    if os.path.exists(web_engine_path):
        web_engine_files = []
        for filename in os.listdir(web_engine_path):
            if filename.startswith("qtwebengine"):
                source = os.path.join(web_engine_path, filename)
                web_engine_files.append((source, "."))
        a.datas.extend(web_engine_files)
except ImportError:
    pass

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

if sys.platform == 'darwin':
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name='Genie-Secrets',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=True,  # Set to True temporarily for debugging
        codesign_identity=None,
        entitlements_file=None,
        icon=os.path.join('{self.assets_dir}', 'logo.png'),
    )
    
    # Create .app bundle for macOS
    app = BUNDLE(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        name='Genie-Secrets.app',
        icon=os.path.join('{self.assets_dir}', 'logo.png'),
        bundle_identifier='com.genie.secrets',
        info_plist={{
            'CFBundleShortVersionString': '1.0.0',
            'CFBundleVersion': '1.0.0',
            'NSHighResolutionCapable': True,
            'LSBackgroundOnly': False,
            'NSRequiresAquaSystemAppearance': False,
            'NSPrincipalClass': 'NSApplication',
            'NSAppleScriptEnabled': False,
            'CFBundleDisplayName': 'Genie-Secrets',
            'CFBundleName': 'Genie-Secrets',
            'NSAppTransportSecurity': {{
                'NSAllowsArbitraryLoads': True
            }},
        }},
    )
else:
    # For Windows and Linux
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name='Genie-Secrets',
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=True,  # Set to True temporarily for debugging
        disable_windowed_traceback=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=os.path.join('{self.assets_dir}', 'logo.png'),
    )
"""
        spec_file = os.path.join(self.project_root, f"{self.app_name}.spec")
        with open(spec_file, 'w') as f:
            f.write(spec_content)
        return spec_file

    def build(self) -> Optional[Path]:
        """Build the executable."""
        try:
            if not self.check_dependencies():
                return None

            # Clean previous builds
            self.clean_build_dirs()

            # Generate spec file
            spec_file = self.generate_spec_file()

            # Build using PyInstaller
            logger.info("Building executable...")
            PyInstaller.__main__.run([
                '--clean',
                '--noconfirm',
                str(spec_file)
            ])

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

            logger.info(f"Build successful! Executable created at: {executable_path}")
            return executable_path

        except Exception as e:
            logger.error(f"Build failed: {str(e)}")
            return None

def main():
    builder = Builder()
    executable_path = builder.build()
    
    if executable_path:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main() 