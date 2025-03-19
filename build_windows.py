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
 
class WindowsBuilder:
    def __init__(self):
        if platform.system().lower() != 'windows':
            raise RuntimeError("This script is intended to be run on Windows only")
            
        self.project_root = Path(__file__).resolve().parent
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
        required_packages = ['PyInstaller', 'PyQt6', 'PyQt6-WebEngine', 'Pillow', 'pywin32', 'winshell']
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package.replace('-', '_').split('==')[0])
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            logger.error(f"Missing dependencies: {', '.join(missing_packages)}")
            logger.info("Installing required dependencies...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_packages)
                return True
            except subprocess.CalledProcessError:
                logger.error("Failed to install dependencies")
                return False
        
        return True
 
    def clean_build_dirs(self):
        """Clean up previous build artifacts."""
        logger.info("Cleaning build directories...")
        for dir_path in [self.dist_dir, self.build_dir]:
            if dir_path.exists():
                shutil.rmtree(dir_path)
        
        # Create directories if they don't exist
        os.makedirs(self.dist_dir, exist_ok=True)
        os.makedirs(self.build_dir, exist_ok=True)
 
    def collect_data_files(self):
        """Collect all necessary data files."""
        data_files = []
        
        # Add hooks directory with proper relative paths
        if self.hooks_dir.exists():
            for root, _, files in os.walk(self.hooks_dir):
                for file in files:
                    full_path = Path(root) / file
                    # Calculate the relative path to maintain directory structure
                    target_dir = Path('hooks') / Path(root).relative_to(self.hooks_dir)
                    data_files.append((str(full_path), str(target_dir)))
 
        # Add assets directory with proper relative paths
        if self.assets_dir.exists():
            for root, _, files in os.walk(self.assets_dir):
                for file in files:
                    full_path = Path(root) / file
                    # Calculate the relative path to maintain directory structure
                    target_dir = Path('assets') / Path(root).relative_to(self.assets_dir)
                    data_files.append((str(full_path), str(target_dir)))
 
        return data_files
 
    def generate_spec_file(self):
        """Generate PyInstaller spec file content."""
        data_files = self.collect_data_files()
        
        # Convert version string to comma-separated integers for Windows version info
        version_parts = [int(x) for x in self.version.split('.')]
        while len(version_parts) < 4:
            version_parts.append(0)
        version_str = ', '.join(str(x) for x in version_parts)
        
        spec_content = f"""# -*- mode: python ; coding: utf-8 -*-
 
import sys
import os
from pathlib import Path
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
    plugins_path = QLibraryInfo.path(QLibraryInfo.LibraryPath.PluginsPath)
    
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
                
    # Add necessary plugins
    plugin_dirs = ['platforms', 'styles', 'webenginecore', 'imageformats']
    for plugin_dir in plugin_dirs:
        plugin_path = os.path.join(plugins_path, plugin_dir)
        if os.path.exists(plugin_path):
            for file in os.listdir(plugin_path):
                if file.endswith('.dll'):
                    source = os.path.join(plugin_path, file)
                    qt_data_files.append((source, os.path.join('PyQt6', 'Qt6', plugin_dir)))
except Exception as e:
    print(f"Warning: Could not collect Qt resources: {{e}}")
 
a = Analysis(
    [str(Path(r'{self.src_dir}') / 'main.py')],
    pathex=[str(Path(r'{self.project_root}'))],
    binaries=[],
    datas=data_files + qt_data_files,
    hiddenimports=[
        'PyQt6.QtWebEngineCore',
        'PyQt6.QtWebEngineWidgets',
        'PyQt6.QtWebChannel',
        'PyQt6.QtNetwork',
        'PyQt6.sip',
        'PyQt6.QtPrintSupport',
        'PyQt6.QtWidgets',
        'PyQt6.QtGui',
        'PyQt6.QtCore'
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
 
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='{self.app_name}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Set to False for Windows GUI application
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(Path(r'{self.assets_dir}') / 'logo.png'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='{self.app_name}',
)
"""
        spec_file = self.project_root / f"{self.app_name}_windows.spec"
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

            # Run PyInstaller
            logger.info("Building executable...")
            PyInstaller.__main__.run([
                '--clean',
                '--noconfirm',
                str(spec_file)
            ])

            # Get the path to the built executable
            executable_path = self.dist_dir / self.app_name / f"{self.app_name}.exe"

            if not executable_path.exists():
                logger.error(f"Build failed: Executable not found at {executable_path}")
                return None

            logger.info(f"Build successful! Executable created at: {executable_path}")
            return executable_path

        except Exception as e:
            logger.error(f"Build failed: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None
    
def main():
    try:
        # Create log directory if it doesn't exist
        log_dir = Path(os.path.expanduser("~")) / ".genie"
        os.makedirs(log_dir, exist_ok=True)

        # Setup file handler for logging
        file_handler = logging.FileHandler(log_dir / "genie.log")
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(file_handler)

        if platform.system().lower() != 'windows':
            logger.error("This script must be run on Windows")
            sys.exit(1)
            
        builder = WindowsBuilder()
        executable_path = builder.build()
        
        if executable_path:
            # Create a shortcut on the desktop
            try:
                import winshell
                from win32com.client import Dispatch
                
                desktop = winshell.desktop()
                shortcut_path = Path(desktop) / f"{builder.app_name}.lnk"
                
                shell = Dispatch('WScript.Shell')
                shortcut = shell.CreateShortCut(str(shortcut_path))
                shortcut.Targetpath = str(executable_path)
                shortcut.WorkingDirectory = str(executable_path.parent)
                shortcut.IconLocation = str(executable_path)
                shortcut.save()
                
                logger.info(f"Created desktop shortcut at: {shortcut_path}")
            except Exception as e:
                logger.warning(f"Failed to create desktop shortcut: {e}")
            
            sys.exit(0)
        else:
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)
 
if __name__ == "__main__":
    main()