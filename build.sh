#!/bin/bash
echo "Building Genie application..."

# Activate virtual environment if it exists
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

# Install requirements if not already installed
pip install -r requirements.txt

# Check if user wants an HSBC build
HSBC_BUILD=false
if [ "$1" = "hsbc" ]; then
    echo "Building special HSBC environment version..."
    HSBC_BUILD=true
    
    # Create an HSBC version spec file with forced fallback UI
    cat > genie-hsbc.spec << EOF
# -*- mode: python ; coding: utf-8 -*-
block_cipher = None

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=[('src/assets', 'assets'), ('src/hooks', 'hooks')],
    hiddenimports=['PySide6.QtWidgets'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PySide6.QtWebEngineCore'],
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
EOF
    
    # Build the HSBC version
    pyinstaller --clean genie-hsbc.spec
else
    # Build the regular executable
    pyinstaller --clean genie.spec
fi

echo "Build complete!"
if [ "$HSBC_BUILD" = true ]; then
    if [ "$(uname)" = "Darwin" ]; then
        echo "The HSBC version executable can be found at dist/Genie-HSBC.app"
    else
        echo "The HSBC version executable can be found at dist/Genie-HSBC"
    fi
else
    echo "The executable can be found in the dist folder."
fi 