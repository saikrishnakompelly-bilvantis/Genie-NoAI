# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

block_cipher = None

# Collect all data files
data_files = [('/Users/sai.kompelly/Desktop/Genie-Secrets/src/hooks/post-commit', 'hooks/.'), ('/Users/sai.kompelly/Desktop/Genie-Secrets/src/hooks/scan-repo', 'hooks/.'), ('/Users/sai.kompelly/Desktop/Genie-Secrets/src/hooks/pre-commit', 'hooks/.'), ('/Users/sai.kompelly/Desktop/Genie-Secrets/src/hooks/commit-scripts/config.py', 'hooks/commit-scripts'), ('/Users/sai.kompelly/Desktop/Genie-Secrets/src/hooks/commit-scripts/secretscan.log', 'hooks/commit-scripts'), ('/Users/sai.kompelly/Desktop/Genie-Secrets/src/hooks/commit-scripts/secretscan.py', 'hooks/commit-scripts'), ('/Users/sai.kompelly/Desktop/Genie-Secrets/src/hooks/commit-scripts/utils.py', 'hooks/commit-scripts'), ('/Users/sai.kompelly/Desktop/Genie-Secrets/src/hooks/commit-scripts/__pycache__/secretscan.cpython-313.pyc', 'hooks/commit-scripts/__pycache__'), ('/Users/sai.kompelly/Desktop/Genie-Secrets/src/hooks/commit-scripts/templates/report.html', 'hooks/commit-scripts/templates'), ('/Users/sai.kompelly/Desktop/Genie-Secrets/src/assets/.DS_Store', 'assets/.'), ('/Users/sai.kompelly/Desktop/Genie-Secrets/src/assets/logo.png', 'assets/.')]

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
    print(f"Warning: Could not collect Qt resources: {e}")

a = Analysis(
    [os.path.join('/Users/sai.kompelly/Desktop/Genie-Secrets/src', 'main.py')],
    pathex=['/Users/sai.kompelly/Desktop/Genie-Secrets'],
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
    hooksconfig={},
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
        icon=os.path.join('/Users/sai.kompelly/Desktop/Genie-Secrets/src/assets', 'logo.png'),
    )
    
    # Create .app bundle for macOS
    app = BUNDLE(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        name='Genie-Secrets.app',
        icon=os.path.join('/Users/sai.kompelly/Desktop/Genie-Secrets/src/assets', 'logo.png'),
        bundle_identifier='com.genie.secrets',
        info_plist={
            'CFBundleShortVersionString': '1.0.0',
            'CFBundleVersion': '1.0.0',
            'NSHighResolutionCapable': True,
            'LSBackgroundOnly': False,
            'NSRequiresAquaSystemAppearance': False,
            'NSPrincipalClass': 'NSApplication',
            'NSAppleScriptEnabled': False,
            'CFBundleDisplayName': 'Genie-Secrets',
            'CFBundleName': 'Genie-Secrets',
            'NSAppTransportSecurity': {
                'NSAllowsArbitraryLoads': True
            },
        },
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
        icon=os.path.join('/Users/sai.kompelly/Desktop/Genie-Secrets/src/assets', 'logo.png'),
    )
