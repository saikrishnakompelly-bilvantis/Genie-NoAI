# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('src/assets', 'assets'),
        ('src/hooks', 'hooks'),  # Include the entire hooks directory
        ('src/hooks/.env.example', 'hooks/'),  # Explicitly include .env.example
        ('src/hooks/.env.sample', 'hooks/'),   # Explicitly include .env.sample
    ],
    hiddenimports=['PySide6.QtWebEngineCore', 'python-dotenv'],
    hookspath=[],
    hooksconfig={},
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Genie',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='src/assets/logo.ico'  # Make sure to convert your logo.png to logo.ico
)

# Only create the app bundle on macOS
import sys
if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='Genie.app',
        icon='src/assets/logo.icns',  # Ensure you have an .icns file for macOS
        bundle_identifier=None,
        info_plist={
            'NSHighResolutionCapable': 'True',
            'LSBackgroundOnly': 'False',  # Ensures app shows in dock and doesn't run in background
            'CFBundleShortVersionString': '1.0.0',
            'NSPrincipalClass': 'NSApplication',
            'NSRequiresAquaSystemAppearance': 'False'  # Allows dark mode support
        }
    ) 