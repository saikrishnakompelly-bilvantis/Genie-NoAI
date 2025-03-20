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
import time
import psutil
import ctypes
from ctypes import wintypes

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def kill_processes_using_dlls(directory: Path):
    """Kill processes that are using DLLs in the specified directory."""
    try:
        # Kill any Python processes first
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if 'python' in proc.info['name'].lower():
                    logger.info(f"Killing Python process {proc.info['name']} (PID: {proc.info['pid']})")
                    proc.kill()
                    time.sleep(0.5)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

        # Then kill processes using DLLs
        for proc in psutil.process_iter(['pid', 'name', 'open_files']):
            try:
                if proc.info['open_files']:
                    for file in proc.info['open_files']:
                        if str(directory) in file:
                            logger.info(f"Killing process {proc.info['name']} (PID: {proc.info['pid']})")
                            proc.kill()
                            time.sleep(0.5)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

        # Additional wait to ensure processes are terminated
        time.sleep(1)
    except Exception as e:
        logger.warning(f"Failed to kill processes: {e}")

def force_delete_file(file_path: Path, max_retries: int = 3):
    """Force delete a file using Windows API with retries."""
    for attempt in range(max_retries):
        try:
            # Convert path to Windows format
            path = str(file_path).replace('/', '\\')
            # Get handle to file
            handle = ctypes.windll.kernel32.CreateFileW(
                path,
                wintypes.DWORD(0x80000000),  # GENERIC_READ
                0,  # No sharing
                None,
                wintypes.DWORD(3),  # OPEN_EXISTING
                wintypes.DWORD(0x02000000),  # FILE_FLAG_DELETE_ON_CLOSE
                None
            )
            if handle != -1:
                ctypes.windll.kernel32.CloseHandle(handle)
                return True
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1} failed to force delete {file_path}: {e}")
            time.sleep(0.5)  # Wait before retry
    return False

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
        required_packages = [
            'PyInstaller',
            'PySide6',
            'PySide6-WebEngine',
            'Pillow',
            'pywin32',
            'winshell',
            'psutil'
        ]
        missing_packages = []
        
        for package in required_packages:
            try:
                # Convert package name to import name
                import_name = package.replace('-', '_').split('==')[0]
                if import_name == 'PySide6_WebEngine':
                    import_name = 'PySide6.QtWebEngineWidgets'
                __import__(import_name)
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

    def get_qt_paths(self):
        """Get Qt installation paths."""
        try:
            import PySide6
            qt_path = os.path.dirname(PySide6.__file__)
            qt_plugins_path = os.path.join(qt_path, "Qt6", "plugins")
            qt_translations_path = os.path.join(qt_path, "Qt6", "translations")
            qt_resources_path = os.path.join(qt_path, "Qt6", "resources")
            return {
                'qt_path': qt_path,
                'plugins_path': qt_plugins_path,
                'translations_path': qt_translations_path,
                'resources_path': qt_resources_path
            }
        except Exception as e:
            logger.error(f"Failed to get Qt paths: {e}")
            return None
 
    def clean_build_dirs(self):
        """Clean up previous build artifacts."""
        logger.info("Cleaning build directories...")
        
        # Kill any processes using DLLs in the dist directory
        if self.dist_dir.exists():
            kill_processes_using_dlls(self.dist_dir)
            time.sleep(2)  # Give more time for processes to terminate
        
        def remove_readonly(func, path, _):
            """Clear the readonly bit and reattempt the removal."""
            try:
                # Clear the readonly bit
                os.chmod(path, 0o777)
                func(path)
            except Exception as e:
                logger.warning(f"Failed to remove {path}: {e}")
                # Try force delete
                if force_delete_file(Path(path)):
                    logger.info(f"Successfully force deleted {path}")
                else:
                    logger.warning(f"Failed to force delete {path}")

        for dir_path in [self.dist_dir, self.build_dir]:
            if dir_path.exists():
                try:
                    shutil.rmtree(dir_path, onerror=remove_readonly)
                except Exception as e:
                    logger.warning(f"Failed to remove directory {dir_path}: {e}")
                    # Try to remove individual files
                    try:
                        for root, dirs, files in os.walk(dir_path, topdown=False):
                            for name in files:
                                file_path = Path(root) / name
                                try:
                                    os.chmod(file_path, 0o777)
                                    os.remove(file_path)
                                except Exception as e:
                                    logger.warning(f"Failed to remove file {file_path}: {e}")
                                    force_delete_file(file_path)
                            for name in dirs:
                                dir_path = Path(root) / name
                                try:
                                    os.chmod(dir_path, 0o777)
                                    os.rmdir(dir_path)
                                except Exception as e:
                                    logger.warning(f"Failed to remove directory {dir_path}: {e}")
                    except Exception as e:
                        logger.error(f"Failed to clean directory {dir_path}: {e}")
        
        # Create directories if they don't exist
        os.makedirs(self.dist_dir, exist_ok=True)
        os.makedirs(self.build_dir, exist_ok=True)
 
    def collect_data_files(self):
        """Collect all necessary data files."""
        data_files = []
        
        # Add hooks directory with proper relative paths
        if self.hooks_dir.exists():
            logger.info(f"Found hooks directory at: {self.hooks_dir}")
            for root, _, files in os.walk(self.hooks_dir):
                for file in files:
                    full_path = Path(root) / file
                    # Calculate the relative path to maintain directory structure
                    target_dir = Path('hooks') / Path(root).relative_to(self.hooks_dir)
                    data_files.append((str(full_path), str(target_dir)))
                    logger.info(f"Adding hook file: {full_path} -> {target_dir}")
        else:
            logger.warning(f"Hooks directory not found at: {self.hooks_dir}")
            # Create an empty hooks directory if it doesn't exist
            os.makedirs(self.hooks_dir, exist_ok=True)
            logger.info(f"Created empty hooks directory at: {self.hooks_dir}")

        # Add assets directory with proper relative paths
        if self.assets_dir.exists():
            for root, _, files in os.walk(self.assets_dir):
                for file in files:
                    full_path = Path(root) / file
                    target_dir = Path('assets') / Path(root).relative_to(self.assets_dir)
                    data_files.append((str(full_path), str(target_dir)))

        # Add Qt WebEngine specific files
        qt_paths = self.get_qt_paths()
        if qt_paths:
            # Add WebEngine resources
            webengine_resources = [
                'qtwebengine_devtools_resources.pak',
                'qtwebengine_resources.pak',
                'qtwebengine_resources_100p.pak',
                'qtwebengine_resources_200p.pak'
            ]
            
            for resource in webengine_resources:
                resource_path = os.path.join(qt_paths['resources_path'], resource)
                if os.path.exists(resource_path):
                    data_files.append((resource_path, 'resources'))

            # Add WebEngine translations
            if os.path.exists(qt_paths['translations_path']):
                for file in os.listdir(qt_paths['translations_path']):
                    if file.startswith('qtwebengine'):
                        source = os.path.join(qt_paths['translations_path'], file)
                        data_files.append((source, 'translations'))

            # Add WebEngine plugins
            webengine_plugins = ['platforms', 'webenginecore', 'imageformats']
            for plugin in webengine_plugins:
                plugin_path = os.path.join(qt_paths['plugins_path'], plugin)
                if os.path.exists(plugin_path):
                    for file in os.listdir(plugin_path):
                        if file.endswith('.dll'):
                            source = os.path.join(plugin_path, file)
                            data_files.append((source, os.path.join('PyQt6', 'Qt6', plugin)))

        # Log all collected data files
        logger.info("Collected data files:")
        for source, target in data_files:
            logger.info(f"  {source} -> {target}")

        return data_files
 
    def create_version_info(self):
        """Create version info file for Windows."""
        try:
            # Convert version string to comma-separated integers for Windows version info
            version_parts = [int(x) for x in self.version.split('.')]
            while len(version_parts) < 4:
                version_parts.append(0)
            version_str = ', '.join(str(x) for x in version_parts)
            
            version_info = f'''VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={version_parts},
    prodvers={version_parts},
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
        StringTable(
          u'040904B0',
          [StringStruct(u'CompanyName', u'{self.author}'),
           StringStruct(u'FileDescription', u'{self.description}'),
           StringStruct(u'FileVersion', u'{self.version}'),
           StringStruct(u'InternalName', u'{self.app_name}'),
           StringStruct(u'LegalCopyright', u'Copyright (c) 2024'),
           StringStruct(u'OriginalFilename', u'{self.app_name}.exe'),
           StringStruct(u'ProductName', u'{self.app_name}'),
           StringStruct(u'ProductVersion', u'{self.version}')])
      ]
    ),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
'''
            version_info_path = self.project_root / 'file_version_info.txt'
            with open(version_info_path, 'w') as f:
                f.write(version_info)
            logger.info(f"Created version info file at: {version_info_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to create version info file: {e}")
            return False

    def generate_spec_file(self):
        """Generate PyInstaller spec file content."""
        data_files = self.collect_data_files()
        
        spec_content = f"""# -*- mode: python ; coding: utf-8 -*-
 
import sys
import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs
 
block_cipher = None
 
# Collect all data files
data_files = {data_files}
 
a = Analysis(
    [str(Path(r'{self.src_dir}') / 'main.py')],
    pathex=[str(Path(r'{self.project_root}'))],
    binaries=[],
    datas=data_files,
    hiddenimports=[
        'PySide6.QtWebEngineCore',
        'PySide6.QtWebEngineWidgets',
        'PySide6.QtWebChannel',
        'PySide6.QtNetwork',
        'PySide6.shiboken6',
        'PySide6.QtPrintSupport',
        'PySide6.QtWidgets',
        'PySide6.QtGui',
        'PySide6.QtCore'
    ],
    hookspath=[str(Path(r'{self.hooks_dir}'))],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
 
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
 
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='{self.app_name}',
    debug=False,
    bootloader_ignore_signals=True,  # Ignore signals to prevent console
    strip=False,
    upx=True,
    console=False,  # Set to False to hide console window
    disable_windowed_traceback=True,  # Prevent error popups
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(Path(r'{self.assets_dir}') / 'logo.png'),
    uac_admin=False,  # Don't request admin privileges
    version='file_version_info.txt',  # Add version info
    win_private_assemblies=False,  # Prevent DLL loading issues
    runtime_tmpdir=None,  # Prevent temp directory creation
    argv_emulation=False,  # Prevent command line argument handling
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
 
    def copy_hooks_to_dist(self):
        """Copy hooks directory to the final distribution directory."""
        try:
            dist_hooks_dir = self.dist_dir / self.app_name / "hooks"
            logger.info(f"Copying hooks from {self.hooks_dir} to {dist_hooks_dir}")
            
            # Create hooks directory in dist if it doesn't exist
            os.makedirs(dist_hooks_dir, exist_ok=True)
            
            # Copy all files from src/hooks to dist/hooks
            if self.hooks_dir.exists():
                for root, _, files in os.walk(self.hooks_dir):
                    for file in files:
                        src_file = Path(root) / file
                        # Calculate relative path from hooks_dir
                        rel_path = src_file.relative_to(self.hooks_dir)
                        dst_file = dist_hooks_dir / rel_path
                        
                        # Create destination directory if it doesn't exist
                        os.makedirs(dst_file.parent, exist_ok=True)
                        
                        # Copy the file
                        shutil.copy2(src_file, dst_file)
                        logger.info(f"Copied hook file: {src_file} -> {dst_file}")
            else:
                logger.warning(f"Source hooks directory not found at: {self.hooks_dir}")
                # Create an empty hooks directory
                os.makedirs(dist_hooks_dir, exist_ok=True)
                logger.info(f"Created empty hooks directory at: {dist_hooks_dir}")
            
            return True
        except Exception as e:
            logger.error(f"Failed to copy hooks directory: {e}")
            return False

    def build(self) -> Optional[Path]:
        """Build the executable."""
        try:
            if not self.check_dependencies():
                return None

            # Clean previous builds
            self.clean_build_dirs()
            time.sleep(1)  # Give time for cleanup to complete

            # Create version info file first
            if not self.create_version_info():
                logger.error("Failed to create version info file")
                return None

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

            # Copy hooks directory to the final distribution
            if not self.copy_hooks_to_dist():
                logger.error("Failed to copy hooks directory to distribution")
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