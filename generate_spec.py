import os

# Create a runtime hook to force native UI mode
runtime_hook_content = '''
import os
os.environ['GENIE_USE_NATIVE_UI'] = 'true'
'''

# Write the runtime hook
with open('runtime_hook.py', 'w') as f:
    f.write(runtime_hook_content)

spec_content = '''# -*- mode: python ; coding: utf-8 -*-
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
        'PySide6.QtWebEngineWidgets',
        'PySide6.QtWebEngineCore',
        'PySide6.QtWebEngine',
        'PySide6.QtWebChannel',
        'PySide6.QtNetwork',
        'PySide6.QtPrintSupport',
        'python-dotenv',
        'requests'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['runtime_hook.py'],
    excludes=[],
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
'''

with open('genie-hsbc.spec', 'w') as f:
    f.write(spec_content) 