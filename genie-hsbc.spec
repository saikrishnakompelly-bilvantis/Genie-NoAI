# -*- mode: python ; coding: utf-8 -*-
block_cipher = None
a = Analysis(['src/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('src/assets', 'assets'), 
        ('src/hooks', 'hooks'),
        ('src/hooks/.env.example', 'hooks/'),  # Explicitly include .env.example
        ('src/hooks/.env.sample', 'hooks/'),   # Explicitly include .env.sample
    ],
    hiddenimports=[
        'PySide6.QtWidgets',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtNetwork',
        'PySide6.QtPrintSupport',
        'python-dotenv'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['runtime_hook.py'],
    excludes=['PySide6.QtWebEngineCore', 'PySide6.QtWebEngineWidgets', 'PySide6.QtWebEngine'],  # Exclude all web engine modules
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Genie-HSBC',
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
    icon='src/assets/logo.ico'
)
